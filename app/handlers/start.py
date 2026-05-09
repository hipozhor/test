from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

from app.database.repository import UserRepository
from app.keyboards import main_menu_keyboard

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, user_repo: UserRepository):
    await state.clear()
    user, created = await user_repo.get_or_create(
        telegram_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username,
        language_code=message.from_user.language_code or "en",
    )
    if created:
        logger.info(f"новый юзер: {user.telegram_id}")
    await message.answer(
        "👋 Привет! Я покажу погоду где угодно.\n\n"
        "🏠 Мой город — твой дом\n"
        "⭐ Избранное — сохранённые города\n"
        "🔍 Поиск — найди любой\n"
        "📍 Отправь локацию — определю автоматически",
        reply_markup=main_menu_keyboard(),
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("/start — главное меню\n/help — эта справка")