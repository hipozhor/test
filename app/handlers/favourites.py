from aiogram import F, Router
from aiogram.types import CallbackQuery, Message

from app.database.repository import UserRepository
from app.keyboards import (
    CB_ADD_FAV,
    CB_DEL_FAV,
    CB_SET_DEFAULT,
    favourites_keyboard,
)
from config import settings

router = Router(name="favourites")


async def _show_favourites(target: Message | CallbackQuery, user_repo: UserRepository) -> None:
    tg_id = target.from_user.id if isinstance(target, Message) else target.from_user.id
    favorites = await user_repo.get_favorites(tg_id)

    text = (
        f"⭐ <b>Your Favourite Cities</b>  ({len(favorites)}/{settings.max_favorite_cities})\n\n"
        + ("Tap a city to see the weather, or 🗑️ to remove it." if favorites else "You have no favourites yet.")
    )
    keyboard = favourites_keyboard(favorites)

    if isinstance(target, Message):
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")
    elif isinstance(target, CallbackQuery) and target.message:
        await target.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.message(F.text == "⭐ Favourites")
async def favourites_list(message: Message, user_repo: UserRepository) -> None:
    await _show_favourites(message, user_repo)


# ── Add favourite ─────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(f"{CB_ADD_FAV}:"))
async def add_favourite(callback: CallbackQuery, user_repo: UserRepository) -> None:
    parts = callback.data.split(":", 4)
    # add_fav:{lat}:{lon}:{name}
    _, lat_s, lon_s, name = parts[0], parts[1], parts[2], parts[3]
    lat, lon = float(lat_s), float(lon_s)

    # We don't store country/display separately in this callback — use name as display
    favorite = await user_repo.add_favorite(
        telegram_id=callback.from_user.id,
        name=name,
        country="",
        lat=lat,
        lon=lon,
        display_name=name,
        max_favorites=settings.max_favorite_cities,
    )

    if favorite is None:
        await callback.answer(
            f"❌ You can't add more than {settings.max_favorite_cities} cities.",
            show_alert=True,
        )
    else:
        await callback.answer(f"⭐ {name} added to favourites!", show_alert=False)


# ── Remove favourite ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(f"{CB_DEL_FAV}:"))
async def remove_favourite(callback: CallbackQuery, user_repo: UserRepository) -> None:
    fav_id = int(callback.data.split(":")[1])
    removed = await user_repo.remove_favorite(callback.from_user.id, fav_id)

    if removed:
        await callback.answer("🗑️ Removed from favourites.")
    else:
        await callback.answer("⚠️ Not found.")

    await _show_favourites(callback, user_repo)


# ── Set default city ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(f"{CB_SET_DEFAULT}:"))
async def set_default_city(callback: CallbackQuery, user_repo: UserRepository) -> None:
    _, lat_s, lon_s, name = callback.data.split(":", 3)
    lat, lon = float(lat_s), float(lon_s)

    await user_repo.update_default_city(callback.from_user.id, name, lat, lon)
    await callback.answer(f"🏠 {name} set as your home city!", show_alert=False)
