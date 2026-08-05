import asyncio

from app.collectors.coingecko import CoinGeckoCollector


async def test():
    collector = CoinGeckoCollector()

    result = await collector.get_btc_market_cap()

    print(result)

    await collector.close()


asyncio.run(test())