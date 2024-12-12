import datetime
import boto3
from opensearchpy import AuthorizationException, OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from app.domain.ports.opensearch_port import OpenSearchPort
from app.core.config import settings

OPENSEARCH_PORT = settings.OPENSEARCH_PORT
OPENSEARCH_URL = settings.OPENSEARCH_URL
OPENSEARCH_SCHEME = settings.OPENSEARCH_SCHEME
OPENSEARCH_CONECTION_WITH_AWS = settings.OPENSEARCH_CONECTION_WITH_AWS


class OpenSearchAdapter(OpenSearchPort):
    def __init__(self):
        self.es = None

        try:
            if OPENSEARCH_CONECTION_WITH_AWS:
                session = boto3.Session(region_name="sa-east-1")
                service = "es"
                credentials = session.get_credentials()
                aws_auth = AWS4Auth(
                    credentials.access_key,
                    credentials.secret_key,
                    session.region_name,
                    service,
                    session_token=credentials.token,
                )
                self.es = OpenSearch(
                    hosts=[{"host": settings.OPENSEARCH_URL, "port": 443}],
                    http_auth=aws_auth,
                    use_ssl=True,
                    verify_certs=True,
                    connection_class=RequestsHttpConnection,
                )
            else:
                self.es = OpenSearch(
                    [
                        {
                            "host": OPENSEARCH_URL,
                            "port": OPENSEARCH_PORT,
                            "scheme": OPENSEARCH_SCHEME,
                        }
                    ]
                )
        except Exception as e:
            print(f"Não foi possível conectar ao OpenSearch: {e}")
            print(
                f"Usando AWS Auth com a região {session.region_name} e host {settings.OPENSEARCH_URL}"
            )

    def create_index_if_not_exists(self, index_name: str, mapping: dict):
        if not self.es.indices.exists(index=index_name):
            try:
                if mapping:
                    self.es.indices.create(index=index_name, body=mapping)
                else:
                    self.es.indices.create(index=index_name)
                print(f"Índice '{index_name}' criado com sucesso.")
            except Exception as e:
                print(f"Erro ao criar índice '{index_name}': {e}")

    def set(self, index: str, data: dict, mapping: dict = None, nivel: str = "INFO"):
        try:
            data["nivel"] = nivel
            data["timestamp"] = datetime.datetime.now().isoformat()
            index = f"{index}_{datetime.datetime.now().strftime('%Y_%m_%d')}"
            self.create_index_if_not_exists(index, mapping)
            data = {k: v for k, v in data.items() if v}
            self.es.index(index=index, body=data)
        except AuthorizationException as e:
            print("Erro ao salvar no OpenSearch:")
            print(f"Index: {index}")
            print(f"Error: {e.error}")
            print(f"info: {e.info}")
            print(f"status_code: {e.status_code}")
            return False
        except Exception as e:
            print(f"Erro ao salvar no OpenSearch: {e}")
            error_type = type(e).__name__
            print(f"Index: {index}")
            print(f"error_type: {error_type}")
            return False

    def get(self, index: str, body: dict):
        if not index.endswith("_*"):
            index = f"{index}_*"
        return self.es.search(index=index, body=body)
