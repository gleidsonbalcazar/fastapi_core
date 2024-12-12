import os
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings
from pydantic import Field


class Config:
    APP_ENV = os.getenv("APP_ENV", "development")

load_dotenv()

class Settings(BaseSettings):
    APP_NAME: str = "ND SAAS"
    DATABASE_URL: str = ""
    REDIS_URL: str = ""
    SCHEMAS: str = ""
    SECRET_KEY: str = ""
    ALGORITHM: str = ""

    EMAIL_HOST: str = ""
    EMAIL_PORT: int = 465
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM_ADDR: str = ""
    EMAIL_RESET_TOKEN_EXPIRE_HOURS: int = 12
    REPORT_EMAIL: str = ""

    KEYCLOAK_CLIENT_ID: str = ""
    KEYCLOAK_REALM_NAME: str = ""
    KEYCLOAK_SERVER_URL: str = ""
    KEYCLOAK_CLIENT_SECRET_KEY: str = ""

    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET_NAME: str = ""

    LOGGING_LEVEL: str = "INFO"

    OPENSEARCH_URL: str = ""
    OPENSEARCH_PORT: int = Field(9200, env="OPENSEARCH_PORT")
    OPENSEARCH_SCHEME: str = "https"
    OPENSEARCH_CONECTION_WITH_AWS: bool = Field(
        False, env="OPENSEARCH_CONECTION_WITH_AWS"
    )

    @property
    def schema_list(self) -> List[str]:
        return [s.strip() for s in self.SCHEMAS.split(",")]

    @property
    def schema_list_without_public(self) -> List[str]:
        return [s for s in self.schema_list if s != "public_schema" and s != "public"]

    class ConfigDict:
        env_prefix = "APP_"
        env_file = ".env"


settings = Settings()
