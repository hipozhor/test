import asyncio
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from app.database import init_db
from app.handlers import get_router
from app.middlewares import DbSessionMiddleware, ThrottlingMiddleware
from app.services import weather_service
from config import settings


def configure_logging() -> None:
    logger.remove()
    logger.add(
        sys.stderr,
        level=settings.log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> — <level>{message}</level>",
        colorize=True,
    )
    logger.add(
        "logs/bot.log",
        rotation="10 MB",
        retention="14 days",
        level="DEBUG",
        encoding="utf-8",
    )


async def on_startup(bot: Bot) -> None:
    await init_db()
    await weather_service.start()
    me = await bot.get_me()
    logger.info(f"Bot started: @{me.username} (id={me.id})")


async def on_shutdown(bot: Bot) -> None:
    await weather_service.stop()
    logger.info("Bot shut down.")


async def main() -> None:
    import os
    os.makedirs("logs", exist_ok=True)

    configure_logging()

    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # ── Middlewares ───────────────────────────────────────────────────────────
    dp.message.middleware(ThrottlingMiddleware(rate=0.5))
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    # ── Routers ───────────────────────────────────────────────────────────────
    dp.include_router(get_router())

    # ── Lifecycle hooks ───────────────────────────────────────────────────────
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("Starting polling…")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
