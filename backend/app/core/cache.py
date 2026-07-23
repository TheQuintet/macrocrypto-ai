import os
import redis
from dotenv import load_dotenv
from redis.exceptions import RedisError


load_dotenv()

# Redis client configured to use local Redis server based on environment variables
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=int(os.getenv("REDIS_PORT")),
    db=int(os.getenv("REDIS_DB")),
    decode_responses=True
)


def get_redis():
    """
    Provides Redis client instance.

    Redis is used only as a cache layer.
    Failure to connect should not stop the application.
    """

    return redis_client


def check_redis_connection():
    """
    Checks Redis availability.

    Used for health checks/testing.
    """

    try:
        return redis_client.ping()

    except RedisError as error:
        print(f"Redis connection error: {error}")
        return False