from fastapi import APIRouter, Request
from fastapi import Depends

from app.api.dependencies import jwt_auth
from app.core.cache import get_redis
from app.core.rate_limit import limiter
from redis.exceptions import RedisError
from app.schemas.price_response import PriceResponse
from app.services.container import price_service


router = APIRouter(
    prefix="/api/v1/btc",
    tags=["Bitcoin"]
)

@router.get(
    "/price",
    response_model=PriceResponse,
    summary="Get current BTC market data"
)
@limiter.limit("60/minute")
async def get_btc_price(
    request: Request,
    _: str | None = Depends(jwt_auth)
):
    """
    BTC price endpoint.

    Provides the latest Bitcoin market snapshot, including current price,
    24-hour statistics, and 7-day price changes.

    Features:
    - Retrieves the latest BTC market data from the price service.
    - Uses Redis caching to reduce load on the price service and improve response time.
    - Cached responses are stored for 5 seconds.
    - If no valid cache entry exists, data is retrieved from the price service
    and stored in Redis for subsequent requests.
    - Requests are rate-limited to 60 requests per minute per IP address.
    - JWT authentication support is prepared for future secured endpoints.
    """
    cache_key = "btc_price_snapshot"

    redis = get_redis()

    try:
        # Try Redis cache first
        cached_snapshot = redis.get(cache_key)

        if cached_snapshot:
            print("Returning BTC price from Redis cache")

            return PriceResponse(
                **json.loads(cached_snapshot)
            )

    except RedisError as error:
        print(f"Redis read failed: {error}")

    except Exception as error:
        print(f"Unexpected Redis error: {error}")


    # Redis miss or Redis unavailable
    print("Reading BTC price from PriceService")


    snapshot = price_service.get_snapshot()


    response = PriceResponse(
        current_price=snapshot.current_price,
        change_24h=snapshot.change_24h,
        change_24h_percent=snapshot.change_24h_percent,
        high_24h=snapshot.high_24h,
        low_24h=snapshot.low_24h,
        volume_24h=snapshot.volume_24h,
        change_7d=snapshot.change_7d,
        change_7d_percent=snapshot.change_7d_percent,
        updated_at=snapshot.updated_at,
    )


    try:
        redis.setex(
            cache_key,
            5,
            response.model_dump_json()
        )

    except RedisError as error:
        print(f"Redis write failed: {error}")

    except Exception as error:
        print(f"Unexpected Redis write error: {error}")


    return response