from app.services.container import price_service


class MarketDataService:
    """
    Handles incoming BTC market updates.

    Receives raw ticker data from Binance WebSocket
    and forwards normalized values to PriceService
    for calculation and state management.
    """

    def process_ticker_update(
        self,
        data: dict
    ):

        try:

            price_service.update_market_data(

                # Current BTC price
                current_price=float(data["c"]),

                # Binance 24h price movement
                change_24h=float(data["p"]),
                change_24h_percent=float(data["P"]),

                # Binance 24h statistics
                high_24h=float(data["h"]),
                low_24h=float(data["l"]),
                volume_24h=float(data["v"]),
            )


            # Temporary debug output for verification
            # This will be removed once T4.6 is implemented and tested.
            print(
                "Current BTC Snapshot:"
            )

            print(
                price_service.get_snapshot()
            )


        except KeyError as error:

            print(
                f"Missing Binance ticker field: {error}"
            )


        except ValueError as error:

            print(
                f"Invalid Binance ticker value: {error}"
            )


        except Exception as error:

            print(
                f"Unexpected market data processing error: {error}"
            )