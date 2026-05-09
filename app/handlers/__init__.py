from aiogram import Router

from . import favourites, location, search, settings, start, weather

def get_router() -> Router:
    """Return a root router with all sub-routers included."""
    root = Router(name="root")
    root.include_router(start.router)
    root.include_router(location.router)
    root.include_router(search.router)
    root.include_router(weather.router)
    root.include_router(favourites.router)
    root.include_router(settings.router)
    return root
