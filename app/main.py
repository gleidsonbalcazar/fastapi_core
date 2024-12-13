import logging
import re

from fastapi import FastAPI, HTTPException, Request
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.container import Container
from app.interface.api.actuator.endpoints import router as actuator_router
from app.middlewares.unified_middleware import UnifiedMiddleware

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_app(environment: str = "development"):
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        dependencies=[],
    )
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    setup_exception_handlers(app)
    setup_dependency_injection(app)
    setup_middlewares(app)
    setup_routers(app)
    if environment != "testing":
        app.add_event_handler("startup", startup)
        app.add_event_handler("shutdown", shutdown)

    return app


def setup_routers(app: FastAPI):
    app.include_router(actuator_router, prefix="/actuator", tags=["actuator"])


def setup_exception_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        match = re.match(r"^(\d+):", exc.detail)
        if match:
            status_code = int(match.group(1))
            detail = exc.detail[len(match.group(0)):].strip()
        else:
            status_code = exc.status_code
            detail = exc.detail

        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
        )


def setup_dependency_injection(app: FastAPI):
    container = Container()
    container.wire(modules=[
        "app.middlewares.unified_middleware"
    ])
    app.container = container


def setup_middlewares(app: FastAPI):
    app.add_middleware(UnifiedMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def startup():
    logger.info("Application startup")


def shutdown():
    logger.info("Application shutdown")


app = create_app()

logger.info(f"{settings.APP_NAME} startup complete")
