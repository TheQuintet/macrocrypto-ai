from dataclasses import dataclass
from datetime import datetime

import httpx

#Binance REST API endpoint for historical daily candles
BINANCE_API = "https://api.binance.com/api/v3/klines"


@dataclass
class DailyCandle:
    """
    Represents one daily BTC price candle.

    Used as historical reference data
    for 7-day price calculations.
    """

    open_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float



class HistoryService:
    """
    Retrieves historical BTC market data.

    Currently uses Binance REST API
    to load daily candles.
    """


    async def get_daily_candles(
        self,
        symbol: str = "BTCUSDT",
        limit: int = 8,
    ) -> list[DailyCandle]:


        params = {
            "symbol": symbol,
            "interval": "1d",
            "limit": limit,
        }


        try:

            async with httpx.AsyncClient() as client:

                response = await client.get(
                    BINANCE_API,
                    params=params,
                    timeout=10,
                )


                response.raise_for_status()


                candles = []


                for item in response.json():

                    candles.append(
                        DailyCandle(

                            # Binance timestamp is milliseconds
                            open_time=datetime.fromtimestamp(
                                item[0] / 1000
                            ),

                            open=float(item[1]),
                            high=float(item[2]),
                            low=float(item[3]),
                            close=float(item[4]),
                            volume=float(item[5]),
                        )
                    )


                return candles


        except httpx.TimeoutException:

            print(
                "Binance historical data request timed out"
            )

            return []


        except httpx.HTTPError as error:

            print(
                f"Binance historical data request failed: {error}"
            )

            return []


        except (IndexError, ValueError) as error:

            print(
                f"Invalid candle data received: {error}"
            )

            return []


        except Exception as error:

            print(
                f"Unexpected history service error: {error}"
            )

            return []