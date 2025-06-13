from concurrent.futures import ThreadPoolExecutor
import asyncio
import browser_test
import config
import multiple_trading

async def main():
    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor() as pool:
        tasks = [
            loop.run_in_executor(pool, multiple_trading.start_multiple_trading, user, config.shares_quantity, "NSE", 3)
            for user in config.ID
        ]
        await asyncio.gather(*tasks)

asyncio.run(main())