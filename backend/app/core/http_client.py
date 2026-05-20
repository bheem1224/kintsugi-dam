"""
Core Request Manager: Centralized HTTP client with rate limiting and retry logic.

All providers and plugins MUST use this HTTP client for external requests.
This ensures:
- Consistent rate limiting across all providers
- Unified retry and backoff behavior
- Centralized configuration management
- Prevention of thundering herd problems
"""

import time
import random
import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional, Callable

import httpx
from httpx import Response


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 3
    base_backoff: float = 0.5  # seconds
    max_backoff: float = 8.0   # seconds
    jitter: float = 0.25       # +/- 25%


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting."""
    # Requests per second allowed; defaults to 1 RPS to prevent API abuse
    requests_per_second: float = 1.0
    # Token bucket capacity (burst size) - Not currently used but good for future
    burst: int = 1


class HttpError(Exception):
    """Exception raised for HTTP errors."""
    def __init__(self, message: str, status: Optional[int] = None, response: Optional[Response] = None):
        super().__init__(message)
        self.status = status
        self.response = response


class RequestManager:
    """
    Central HTTP client with provider-configurable rate-limiting and retries.
    """

    def __init__(self, provider: str, client_factory: Optional[Callable[[], httpx.AsyncClient]] = None,
                 retry: Optional[RetryConfig] = None, rate: Optional[RateLimitConfig] = None):
        """
        Initialize RequestManager for a specific provider.

        Args:
            provider: Provider name
            client_factory: Optional factory to create custom httpx.AsyncClient
            retry: Optional RetryConfig
            rate: Optional RateLimitConfig
        """
        self.provider = provider
        self._client = (client_factory() if client_factory else httpx.AsyncClient())
        self.retry = retry or RetryConfig()
        # Default rate load, could be loaded from db/config
        self.rate = rate or RateLimitConfig(requests_per_second=1.0)
        self._last_call_ts: float = 0.0
        self._rate_lock = asyncio.Lock()  # Protects _last_call_ts for concurrent async execution

    async def _apply_rate_limit(self):
        """Apply rate limiting before making a request."""
        if not self.rate.requests_per_second or self.rate.requests_per_second <= 0:
            return
        min_interval = 1.0 / self.rate.requests_per_second
        async with self._rate_lock:
            now = time.time()
            delta = now - self._last_call_ts
            if delta < min_interval:
                await asyncio.sleep(min_interval - delta)
            self._last_call_ts = time.time()

    def _should_retry(self, resp: Optional[Response], exc: Optional[Exception], attempt: int) -> bool:
        """Determine if a request should be retried."""
        if attempt >= self.retry.max_retries:
            return False
        if exc is not None:
            return True  # network/timeout/etc.
        if resp is None:
            return False
        # Retry on 429 (Too Many Requests) and 5xx (Server Errors)
        if resp.status_code == 429 or 500 <= resp.status_code < 600:
            return True
        return False

    async def _backoff_sleep(self, attempt: int):
        """Apply exponential backoff with jitter."""
        back = min(self.retry.base_backoff * (2 ** (attempt - 1)), self.retry.max_backoff)
        jitter_factor = 1 + random.uniform(-self.retry.jitter, self.retry.jitter)
        await asyncio.sleep(back * jitter_factor)

    async def request(self, method: str, url: str, **kwargs) -> Response:
        """
        Make an HTTP request with automatic retries and rate limiting.
        """
        attempt = 0
        last_exc: Optional[Exception] = None
        last_resp: Optional[Response] = None

        while True:
            attempt += 1
            try:
                await self._apply_rate_limit()
                # httpx uses `timeout` with default 5s
                timeout = kwargs.pop('timeout', 15)
                resp = await self._client.request(method, url, timeout=timeout, **kwargs)
                if not self._should_retry(resp, None, attempt):
                    if resp.status_code >= 400:
                        raise HttpError(f"HTTP {resp.status_code} for {url}", status=resp.status_code, response=resp)
                    return resp
                last_resp = resp
            except Exception as e:
                last_exc = e
                if not self._should_retry(None, e, attempt):
                    if isinstance(e, HttpError):
                        raise e
                    raise HttpError(f"HTTP error for {url}: {e}")

            await self._backoff_sleep(attempt)

    async def get(self, url: str, **kwargs) -> Response:
        """Make a GET request."""
        return await self.request('GET', url, **kwargs)

    async def post(self, url: str, **kwargs) -> Response:
        """Make a POST request."""
        return await self.request('POST', url, **kwargs)

    async def put(self, url: str, **kwargs) -> Response:
        """Make a PUT request."""
        return await self.request('PUT', url, **kwargs)

    async def delete(self, url: str, **kwargs) -> Response:
        """Make a DELETE request."""
        return await self.request('DELETE', url, **kwargs)

    async def patch(self, url: str, **kwargs) -> Response:
        """Make a PATCH request."""
        return await self.request('PATCH', url, **kwargs)

    async def aclose(self):
        """Close the underlying client."""
        await self._client.aclose()


def rate_limited(key: str, min_interval_sec: float) -> Callable:
    """
    Decorator to rate limit a function call based on a key and interval.
    """
    # Note: State in decorator is usually a global, so we'll use a global dict
    # but we will use asyncio.Lock since the target function might be async or sync
    _last_call = {}
    _last_call_lock = asyncio.Lock()

    def decorator(fn):
        async def wrapper(*args, **kwargs):
            now = time.time()
            async with _last_call_lock:
                prev = _last_call.get(key, 0)
                if now - prev < min_interval_sec:
                    return {"rate_limited": True}
                _last_call[key] = now

            # support both async and sync decorated functions
            if asyncio.iscoroutinefunction(fn):
                return await fn(*args, **kwargs)
            else:
                return fn(*args, **kwargs)
        return wrapper
    return decorator


class RateLimiter:
    """
    A generic token-bucket style rate limiter (window-based).
    """
    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.timestamps = []

    async def wait(self):
        """Wait if necessary to respect rate limiting."""
        while True:
            self._clean_old_timestamps()
            if len(self.timestamps) < self.max_requests:
                break
            oldest_timestamp = self.timestamps[0]
            wait_time = oldest_timestamp + self.window_seconds - time.time()
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            # Re-check after sleep: another coroutine may have consumed a slot
        self.timestamps.append(time.time())

    def _clean_old_timestamps(self):
        """Remove timestamps older than the rate limit window."""
        cutoff_time = time.time() - self.window_seconds
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff_time]

    def get_status(self) -> dict:
        """Get current rate limiting status."""
        self._clean_old_timestamps()
        return {
            'requests_in_window': len(self.timestamps),
            'max_requests': self.max_requests,
            'window_seconds': self.window_seconds,
            'remaining_requests': max(0, self.max_requests - len(self.timestamps))
        }


class TokenBucketRateLimiter:
    """A standard thread-safe token bucket rate limiter for API requests."""
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self._lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        async with self._lock:
            now = time.time()
            # Refill tokens based on elapsed time
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
            self.last_refill = now

            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
