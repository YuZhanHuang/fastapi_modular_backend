import redis

from app.infra.containers import get_container

def get_redis() -> redis.Redis:
    return get_container().infra.redis()
