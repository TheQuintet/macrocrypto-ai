import asyncio
import json
import websockets


BINANCE_WS_URL = (
    "wss://stream.binance.com:9443/ws/btcusdt@ticker"
)


INITIAL_RETRY_DELAY = 1
MAX_RETRY_DELAY = 60


async def connect_btc_price_stream():

    retry_delay = INITIAL_RETRY_DELAY

    while True:
        try:
            print(
                "Connecting to Binance BTC stream..."
            )

            async with websockets.connect(
                BINANCE_WS_URL
            ) as websocket:

                print(
                    "Connected to Binance BTC stream"
                )

                # Reset delay after successful connection
                retry_delay = INITIAL_RETRY_DELAY

                while True:

                    message = await websocket.recv()

                    data = json.loads(message)

                    price = float(data["c"])

                    print(
                        f"BTC Price: {price}"
                    )

        except Exception as error:

            print(
                f"WebSocket error: {error}"
            )

            print(
                f"Retrying in {retry_delay} seconds..."
            )

            await asyncio.sleep(
                retry_delay
            )

            retry_delay = min(
                retry_delay * 2,
                MAX_RETRY_DELAY
            )