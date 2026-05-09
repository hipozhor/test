from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from app.models.db import FavoriteCity
from app.models.schemas import GeoLocation

# ── Callback data prefixes ────────────────────────────────────────────────────
CB_WEATHER_LAT_LON = "weather"      # weather:{lat}:{lon}:{name}
CB_FORECAST_LAT_LON = "forecast"    # forecast:{lat}:{lon}:{name}
CB_HOURLY_LAT_LON = "hourly"        # hourly:{lat}:{lon}:{name}
CB_ADD_FAV = "add_fav"              # add_fav:{lat}:{lon}:{name}:{country}:{display}
CB_DEL_FAV = "del_fav"              # del_fav:{fav_id}
CB_SET_DEFAULT = "set_default"      # set_default:{lat}:{lon}:{name}
CB_SELECT_GEO = "select_geo"        # select_geo:{idx} (index in session search results)
CB_BACK_MAIN = "back_main"


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


# ── Main menu keyboard ────────────────────────────────────────────────────────

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="🏠 My City"),
        KeyboardButton(text="⭐ Favourites"),
    )
    builder.row(
        KeyboardButton(text="🔍 Search City"),
        KeyboardButton(text="📍 Send Location", request_location=True),
    )
    builder.row(
        KeyboardButton(text="⚙️ Settings"),
    )
    return builder.as_markup(resize_keyboard=True)


# ── Weather action buttons ─────────────────────────────────────────────────────

def weather_actions_keyboard(lat: float, lon: float, city_name: str) -> InlineKeyboardMarkup:
    _name = city_name[:20]  # keep callback data short
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="📅 5-Day Forecast",
            callback_data=f"{CB_FORECAST_LAT_LON}:{lat:.4f}:{lon:.4f}:{_name}",
        ),
        InlineKeyboardButton(
            text="⏰ Hourly",
            callback_data=f"{CB_HOURLY_LAT_LON}:{lat:.4f}:{lon:.4f}:{_name}",
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="⭐ Add to Favourites",
            callback_data=f"{CB_ADD_FAV}:{lat:.4f}:{lon:.4f}:{_name}",
        ),
        InlineKeyboardButton(
            text="🏠 Set as Home",
            callback_data=f"{CB_SET_DEFAULT}:{lat:.4f}:{lon:.4f}:{_name}",
        ),
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Refresh", callback_data=f"{CB_WEATHER_LAT_LON}:{lat:.4f}:{lon:.4f}:{_name}")
    )
    return builder.as_markup()


def forecast_back_keyboard(lat: float, lon: float, city_name: str) -> InlineKeyboardMarkup:
    _name = city_name[:20]
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="◀️ Back to Current",
            callback_data=f"{CB_WEATHER_LAT_LON}:{lat:.4f}:{lon:.4f}:{_name}",
        )
    )
    return builder.as_markup()


# ── Geocoding search results ───────────────────────────────────────────────────

def geo_results_keyboard(locations: list[GeoLocation]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, loc in enumerate(locations):
        builder.row(
            InlineKeyboardButton(
                text=f"📍 {loc.display_name}",
                callback_data=f"{CB_SELECT_GEO}:{i}",
            )
        )
    builder.row(
        InlineKeyboardButton(text="❌ Cancel", callback_data=CB_BACK_MAIN)
    )
    return builder.as_markup()


# ── Favourites list ────────────────────────────────────────────────────────────

def favourites_keyboard(favorites: list[FavoriteCity]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for fav in favorites:
        builder.row(
            InlineKeyboardButton(
                text=f"🌤️ {fav.display_name}",
                callback_data=f"{CB_WEATHER_LAT_LON}:{fav.lat:.4f}:{fav.lon:.4f}:{fav.name[:20]}",
            ),
            InlineKeyboardButton(
                text="🗑️",
                callback_data=f"{CB_DEL_FAV}:{fav.id}",
            ),
        )
    if not favorites:
        builder.row(
            InlineKeyboardButton(text="🔍 Search a city to add", callback_data=CB_BACK_MAIN)
        )
    return builder.as_markup()


# ── Settings keyboard ──────────────────────────────────────────────────────────

def settings_keyboard(has_default: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if has_default:
        builder.row(
            InlineKeyboardButton(text="🗑️ Clear Home City", callback_data="clear_default")
        )
    builder.row(
        InlineKeyboardButton(text="◀️ Back", callback_data=CB_BACK_MAIN)
    )
    return builder.as_markup()
