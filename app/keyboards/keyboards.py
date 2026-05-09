from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.models.db import FavoriteCity
from app.models.schemas import GeoLocation

CB_WEATHER = "w"
CB_FORECAST = "f"
CB_HOURLY = "h"
CB_ADD_FAV = "af"
CB_DEL_FAV = "df"
CB_SET_DEFAULT = "sd"
CB_SELECT_GEO = "sg"
CB_BACK_MAIN = "bm"

def main_menu_keyboard():
    kb = ReplyKeyboardBuilder()
    kb.button(text="🏠 My City")
    kb.button(text="⭐ Favourites")
    kb.button(text="🔍 Search City")
    kb.button(text="📍 Send Location", request_location=True)
    kb.button(text="⚙️ Settings")
    kb.adjust(2, 2, 1)
    return kb.as_markup(resize_keyboard=True)

def weather_actions_keyboard(lat: float, lon: float, city_name: str):
    name = city_name[:20]
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📅 5 дней", callback_data=f"{CB_FORECAST}:{lat:.4f}:{lon:.4f}:{name}"),
        InlineKeyboardButton(text="⏰ Почасовой", callback_data=f"{CB_HOURLY}:{lat:.4f}:{lon:.4f}:{name}"),
    )
    builder.row(
        InlineKeyboardButton(text="⭐ В избранное", callback_data=f"{CB_ADD_FAV}:{lat:.4f}:{lon:.4f}:{name}"),
        InlineKeyboardButton(text="🏠 Домой", callback_data=f"{CB_SET_DEFAULT}:{lat:.4f}:{lon:.4f}:{name}"),
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data=f"{CB_WEATHER}:{lat:.4f}:{lon:.4f}:{name}")
    )
    return builder.as_markup()

def forecast_back_keyboard(lat: float, lon: float, city_name: str):
    name = city_name[:20]
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ Назад", callback_data=f"{CB_WEATHER}:{lat:.4f}:{lon:.4f}:{name}")
    return builder.as_markup()

def geo_results_keyboard(locations: list[GeoLocation]):
    builder = InlineKeyboardBuilder()
    for i, loc in enumerate(locations):
        builder.button(text=f"📍 {loc.display_name}", callback_data=f"{CB_SELECT_GEO}:{i}")
    builder.button(text="❌ Отмена", callback_data=CB_BACK_MAIN)
    builder.adjust(1)
    return builder.as_markup()

def favourites_keyboard(favorites: list[FavoriteCity]):
    builder = InlineKeyboardBuilder()
    for fav in favorites:
        builder.row(
            InlineKeyboardButton(text=f"🌤️ {fav.display_name}", callback_data=f"{CB_WEATHER}:{fav.lat:.4f}:{fav.lon:.4f}:{fav.name[:20]}"),
            InlineKeyboardButton(text="🗑️", callback_data=f"{CB_DEL_FAV}:{fav.id}"),
        )
    if not favorites:
        builder.button(text="🔍 Добавить город", callback_data=CB_BACK_MAIN)
    return builder.as_markup()

def settings_keyboard(has_default: bool):
    builder = InlineKeyboardBuilder()
    if has_default:
        builder.button(text="🗑️ Сбросить", callback_data="clear_default")
    builder.button(text="◀️ Назад", callback_data=CB_BACK_MAIN)
    return builder.as_markup()