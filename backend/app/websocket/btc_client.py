import asyncio
import json
import websockets

BINANCE_WS_URL = (
    "wss://stream.binance.com:9443/ws/btcusdt@ticker"
)

INITIAL_RETRY_DELAY = 1
MAX_RETRY_DELAY = 60
MAX_RETRY_ATTEMPTS = 10
CONNECTION_TIMEOUT = 30  # Connection timeout in seconds


async def connect_btc_price_stream():
    """Connect to Binance WebSocket with automatic reconnection.
    
    Features:
    - Exponential backoff with max retry limit
    - Graceful shutdown on cancellation
    - Connection timeout handling
    - Automatic reconnection on connection loss
    """
    
    retry_delay = INITIAL_RETRY_DELAY
    retry_count = 0

    while True:
        # Check for cancellation before attempting connection
        if asyncio.current_task().cancelled():
            print("Task cancelled, stopping...")
            break

        try:
            print("Connecting to Binance BTC stream...")

            # Use open_timeout for websockets 10.0+
            async with websockets.connect(
                BINANCE_WS_URL,
                open_timeout=CONNECTION_TIMEOUT
            ) as websocket:

                print("Connected to Binance BTC stream")

                # Reset delay and retry count on successful connection
                retry_delay = INITIAL_RETRY_DELAY
                retry_count = 0

                while True:
                    # Check for cancellation before each receive
                    if asyncio.current_task().cancelled():
                        print("Task cancelled, closing connection...")
                        await websocket.close()
                        return

                    message = await websocket.recv()
                    data = json.loads(message)
                    price = float(data["c"])
                    print(f"BTC Price: {price}")

        except asyncio.CancelledError:
            print("WebSocket task cancelled, stopping gracefully...")
            break
        except websockets.ConnectionClosed:
            print("WebSocket connection closed, reconnecting...")
            retry_count += 1
        except TimeoutError:
            print(f"Connection timeout after {CONNECTION_TIMEOUT} seconds")
            retry_count += 1
        except Exception as error:
            print(f"WebSocket error: {error}")
            retry_count += 1

        # Check if max retry attempts exceeded
        if retry_count >= MAX_RETRY_ATTEMPTS:
            print(f"Max retry attempts ({MAX_RETRY_ATTEMPTS}) reached, giving up")
            break

        # Exponential backoff with max delay
        print(f"Retrying in {retry_delay} seconds... (Attempt {retry_count}/{MAX_RETRY_ATTEMPTS})")
        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, MAX_RETRY_DELAY)