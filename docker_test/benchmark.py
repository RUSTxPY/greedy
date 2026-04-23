import asyncio
import httpx
import time
import statistics
import json

# Configuration
API_URL = "http://localhost:8000/search/text"
QUERY = "python programming"
CONCURRENCY = 10
TOTAL_REQUESTS = 100

async def fetch(client, i):
    start = time.perf_counter()
    try:
        response = await client.get(API_URL, params={"query": QUERY, "max_results": 5})
        status = response.status_code
        # Consume content
        _ = response.text
        end = time.perf_counter()
        return end - start, status
    except Exception as e:
        return None, str(e)

async def main():
    print(f"🚀 Starting benchmark: {TOTAL_REQUESTS} requests, concurrency={CONCURRENCY}...")
    
    # We use a single AsyncClient for connection pooling
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Control concurrency with a semaphore
        sem = asyncio.Semaphore(CONCURRENCY)
        
        async def sem_fetch(i):
            async with sem:
                return await fetch(client, i)

        start_time = time.perf_counter()
        results = await asyncio.gather(*(sem_fetch(i) for i in range(TOTAL_REQUESTS)))
        end_time = time.perf_counter()

    # Processing results
    latencies = [r[0] for r in results if r[0] is not None]
    errors = [r[1] for r in results if r[0] is None or r[1] != 200]
    
    total_time = end_time - start_time
    rps = TOTAL_REQUESTS / total_time

    print("\n--- Benchmark Results ---")
    print(f"Total Requests: {TOTAL_REQUESTS}")
    print(f"Successful:     {len(latencies) - len([e for e in errors if e != 200])}")
    print(f"Errors:         {len(errors)}")
    print(f"Total Time:     {total_time:.2f}s")
    print(f"Throughput:     {rps:.2f} req/s")
    
    if latencies:
        print(f"Min Latency:    {min(latencies)*1000:.2f}ms")
        print(f"Max Latency:    {max(latencies)*1000:.2f}ms")
        print(f"Avg Latency:    {statistics.mean(latencies)*1000:.2f}ms")
        # statistics.quantiles is in Python 3.8+
        try:
            print(f"P95 Latency:    {statistics.quantiles(latencies, n=20)[18]*1000:.2f}ms")
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
