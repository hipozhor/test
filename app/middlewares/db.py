from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.database.connection import AsyncSessionLocal
from app.database.repository import UserRepository

class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        async with AsyncSessionLocal() as session:
            data["session"] = session
            data["user_repo"] = UserRepository(session)
            try:
                return await handler(event, data)
            except Exception:
                await session.rollback()
                raise