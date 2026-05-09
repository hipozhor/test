from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.database.repository import UserRepository
from app.keyboards import settings_keyboard

router = Router()

@router.message(F.text == "⚙️ Settings")
async def settings_menu(message: Message, user_repo: UserRepository):
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    has_default = bool(user and user.default_city)
    home_str = f"🏠 Дом: <b>{user.default_city}</b>" if has_default else "🏠 Дом: не задан"
    fav_count = len(user.favorites) if user else 0
    await message.answer(f"⚙️ <b>Настройки</b>\n\n{home_str}\n⭐ Избранное: {fav_count}", reply_markup=settings_keyboard(has_default))

@router.callback_query(F.data == "clear_default")
async def clear_default(callback: CallbackQuery, user_repo: UserRepository):
    await user_repo.update_default_city(callback.from_user.id, None, None, None)
    await callback.answer("🏠 Дом сброшен")
    await callback.message.edit_text("⚙️ Настройки\n\n🏠 Дом: не задан", reply_markup=settings_keyboard(False))