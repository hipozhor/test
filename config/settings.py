from functools import lru_cache
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    bot_token: SecretStr
    owm_api_key: SecretStr
    owm_base_url: str = "https://api.openweathermap.org/data/2.5"
    owm_geo_url: str = "https://api.openweathermap.org/geo/1.0"
    database_url: str = "sqlite+aiosqlite:///./data/weather_bot.db"
    debug: bool = False
    log_level: str = "INFO"
    weather_cache_ttl: int = 600
    max_favorite_cities: int = 10

@lru_cache(maxsize=1)
def get_settings():
    return Settings()

settings = get_settings()