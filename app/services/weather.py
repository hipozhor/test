import asyncio
import time
from typing import Any

import aiohttp
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.models.schemas import CurrentWeather, ForecastResponse, GeoLocation
from config import settings


class WeatherCache:
    """Simple in-memory TTL cache."""

    def __init__(self, ttl: int) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            value, ts = item
            if time.monotonic() - ts > self._ttl:
                del self._store[key]
                return None
            return value

    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._store[key] = (value, time.monotonic())

    async def invalidate(self, key: str) -> None:
        async with self._lock:
            self._store.pop(key, None)


class WeatherService:
    """Async client for OpenWeatherMap API."""

    def __init__(self) -> None:
        self._api_key = settings.owm_api_key.get_secret_value()
        self._base_url = settings.owm_base_url
        self._geo_url = settings.owm_geo_url
        self._cache = WeatherCache(ttl=settings.weather_cache_ttl)
        self._session: aiohttp.ClientSession | None = None

    async def start(self) -> None:
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"Accept": "application/json"},
        )
        logger.info("WeatherService HTTP session opened ✓")

    async def stop(self) -> None:
        if self._session:
            await self._session.close()
        logger.info("WeatherService HTTP session closed ✓")

    # ── Internal HTTP helper ──────────────────────────────────────────────

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=4))
    async def _get(self, url: str, params: dict) -> dict:
        assert self._session, "WeatherService.start() not called"
        params["appid"] = self._api_key
        async with self._session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()

    # ── Geocoding ─────────────────────────────────────────────────────────

    async def geocode(self, query: str, limit: int = 5) -> list[GeoLocation]:
        """Convert a city name string to geo coordinates."""
        cache_key = f"geo:{query.lower()}:{limit}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached

        data = await self._get(
            f"{self._geo_url}/direct",
            {"q": query, "limit": limit},
        )
        results = [GeoLocation(**item) for item in data]
        await self._cache.set(cache_key, results)
        return results

    async def reverse_geocode(self, lat: float, lon: float) -> GeoLocation | None:
        """Convert coordinates to a city name."""
        cache_key = f"rgeo:{lat:.4f}:{lon:.4f}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached

        data = await self._get(
            f"{self._geo_url}/reverse",
            {"lat": lat, "lon": lon, "limit": 1},
        )
        if not data:
            return None
        result = GeoLocation(**data[0])
        await self._cache.set(cache_key, result)
        return result

    # ── Weather ───────────────────────────────────────────────────────────

    async def get_current_weather(
        self, lat: float, lon: float, units: str = "metric", lang: str = "en"
    ) -> CurrentWeather:
        cache_key = f"current:{lat:.4f}:{lon:.4f}:{units}:{lang}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached

        data = await self._get(
            f"{self._base_url}/weather",
            {"lat": lat, "lon": lon, "units": units, "lang": lang},
        )
        result = CurrentWeather(**data)
        await self._cache.set(cache_key, result)
        return result

    async def get_forecast(
        self, lat: float, lon: float, cnt: int = 40, units: str = "metric", lang: str = "en"
    ) -> ForecastResponse:
        """5-day / 3-hour forecast (cnt = number of 3h steps, max 40)."""
        cache_key = f"forecast:{lat:.4f}:{lon:.4f}:{units}:{lang}"
        cached = await self._cache.get(cache_key)
        if cached:
            return cached

        data = await self._get(
            f"{self._base_url}/forecast",
            {"lat": lat, "lon": lon, "cnt": cnt, "units": units, "lang": lang},
        )
        result = ForecastResponse(**data)
        await self._cache.set(cache_key, result)
        return result


# Singleton
weather_service = WeatherService()
