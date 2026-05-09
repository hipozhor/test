from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.database.repository import UserRepository
from app.keyboards import settings_keyboard

router = Router(name="settings")


@router.message(F.text == "⚙️ Settings")
async def settings_menu(message: Message, user_repo: UserRepository) -> None:
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    has_default = bool(user and user.default_city)

    home_str = f"🏠 Home city: <b>{user.default_city}</b>" if has_default else "🏠 Home city: <i>not set</i>"
    fav_count = len(user.favorites) if user else 0

    text = (
        f"⚙️ <b>Settings</b>\n\n"
        f"{home_str}\n"
        f"⭐ Saved cities: <b>{fav_count}</b>"
    )
    await message.answer(text, reply_markup=settings_keyboard(has_default), parse_mode="HTML")


@router.callback_query(F.data == "clear_default")
async def clear_default(callback: CallbackQuery, user_repo: UserRepository) -> None:
    await user_repo.update_default_city(callback.from_user.id, None, None, None)
    await callback.answer("🏠 Home city cleared.")

    user = await user_repo.get_by_telegram_id(callback.from_user.id)
    await callback.message.edit_text(
        "⚙️ <b>Settings</b>\n\n🏠 Home city: <i>not set</i>",
        reply_markup=settings_keyboard(False),
        parse_mode="HTML",
    )
