import asyncio
import json
import websockets

from app.services.market_data_service import MarketDataService
market_data_service = MarketDataService()

BINANCE_WS_URL = (
    "wss://stream.binance.com:9443/ws/btcusdt@ticker"
)

INITIAL_RETRY_DELAY = 1
MAX_RETRY_DELAY = 60
MAX_RETRY_ATTEMPTS = 10
CONNECTION_TIMEOUT = 30


async def process_btc_ticker_update(data: dict):
    """
    Process BTC ticker updates. 
    Provide live market data to PriceService for calculations and state management.
    """

    market_data_service.process_ticker_update(data)


async def connect_btc_price_stream():
    """
    Connect to Binance WebSocket with automatic reconnection.

    Features:
    - Exponential backoff
    - Graceful shutdown
    - Connection timeout handling
    - Automatic reconnect
    """

    retry_delay = INITIAL_RETRY_DELAY
    retry_count = 0

    while True:

        if asyncio.current_task().cancelled():
            print("Task cancelled, stopping...")
            break

        try:
            print("Connecting to Binance BTC stream...")

            async with websockets.connect(
                BINANCE_WS_URL,
                open_timeout=CONNECTION_TIMEOUT
            ) as websocket:

                print("Connected to Binance BTC stream")

                retry_delay = INITIAL_RETRY_DELAY
                retry_count = 0

                while True:

                    if asyncio.current_task().cancelled():
                        print(
                            "Task cancelled, closing connection..."
                        )

                        await websocket.close()
                        return


                    message = await websocket.recv()

                    data = json.loads(message)


                    # Existing functionality
                    price = float(data["c"])

                    print(
                        f"BTC Price: {price}"
                    )


                    # Update price calculations
                    await process_btc_ticker_update(
                        data
                    )


        except asyncio.CancelledError:
            print(
                "WebSocket task cancelled, stopping gracefully..."
            )
            break


        except websockets.ConnectionClosed:
            print(
                "WebSocket connection closed, reconnecting..."
            )
            retry_count += 1


        except TimeoutError:
            print(
                f"Connection timeout after {CONNECTION_TIMEOUT} seconds"
            )
            retry_count += 1


        except Exception as error:
            print(
                f"WebSocket error: {error}"
            )
            retry_count += 1


        if retry_count >= MAX_RETRY_ATTEMPTS:

            print(
                f"Max retry attempts ({MAX_RETRY_ATTEMPTS}) reached, giving up"
            )

            break


        print(
            f"Retrying in {retry_delay} seconds..."
            f" (Attempt {retry_count}/{MAX_RETRY_ATTEMPTS})"
        )


        await asyncio.sleep(retry_delay)

        retry_delay = min(
            retry_delay * 2,
            MAX_RETRY_DELAY
        )