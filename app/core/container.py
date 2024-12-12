from dependency_injector import containers, providers
from fastapi import Request

from app.core.config import settings
from app.infrastructure.cache.redis import RedisClient
from sqlalchemy.orm import Session


def get_request_id(request: Request):
    return request.headers.get("X-Request-ID", None)

# Container
class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    db = providers.Dependency(instance_of=Session)
    redis_client = providers.Singleton(RedisClient, redis_url=settings.REDIS_URL)
