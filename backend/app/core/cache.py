import os
import redis
from dotenv import load_dotenv
from redis.exceptions import RedisError

load_dotenv()

# Check if Redis is enabled via environment variable
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "true").lower() == "true"

# Initialize Redis client only if enabled
if REDIS_ENABLED:
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True,
            socket_connect_timeout=2  # Quick timeout to prevent hanging
        )
        # Test the connection
        redis_client.ping()
        print("✅ Redis connected successfully")
    except Exception as e:
        print(f"⚠️ Redis connection failed: {e}")
        print("   Running without Redis cache")
        redis_client = None
else:
    print("ℹ️ Redis disabled via REDIS_ENABLED=false")
    redis_client = None


def get_redis():
    """
    Provides Redis client instance.

    Returns None if Redis is disabled or unavailable.
    Redis is used only as a cache layer.
    Failure to connect should not stop the application.
    """
    return redis_client


def check_redis_connection():
    """
    Checks Redis availability.

    Used for health checks/testing.
    """
    if redis_client is None:
        return False
    try:
        return redis_client.ping()
    except RedisError as error:
        print(f"Redis connection error: {error}")
        return False