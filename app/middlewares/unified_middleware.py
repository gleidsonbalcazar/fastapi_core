import json
import logging
import secrets
import time
import traceback
import uuid
from datetime import datetime, timezone
from http import HTTPStatus

from app.core.container import Container
from fastapi import Request, Response, HTTPException, BackgroundTasks
from keycloak.exceptions import KeycloakAuthenticationError
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from dependency_injector.wiring import Provide, inject
from app.infrastructure.mappings.opensearch.log_entries import get_log_entries_mapping

from app.core.config import settings
from app.domain.entities.log_entry import LogEntry
from app.infrastructure.adapters.email_adapter import EmailAdapter
from app.infrastructure.cache.redis import RedisClient

logger = logging.getLogger(__name__)

IGNORED_ROUTES = [
    "/actuator/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/admin",
    "/config",
    "/favicon",
]

BYPASS_ROUTES = [
    "/actuator/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/config",
    "/favicon"
]

redis = RedisClient(redis_url=settings.REDIS_URL)


def get_random_ip():
    return ".".join(str(secrets.randbelow(256)) for _ in range(4))


def rate_limit_key_func(request: Request) -> str:
    # TODO: Trocar para Cloudflare repassar depois
    # scret random
    rnd = secrets.token_hex(16)
    client_ip = request.headers.get("Client-Ip", get_random_ip())
    path = request.url.path
    method = request.method
    tenant_id = request.headers.get("X-Tenant-ID", "")
    session_id = request.headers.get("session-id", "")
    user_agent = request.headers.get("User-Agent", "")
    geolocation = request.headers.get("geolocation", "")
    return f"{rnd}{client_ip}:{path}:{method}:{tenant_id}:{session_id}:{user_agent}:{geolocation}"


def get_schema_name(tenant_id):
    if tenant_id:
        return redis.get(tenant_id)
    return "no_tenant_defined"


class UnifiedMiddleware(BaseHTTPMiddleware):
    @inject
    def __init__(self, app, container: Container = Provide[Container]):
        super().__init__(app)
        self.open_search_port = container.open_search_port()
        self.limiter = Limiter(
            key_func=rate_limit_key_func, storage_uri=settings.REDIS_URL
        )
        self.global_rate_limit = f"{settings.GLOBAL_RATE_LIMIT}/minute"
        self.email_adapter = EmailAdapter()

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()
        background_tasks = BackgroundTasks()

        # Inicializa o log_entry
        log_entry = LogEntry(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=str(request.query_params),
            ip_address=request.headers.get(
                "client-ip", get_random_ip()
            ),  # TODO: Trocar para Cloudflare repassar depois
            user_agent=request.headers.get("User-Agent", "unknown"),
            # O formato do geolocation no opensearch é [40.7128, -74.0060]
            geolocation=request.headers.get("geolocation", None),
            session_id=request.headers.get("session-id", None),
            timestamp=datetime.now(timezone.utc),
            tenant_id=request.headers.get("X-Tenant-ID"),
        )

        try:
            # Tratamento do Tenant
            if not self.is_bypass_route(request.url.path):
                header_tenant = request.headers.get("X-Tenant-ID")
                if not header_tenant:
                    return self.build_response(400, "Requisição inválida", request_id)
                schema_name = get_schema_name(header_tenant)
                if not schema_name:
                    return self.build_response(400, "Requisição inválida", request_id)
                request.state.schema = schema_name
                logger.info(
                    f"Tenant schema definido para: {schema_name} no request_id: {request_id}"
                )

            if any(request.url.path.startswith(route) for route in IGNORED_ROUTES):
                return await call_next(request)

            # Processa o corpo da requisição
            (
                log_entry.request_body,
                log_entry.request_headers,
            ) = await self.process_request_body(request)

            # Rate Limiting
            response = await self.limiter.limit(self.global_rate_limit)(call_next)(
                request
            )

            log_entry.response_body = await self.process_response_body(response)
            process_time = time.time() - start_time
            log_entry.response_status_code = response.status_code
            log_entry.response_headers = dict(response.headers)
            log_entry.duration = process_time
            logger.info(f"[Request Concluído]: {log_entry}")

            if process_time > settings.SLOW_API_THRESHOLD:
                background_tasks.add_task(
                    self.send_error_email,
                    request.headers.get("X-Tenant-ID"),
                    f"Tempo de resposta alto na rota {request.url.path}",
                    f"""
                    <p><strong>Tempo de resposta:</strong> {process_time} segundos</p>
                    <p><strong>Request ID:</strong> {request_id}</p>
                    <p><strong>Limite configurado:</strong> {settings.SLOW_API_THRESHOLD} segundos</p>
                    <p><strong>IP:</strong> {log_entry.ip_address}</p>
                    <p><strong>Session ID:</strong> {log_entry.session_id}</p>
                    """,
                )

            # Agendamento de tarefas em background
            background_tasks.add_task(self.save_log, log_entry)

            if response.status_code >= 400 and response.status_code not in [401]:
                background_tasks.add_task(
                    self.send_error_email,
                    request.state.schema
                    if hasattr(request.state, "schema")
                    else get_schema_name(request.headers.get("X-Tenant-ID")),
                    f"Erro na API para request_id {request_id}",
                    f"""
                    <p><strong>Erro:</strong> {log_entry.response_body}</p>
                    <p><strong>Rota:</strong> {log_entry.path}</p>
                    <p><strong>Método:</strong> {log_entry.method}</p>
                    <p><strong>Request ID:</strong> {request_id}</p>
                    <p><strong>IP:</strong> {log_entry.ip_address}</p>
                    <p><strong>Session ID:</strong> {log_entry.session_id}</p>
                    """,
                )
                response = self.build_response(
                    response.status_code,
                    self.get_http_error_detail(response.status_code),
                    request_id,
                )
            response.background = background_tasks  # Anexa as tarefas em background
            return response

        except Exception as exc:
            return await self.handle_exception(
                exc, request, log_entry, start_time, background_tasks
            )

    async def handle_exception(
        self, exc, request, log_entry, start_time, background_tasks
    ):
        process_time = time.time() - start_time
        log_entry.duration = process_time

        if isinstance(exc, RateLimitExceeded):
            status_code = 429
            detail = "Muitas requisições"
            logger.warning(
                f"Limite de requisições excedido no request_id {log_entry.request_id}"
            )
        elif isinstance(exc, KeycloakAuthenticationError):
            status_code = exc.response_code
            detail = "Erro de autenticação"
            logger.exception(
                f"Erro de autenticação no request_id {log_entry.request_id}"
            )
        elif isinstance(exc, HTTPException):
            status_code = exc.status_code
            detail = self.get_http_error_detail(status_code)
            logger.exception(f"Erro HTTP no request_id {log_entry.request_id}")
        else:
            status_code = 500
            detail = HTTPStatus.INTERNAL_SERVER_ERROR.phrase
            logger.exception(f"Erro não tratado no request_id {log_entry.request_id}")

        log_entry.response_status_code = status_code
        log_entry.response_body = str(exc)  # Armazena o detalhe do erro apenas no log

        # Envia email de erro detalhado
        traceback_str = traceback.format_exc()
        background_tasks.add_task(
            self.send_error_email,
            request.state.schema
            if hasattr(request.state, "schema")
            else get_schema_name(request.headers.get("X-Tenant-ID")),
            f"Erro no request_id {log_entry.request_id}",
            f"""
            <p><strong>Erro:</strong> {str(exc)}</p>
            <p><strong>Request ID:</strong> {log_entry.request_id}</p>
            <p><strong>Rota:</strong> {log_entry.path}</p>
            <p><strong>Método:</strong> {log_entry.method}</p>
            <p><strong>IP:</strong> {log_entry.ip_address}</p>
            <p><strong>Session ID:</strong> {log_entry.session_id}</p>
            <p><strong>Traceback:</strong></p>
            <pre>{traceback_str}</pre>
            """,
        )

        background_tasks.add_task(self.save_log, log_entry)
        response = self.build_response(
            status_code, detail, log_entry.request_id, traceback_str=traceback_str
        )
        response.background = background_tasks
        return response

    @staticmethod
    def get_http_error_detail(status_code):
        error_messages = {
            400: HTTPStatus.BAD_REQUEST.phrase,
            401: HTTPStatus.UNAUTHORIZED.phrase,
            403: HTTPStatus.FORBIDDEN.phrase,
            404: HTTPStatus.NOT_FOUND.phrase,
            405: HTTPStatus.METHOD_NOT_ALLOWED.phrase,
            409: HTTPStatus.CONFLICT.phrase,
            422: HTTPStatus.UNPROCESSABLE_ENTITY.phrase,
            429: HTTPStatus.TOO_MANY_REQUESTS.phrase,
            500: HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
        }
        return error_messages.get(status_code, "Erro desconhecido")

    @staticmethod
    def is_bypass_route(path: str) -> bool:
        return any(route in path for route in BYPASS_ROUTES)

    @staticmethod
    async def process_request_body(request: Request):
        request_headers = dict(request.headers)
        try:
            request_body = await request.json()
        except (json.JSONDecodeError, UnicodeDecodeError):
            request_body = await request.body()
            request_body = request_body.decode("utf-8", errors="ignore")
            request_body = {"raw_body": request_body}
        return request_body, request_headers

    @staticmethod
    async def process_response_body(response: Response) -> str:
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        # Reatribui o body_iterator com um iterador assíncrono
        async def new_body_iterator():
            yield body

        response.body_iterator = new_body_iterator()
        return body.decode("utf-8", errors="ignore")

    def save_log(self, log_entry: LogEntry):
        try:
            mapping = get_log_entries_mapping()
            self.open_search_port.set("logs", log_entry.to_dict(), mapping)
        except Exception as e:
            logger.error(f"Failed to save log entry: {str(e)}")

    def send_error_email(self, schema, subject: str, body: str):
        to_email = settings.REPORT_EMAIL
        email_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e0e0e0; border-radius: 8px;">
            <h2 style="color: #d9534f; border-bottom: 2px solid #d9534f; padding-bottom: 10px;">{subject}</h2>
            {body}
            <p style="font-size: 16px; color: #333;">
                <strong>Informações do Tenant:</strong>
            </p>
            <p style="font-size: 14px; color: #555;">
                <strong>Tenant ID:</strong> {schema}
            </p>
            <br>
            <p style="font-size: 14px; color: #999;">
                Este email foi gerado automaticamente pelo sistema de monitoramento de erros do <strong>Consórcio Multi-Tenant</strong>.
            </p>
            <hr style="border-top: 1px solid #e0e0e0; margin-top: 20px;">
            <p style="font-size: 12px; color: #999; text-align: center;">
                &copy; {datetime.now().year} Paneas. Todos os direitos reservados.
            </p>
        </div>
        """
        self.email_adapter.send_email(to_email, subject, email_body)

    @staticmethod
    def build_response(
        status_code: int, detail: str, request_id: str, traceback_str: str = None
    ) -> JSONResponse:
        response_content = {
            "status_code": status_code,
            "detail": detail,
            "request_id": request_id,
        }
        if traceback_str and status_code == 500:
            response_content["traceback"] = traceback_str

        return JSONResponse(
            status_code=status_code,
            content=response_content,
        )

    @staticmethod
    def get_geolocation(ip_address):
        pass  # TODO: Implementar função de geolocalização
