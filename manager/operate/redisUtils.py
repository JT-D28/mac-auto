import redis
from django.conf import settings


def RedisUtils():
    pool = redis.ConnectionPool(host=settings.REDIS_HOST, port=settings.REDIS_PORT,db=0, decode_responses=True)
    con = redis.Redis(connection_pool=pool)
    return con

