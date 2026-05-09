from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.repository import UserRepository
from app.filters.states import SearchCityStates
from app.handlers.weather import show_weather
from app.keyboards import CB_BACK_MAIN, CB_SELECT_GEO, geo_results_keyboard
from app.services.weather import weather_service

router = Router()

@router.message(F.text == "🔍 Search City")
async def search_start(message: Message, state: FSMContext):
    await state.set_state(SearchCityStates.waiting_for_query)
    await message.answer("🔍 Введи название города (например, Москва или London):")

@router.message(SearchCityStates.waiting_for_query, F.text)
async def search_query(message: Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        await message.answer("ну напиши что-нибудь")
        return
    await message.answer("🔍 Ищу...")
    try:
        locations = await weather_service.geocode(query, limit=5)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")
        return
    if not locations:
        await message.answer(f"❌ Ничего не нашёл для «{query}»")
        return
    await state.update_data(search_results=[(loc.lat, loc.lon, loc.name, loc.country, loc.display_name) for loc in locations])
    await state.set_state(SearchCityStates.choosing_location)
    await message.answer(f"🗺️ Нашёл {len(locations)} вариант(ов):", reply_markup=geo_results_keyboard(locations))

@router.callback_query(SearchCityStates.choosing_location, F.data.startswith(f"{CB_SELECT_GEO}:"))
async def select_location(callback: CallbackQuery, state: FSMContext, user_repo: UserRepository):
    await callback.answer()
    idx = int(callback.data.split(":")[1])
    data = await state.get_data()
    results = data.get("search_results", [])
    if idx >= len(results):
        await callback.message.edit_text("⚠️ Поиск устарел, попробуй снова")
        await state.clear()
        return
    lat, lon, name, country, display = results[idx]
    city_label = f"{name}, {country}"
    await state.clear()
    await callback.message.edit_text(f"📍 Выбрано: {display}")
    await show_weather(callback.message, lat, lon, city_label)

@router.callback_query(F.data == CB_BACK_MAIN)
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.edit_text("❌ Отменено")