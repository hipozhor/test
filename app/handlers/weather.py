from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.repository import UserRepository
from app.keyboards import (
    CB_FORECAST_LAT_LON,
    CB_HOURLY_LAT_LON,
    CB_WEATHER_LAT_LON,
    forecast_back_keyboard,
    main_menu_keyboard,
    weather_actions_keyboard,
)
from app.services.weather import weather_service
from app.utils.formatters import format_current, format_forecast_hourly, format_forecast_short

router = Router(name="weather")


async def show_weather(
    target: Message | CallbackQuery,
    lat: float,
    lon: float,
    city_name: str,
    edit: bool = False,
) -> None:
    """Shared helper that shows current weather."""
    try:
        weather = await weather_service.get_current_weather(lat, lon)
    except Exception as exc:
        err = f"⚠️ Couldn't fetch weather: {exc}"
        if edit and isinstance(target, CallbackQuery) and target.message:
            await target.message.edit_text(err)
        elif isinstance(target, Message):
            await target.answer(err)
        return

    text = format_current(weather, city_name)
    keyboard = weather_actions_keyboard(lat, lon, city_name)

    if edit and isinstance(target, CallbackQuery) and target.message:
        await target.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    elif isinstance(target, Message):
        await target.answer(text, reply_markup=keyboard, parse_mode="HTML")
    elif isinstance(target, CallbackQuery) and target.message:
        await target.message.answer(text, reply_markup=keyboard, parse_mode="HTML")


# ── "My City" button ──────────────────────────────────────────────────────────

@router.message(F.text == "🏠 My City")
async def my_city(message: Message, user_repo: UserRepository) -> None:
    user = await user_repo.get_by_telegram_id(message.from_user.id)
    if not user or not user.default_city:
        await message.answer(
            "🏠 You haven't set a home city yet.\n"
            "Send your 📍 <b>Location</b> or use <b>🔍 Search City</b> to set one.",
            parse_mode="HTML",
        )
        return

    await show_weather(message, user.default_lat, user.default_lon, user.default_city)


# ── Callback: show weather at coords ─────────────────────────────────────────

@router.callback_query(F.data.startswith(f"{CB_WEATHER_LAT_LON}:"))
async def cb_weather(callback: CallbackQuery) -> None:
    await callback.answer()
    _, lat_s, lon_s, name = callback.data.split(":", 3)
    await show_weather(callback, float(lat_s), float(lon_s), name, edit=True)


# ── Callback: 5-day forecast ──────────────────────────────────────────────────

@router.callback_query(F.data.startswith(f"{CB_FORECAST_LAT_LON}:"))
async def cb_forecast(callback: CallbackQuery) -> None:
    await callback.answer("Loading forecast…")
    _, lat_s, lon_s, name = callback.data.split(":", 3)
    lat, lon = float(lat_s), float(lon_s)

    try:
        forecast = await weather_service.get_forecast(lat, lon)
    except Exception as exc:
        await callback.message.edit_text(f"⚠️ Error: {exc}")
        return

    text = format_forecast_short(forecast)
    await callback.message.edit_text(
        text,
        reply_markup=forecast_back_keyboard(lat, lon, name),
        parse_mode="HTML",
    )


# ── Callback: hourly ──────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith(f"{CB_HOURLY_LAT_LON}:"))
async def cb_hourly(callback: CallbackQuery) -> None:
    await callback.answer("Loading hourly…")
    _, lat_s, lon_s, name = callback.data.split(":", 3)
    lat, lon = float(lat_s), float(lon_s)

    try:
        forecast = await weather_service.get_forecast(lat, lon)
    except Exception as exc:
        await callback.message.edit_text(f"⚠️ Error: {exc}")
        return

    text = format_forecast_hourly(forecast, hours=8)
    await callback.message.edit_text(
        text,
        reply_markup=forecast_back_keyboard(lat, lon, name),
        parse_mode="HTML",
    )
