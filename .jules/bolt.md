## 2024-05-18 - Async IO offloading for FastAPI routes
**Learning:** In FastAPI applications, synchronous blocking operations (such as file I/O or CPU-bound code) placed directly inside `async def` routes can block the entire event loop, starving other requests.
**Action:** When working with FastAPI and heavy synchronous calls, remember to use `anyio.to_thread.run_sync()` in combination with `functools.partial()` (as `run_sync` only accepts positional arguments for the callable) to properly offload these blocking steps to a worker thread and keep the event loop non-blocking.
