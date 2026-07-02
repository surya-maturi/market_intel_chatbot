import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def call_with_fallback(
    step_name: str,
    is_configured: bool,
    live_call: Callable[[], Awaitable[T]],
    demo_loader: Callable[[], T],
) -> tuple[T, bool]:
    if not is_configured:
        logger.warning("%s: not configured, using demo data", step_name)
        return demo_loader(), True
    try:
        result = await live_call()
        return result, False
    except Exception as exc:
        logger.warning("%s: live call failed (%s), falling back to demo data", step_name, exc)
        return demo_loader(), True
