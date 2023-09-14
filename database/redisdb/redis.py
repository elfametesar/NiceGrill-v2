from redis.asyncio import Redis
from redis import Redis as NonAsyncRedis
from config import REDIS_CREDS


AsyncRedis = Redis(**REDIS_CREDS, decode_responses=True)
SyncRedis = NonAsyncRedis(**REDIS_CREDS, decode_responses=True)