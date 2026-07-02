from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import Settings
from app.services.fallback import call_with_fallback as _call_with_fallback

T = TypeVar("T")

RETRYABLE_EXCEPTIONS = (
    httpx.TimeoutException,
    httpx.ConnectError,
    httpx.RemoteProtocolError,
    httpx.HTTPStatusError,
)


class BaseAPIClient:
    def __init__(self, settings: Settings, client: httpx.AsyncClient | None = None):
        self._settings = settings
        self._client = client or httpx.AsyncClient(timeout=settings.request_timeout_seconds)

    async def aclose(self) -> None:
        await self._client.aclose()

    async def request_with_retry(self, method: str, url: str, **kwargs) -> httpx.Response:
        @retry(
            stop=stop_after_attempt(self._settings.max_retries + 1),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
            retry=retry_if_exception_type(RETRYABLE_EXCEPTIONS),
            reraise=True,
        )
        async def _do() -> httpx.Response:
            resp = await self._client.request(method, url, **kwargs)
            if resp.status_code >= 500:
                raise httpx.HTTPStatusError(
                    f"server error {resp.status_code}", request=resp.request, response=resp
                )
            return resp

        return await _do()

    async def call_with_fallback(
        self,
        step_name: str,
        is_configured: bool,
        live_call: Callable[[], Awaitable[T]],
        demo_loader: Callable[[], T],
    ) -> tuple[T, bool]:
        return await _call_with_fallback(step_name, is_configured, live_call, demo_loader)
