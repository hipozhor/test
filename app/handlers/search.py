from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.database.repository import UserRepository
from app.filters.states import SearchCityStates
from app.handlers.weather import show_weather
from app.keyboards import CB_BACK_MAIN, CB_SELECT_GEO, geo_results_keyboard, main_menu_keyboard
from app.services.weather import weather_service

router = Router(name="search")

_SESSION_KEY = "search_results"


@router.message(F.text == "🔍 Search City")
async def search_start(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchCityStates.waiting_for_query)
    await message.answer(
        "🔍 <b>City Search</b>\n\nType a city name (e.g. <i>Amsterdam</i> or <i>New York, US</i>):",
        parse_mode="HTML",
    )


@router.message(SearchCityStates.waiting_for_query, F.text)
async def search_query(message: Message, state: FSMContext) -> None:
    query = message.text.strip()
    if not query:
        await message.answer("Please enter a city name.")
        return

    await message.answer("🔍 Searching…")

    try:
        locations = await weather_service.geocode(query, limit=5)
    except Exception as exc:
        await message.answer(f"⚠️ Search error: {exc}")
        return

    if not locations:
        await message.answer(
            f"❌ No cities found for «{query}».\nTry a different spelling.",
        )
        return

    # Store results in FSM state
    await state.update_data(
        {_SESSION_KEY: [(loc.lat, loc.lon, loc.name, loc.country, loc.display_name) for loc in locations]}
    )
    await state.set_state(SearchCityStates.choosing_location)

    await message.answer(
        f"🗺️ Found <b>{len(locations)}</b> result(s) for «{query}».\nChoose a city:",
        reply_markup=geo_results_keyboard(locations),
        parse_mode="HTML",
    )


@router.callback_query(SearchCityStates.choosing_location, F.data.startswith(f"{CB_SELECT_GEO}:"))
async def select_location(callback: CallbackQuery, state: FSMContext, user_repo: UserRepository) -> None:
    await callback.answer()
    idx = int(callback.data.split(":")[1])

    data = await state.get_data()
    results = data.get(_SESSION_KEY, [])

    if idx >= len(results):
        await callback.message.edit_text("⚠️ Session expired. Please search again.")
        await state.clear()
        return

    lat, lon, name, country, display_name = results[idx]
    city_label = f"{name}, {country}"

    await state.clear()
    await callback.message.edit_text(f"📍 Selected: <b>{display_name}</b>", parse_mode="HTML")
    await show_weather(callback.message, lat, lon, city_label)


@router.callback_query(F.data == CB_BACK_MAIN)
async def back_to_main(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    await callback.message.edit_text("✅ Cancelled.")
