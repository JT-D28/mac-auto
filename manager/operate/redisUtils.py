import redis
from ME2 import configs


def RedisUtils():
    pool = redis.ConnectionPool(host=configs.REDIS_HOST, port=configs.REDIS_PORT,db=0, decode_responses=True)
    con = redis.Redis(connection_pool=pool)
    return con

