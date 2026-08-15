import redis

redis_client = redis.Redis(
    host="",
    port= 378,
    db=0,
    decode_responses=True
)