import asyncio
from concurrent.futures import ProcessPoolExecutor
import time

async def test_blocking():
    start = time.time()

    def fake_long_task():
        time.sleep(2)
        return "done"

    async def run_scan_sim():
        print("run_scan_sim starting")
        with ProcessPoolExecutor() as pool:
            pool.submit(fake_long_task)
            print("Scan paused, exiting context manager...")
            # The context manager __exit__ calls pool.shutdown(wait=True)
            # This is a BLOCKING call, which blocks the asyncio event loop thread
        print(f"run_scan_sim exited context manager at {time.time() - start:.2f}")

    async def ticker():
        for i in range(5):
            print(f"tick {i} at {time.time() - start:.2f}")
            await asyncio.sleep(0.5)

    # Run concurrently - the event loop will block waiting for run_scan_sim to finish
    await asyncio.gather(run_scan_sim(), ticker())

if __name__ == "__main__":
    asyncio.run(test_blocking())
