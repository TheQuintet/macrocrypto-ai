import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.websocket.btc_client import (
    connect_btc_price_stream
)

from app.services.history_service import HistoryService
from app.services.container import price_service


btc_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global btc_task


    # =====================================
    # Initialize historical market data
    # =====================================
    #
    # Loads historical BTC daily candles
    # required for calculating 7-day price
    # movement.
    #
    # This must happen before starting the
    # WebSocket stream so live updates can
    # immediately calculate 7-day changes.

    try:

        history_service = HistoryService()

        candles = await history_service.get_daily_candles(
            limit=8
        )


        price_service.initialize_from_history(
            candles
        )


        print(
            f"7-day reference price initialized: "
            f"{price_service.price_7d_reference}"
        )


    except Exception as error:

        # Historical data is required for 7-day
        # calculations but should not prevent the
        # application from starting.
        #
        # Live BTC price updates can still continue.
        print(
            f"Historical initialization failed: {error}"
        )



    # =====================================
    # Start real-time BTC price stream
    # =====================================
    #
    # WebSocket task continuously receives
    # Binance ticker updates and updates
    # PriceService state.

    try:

        btc_task = asyncio.create_task(
            connect_btc_price_stream()
        )


    except Exception as error:

        print(
            f"Failed to start BTC WebSocket task: {error}"
        )


    yield

    # Graceful shutdown: Cancel the WebSocket task and wait for it to finish
    if btc_task:
        btc_task.cancel()
        try:
            await btc_task
            print("WebSocket task completed successfully")
        except asyncio.CancelledError:
            print("WebSocket task cancelled successfully")
        except Exception as e:
            print(f"Error during WebSocket shutdown: {e}")
        finally:
            btc_task = None


app = FastAPI(
    title="MacroCrypto AI Backend",
    version="0.1.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "message": "MacroCrypto AI Backend is running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for service monitoring.
    
    Used for:
    - Docker health checks
    - Kubernetes liveness/readiness probes
    - Service discovery
    """
    global btc_task
    
    if btc_task is None:
        return {"status": "not_started", "message": "WebSocket task not started"}
    elif btc_task.cancelled():
        return {"status": "cancelled", "message": "WebSocket task cancelled"}
    elif btc_task.done():
        try:
            exception = btc_task.exception()
            if exception:
                return {
                    "status": "error",
                    "message": f"WebSocket task error: {str(exception)}"
                }
        except asyncio.CancelledError:
            return {"status": "cancelled", "message": "WebSocket task cancelled"}
        except Exception as e:
            return {"status": "error", "message": f"Unexpected error: {str(e)}"}
        return {"status": "stopped", "message": "WebSocket task stopped"}
    else:
        return {"status": "running", "message": "WebSocket is active"}