from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import FavoriteCity, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_id: int,
        first_name: str,
        username: str | None = None,
        language_code: str = "en",
    ) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False

        user = User(
            telegram_id=telegram_id,
            first_name=first_name,
            username=username,
            language_code=language_code,
        )
        self._session.add(user)
        await self._session.flush()
        return user, True

    async def update_default_city(
        self, telegram_id: int, city_name: str, lat: float, lon: float
    ) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return None
        user.default_city = city_name
        user.default_lat = lat
        user.default_lon = lon
        await self._session.flush()
        return user

    async def get_favorites(self, telegram_id: int) -> list[FavoriteCity]:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return []
        return list(user.favorites)

    async def add_favorite(
        self,
        telegram_id: int,
        name: str,
        country: str,
        lat: float,
        lon: float,
        display_name: str,
        max_favorites: int = 10,
    ) -> FavoriteCity | None:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return None

        # Idempotent – skip if already saved
        for fav in user.favorites:
            if abs(fav.lat - lat) < 0.01 and abs(fav.lon - lon) < 0.01:
                return fav

        if len(user.favorites) >= max_favorites:
            return None

        favorite = FavoriteCity(
            user_id=user.id,
            name=name,
            country=country,
            lat=lat,
            lon=lon,
            display_name=display_name,
        )
        self._session.add(favorite)
        await self._session.flush()
        user.favorites.append(favorite)
        return favorite

    async def remove_favorite(self, telegram_id: int, favorite_id: int) -> bool:
        user = await self.get_by_telegram_id(telegram_id)
        if not user:
            return False
        for fav in user.favorites:
            if fav.id == favorite_id:
                await self._session.delete(fav)
                await self._session.flush()
                return True
        return False
