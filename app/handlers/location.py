from aiogram import F, Router
from aiogram.types import Message

from app.database.repository import UserRepository
from app.handlers.weather import show_weather
from app.services.weather import weather_service

router = Router()

@router.message(F.location)
async def handle_location(message: Message, user_repo: UserRepository):
    lat = message.location.latitude
    lon = message.location.longitude
    await message.answer("📍 Определяю город...")
    city = await weather_service.reverse_geocode(lat, lon)
    if city:
        city_name = f"{city.name}, {city.country}"
        await user_repo.update_default_city(message.from_user.id, city_name, lat, lon)
        await message.answer(f"✅ Домашний город установлен: {city_name}")
    else:
        city_name = f"{lat:.2f}, {lon:.2f}"
    await show_weather(message, lat, lon, city_name)