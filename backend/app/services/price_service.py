from dataclasses import dataclass
from datetime import datetime


@dataclass
class PriceSnapshot:
    """
    Represents the current BTC market state.

    Contains:
    - Current price
    - 24h market statistics
    - 7d calculated price movement
    - Last update timestamp
    """

    current_price: float

    change_24h: float
    change_24h_percent: float

    high_24h: float
    low_24h: float
    volume_24h: float

    change_7d: float | None = None
    change_7d_percent: float | None = None

    updated_at: datetime | None = None



class PriceService:
    """
    Maintains BTC price state and performs
    market calculations.

    Responsibilities:
    - Store latest BTC price data
    - Calculate 7-day price changes
    - Provide current market snapshot
    """


    def __init__(self):

        self.snapshot = PriceSnapshot(
            current_price=0,

            change_24h=0,
            change_24h_percent=0,

            high_24h=0,
            low_24h=0,
            volume_24h=0,

            updated_at=datetime.utcnow()
        )


        # Reference BTC closing price from
        # historical candles used for 7-day calculation.
        self.price_7d_reference = None



    def initialize_from_history(
        self,
        candles
    ):
        """
        Initialize historical reference data.

        The first candle close price is used as
        the 7-day comparison baseline.
        """

        try:

            if not candles:

                print(
                    "No historical candles available"
                )

                return


            self.price_7d_reference = candles[0].close


            print(
                f"7-day reference initialized: "
                f"{self.price_7d_reference}"
            )


        except Exception as error:

            print(
                f"Historical initialization failed: {error}"
            )



    def update_market_data(
        self,
        current_price: float,

        change_24h: float,
        change_24h_percent: float,

        high_24h: float,
        low_24h: float,

        volume_24h: float,
    ):
        """
        Update BTC market data from live WebSocket events.

        Called every time Binance sends a ticker update.
        """


        try:

            self.snapshot.current_price = current_price

            self.snapshot.change_24h = change_24h
            self.snapshot.change_24h_percent = (
                change_24h_percent
            )

            self.snapshot.high_24h = high_24h
            self.snapshot.low_24h = low_24h

            self.snapshot.volume_24h = volume_24h


            # Recalculate 7-day movement
            # whenever live price changes.
            self._calculate_7d_change()


            self.snapshot.updated_at = datetime.utcnow()



        except Exception as error:

            print(
                f"Market data update failed: {error}"
            )



    def _calculate_7d_change(self):
        """
        Calculate absolute and percentage
        BTC price movement over 7 days.
        """

        try:

            if self.price_7d_reference is None:

                self.snapshot.change_7d = None

                self.snapshot.change_7d_percent = None

                return


            current_price = (
                self.snapshot.current_price
            )


            self.snapshot.change_7d = (
                current_price -
                self.price_7d_reference
            )


            self.snapshot.change_7d_percent = (
                (
                    self.snapshot.change_7d /
                    self.price_7d_reference
                )
                * 100
            )


        except Exception as error:

            print(
                f"7-day calculation failed: {error}"
            )



    def get_snapshot(self) -> PriceSnapshot:
        """
        Return current BTC market snapshot.
        """

        return self.snapshot