import asyncio
import sys
import os

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

os.makedirs("logs", exist_ok=True)

logger.remove()
logger.add(
    sys.stderr,
    level=settings.log_level,
    format="<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <message>",
    colorize=True,
)
logger.add("logs/bot.log", rotation="10 MB", retention="14 days", level="DEBUG", encoding="utf-8")

async def on_startup(bot: Bot):
    await init_db()
    await weather_service.start()
    me = await bot.get_me()
    logger.info(f"бот запущен: @{me.username}")

async def on_shutdown(bot: Bot):
    await weather_service.stop()
    logger.info("всё, закрылись")

async def main():
    bot = Bot(
        token=settings.bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(ThrottlingMiddleware(rate=0.5))
    dp.message.middleware(DbSessionMiddleware())
    dp.callback_query.middleware(DbSessionMiddleware())

    dp.include_router(get_router())

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    logger.info("стартую...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

if __name__ == "__main__":
    asyncio.run(main())