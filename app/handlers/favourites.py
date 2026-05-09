from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.database.repository import UserRepository
from app.keyboards import CB_ADD_FAV, CB_DEL_FAV, CB_SET_DEFAULT, favourites_keyboard
from config import settings

router = Router()

async def _show_fav(target, user_repo):
    tg_id = target.from_user.id
    favs = await user_repo.get_favorites(tg_id)
    text = f"⭐ <b>Избранное</b> ({len(favs)}/{settings.max_favorite_cities})\n\n"
    text += "Нажми на город чтобы посмотреть погоду" if favs else "Пока пусто"
    kb = favourites_keyboard(favs)
    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb)
    elif isinstance(target, CallbackQuery) and target.message:
        await target.message.edit_text(text, reply_markup=kb)

@router.message(F.text == "⭐ Favourites")
async def favourites_list(message: Message, user_repo: UserRepository):
    await _show_fav(message, user_repo)

@router.callback_query(F.data.startswith(f"{CB_ADD_FAV}:"))
async def add_favourite(callback: CallbackQuery, user_repo: UserRepository):
    _, lat_s, lon_s, name = callback.data.split(":", 3)
    lat, lon = float(lat_s), float(lon_s)
    fav = await user_repo.add_favorite(
        telegram_id=callback.from_user.id,
        name=name,
        country="",
        lat=lat,
        lon=lon,
        display_name=name,
        max_favorites=settings.max_favorite_cities,
    )
    if not fav:
        await callback.answer(f"❌ Нельзя больше {settings.max_favorite_cities} городов", show_alert=True)
    else:
        await callback.answer(f"⭐ {name} добавлено!")

@router.callback_query(F.data.startswith(f"{CB_DEL_FAV}:"))
async def remove_favourite(callback: CallbackQuery, user_repo: UserRepository):
    fav_id = int(callback.data.split(":")[1])
    removed = await user_repo.remove_favorite(callback.from_user.id, fav_id)
    await callback.answer("🗑️ Удалено" if removed else "⚠️ Не найдено")
    await _show_fav(callback, user_repo)

@router.callback_query(F.data.startswith(f"{CB_SET_DEFAULT}:"))
async def set_default_city(callback: CallbackQuery, user_repo: UserRepository):
    _, lat_s, lon_s, name = callback.data.split(":", 3)
    lat, lon = float(lat_s), float(lon_s)
    await user_repo.update_default_city(callback.from_user.id, name, lat, lon)
    await callback.answer(f"🏠 {name} теперь домашний!")