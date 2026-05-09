import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject


class ThrottlingMiddleware(BaseMiddleware):
    """Simple per-user rate limiter."""

    def __init__(self, rate: float = 0.5) -> None:
        """rate: minimum seconds between messages per user."""
        self._rate = rate
        self._bucket: dict[int, float] = {}
        self._lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)

        user_id = event.from_user.id if event.from_user else None
        if user_id is None:
            return await handler(event, data)

        now = time.monotonic()
        async with self._lock:
            last = self._bucket.get(user_id, 0.0)
            if now - last < self._rate:
                return None  # silently drop
            self._bucket[user_id] = now

        return await handler(event, data)
