from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from app.database.repository import UserRepository
from app.keyboards import main_menu_keyboard

router = Router(name="start")

WELCOME_TEXT = (
    "👋 <b>Welcome to WeatherBot!</b>\n\n"
    "I'll show you real-time weather and 5-day forecasts for any city in the world.\n\n"
    "🏠 <b>My City</b> — weather for your default city\n"
    "⭐ <b>Favourites</b> — your saved cities\n"
    "🔍 <b>Search City</b> — find any city\n"
    "📍 <b>Send Location</b> — detect your city automatically\n\n"
    "Let's start — send me your location or search for a city!"
)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user_repo: UserRepository) -> None:
    await state.clear()

    user, created = await user_repo.get_or_create(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        language_code=message.from_user.language_code or "en",
    )

    if created:
        logger.info(f"New user registered: {user.telegram_id} ({user.first_name})")

    await message.answer(
        WELCOME_TEXT,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    text = (
        "ℹ️ <b>WeatherBot — Help</b>\n\n"
        "<b>Commands:</b>\n"
        "/start — Main menu\n"
        "/help  — This message\n\n"
        "<b>Tips:</b>\n"
        "• Share your location to auto-detect your city\n"
        "• Save up to 10 favourite cities\n"
        "• Set a home city for quick one-tap access\n"
    )
    await message.answer(text, parse_mode="HTML")
