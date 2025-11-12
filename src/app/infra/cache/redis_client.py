import redis

from app.config import settings

_redis = None


def get_redis():
    global _redis
    if _redis is None:
        _redis = redis.Redis.from_url(
            f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/0",
            decode_responses=True,
        )
    return _redis


