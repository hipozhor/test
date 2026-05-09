from datetime import datetime, timezone

from app.models.schemas import CurrentWeather, ForecastResponse

# ── Emoji maps ────────────────────────────────────────────────────────────────

WEATHER_EMOJI: dict[int, str] = {
    # Thunderstorm
    200: "⛈️", 201: "⛈️", 202: "⛈️", 210: "🌩️", 211: "🌩️",
    212: "🌩️", 221: "🌩️", 230: "⛈️", 231: "⛈️", 232: "⛈️",
    # Drizzle
    300: "🌦️", 301: "🌦️", 302: "🌦️", 310: "🌦️", 311: "🌦️",
    312: "🌦️", 313: "🌦️", 314: "🌦️", 321: "🌦️",
    # Rain
    500: "🌧️", 501: "🌧️", 502: "🌧️", 503: "🌧️", 504: "🌧️",
    511: "🌨️", 520: "🌧️", 521: "🌧️", 522: "🌧️", 531: "🌧️",
    # Snow
    600: "❄️", 601: "❄️", 602: "❄️", 611: "🌨️", 612: "🌨️",
    613: "🌨️", 615: "🌨️", 616: "🌨️", 620: "🌨️", 621: "🌨️", 622: "🌨️",
    # Atmosphere
    701: "🌫️", 711: "🌫️", 721: "🌫️", 731: "🌫️", 741: "🌫️",
    751: "🌫️", 761: "🌫️", 762: "🌋", 771: "🌬️", 781: "🌪️",
    # Clear / Clouds
    800: "☀️", 801: "🌤️", 802: "⛅", 803: "🌥️", 804: "☁️",
}

WIND_DIRECTIONS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

UV_LEVELS = [
    (3, "🟢 Low"),
    (6, "🟡 Moderate"),
    (8, "🟠 High"),
    (11, "🔴 Very High"),
    (float("inf"), "🟣 Extreme"),
]


def _wind_direction(deg: int) -> str:
    idx = round(deg / 45) % 8
    return WIND_DIRECTIONS[idx]


def _beaufort(speed_ms: float) -> str:
    """Beaufort scale label from m/s."""
    thresholds = [
        (0.3, "Calm"), (1.5, "Light air"), (3.3, "Light breeze"),
        (5.5, "Gentle breeze"), (7.9, "Moderate breeze"), (10.7, "Fresh breeze"),
        (13.8, "Strong breeze"), (17.1, "Near gale"), (20.7, "Gale"),
        (24.4, "Strong gale"), (28.4, "Storm"), (32.6, "Violent storm"),
    ]
    for threshold, label in thresholds:
        if speed_ms <= threshold:
            return label
    return "Hurricane"


def _pressure_hpa(hpa: int) -> str:
    if hpa < 1000:
        return f"{hpa} hPa ⬇️"
    if hpa > 1020:
        return f"{hpa} hPa ⬆️"
    return f"{hpa} hPa ➡️"


def _visibility_fmt(meters: int | None) -> str:
    if meters is None:
        return "N/A"
    if meters >= 10000:
        return "≥ 10 km 👁️"
    return f"{meters / 1000:.1f} km"


def _sunrise_sunset(unix: int, offset: int) -> str:
    dt = datetime.fromtimestamp(unix + offset, tz=timezone.utc)
    return dt.strftime("%H:%M")


def weather_emoji(condition_id: int) -> str:
    return WEATHER_EMOJI.get(condition_id, "🌡️")


# ── Public formatters ─────────────────────────────────────────────────────────

def format_current(w: CurrentWeather, city_name: str | None = None) -> str:
    name = city_name or w.name
    cond = w.weather[0]
    emoji = weather_emoji(cond.id)
    temp = w.main.temp
    feels = w.main.feels_like
    t_min = w.main.temp_min
    t_max = w.main.temp_max
    wind_dir = _wind_direction(w.wind.deg)
    wind_speed = w.wind.speed
    beaufort = _beaufort(wind_speed)
    sunrise = _sunrise_sunset(w.sys.sunrise, w.timezone) if w.sys.sunrise else "—"
    sunset = _sunrise_sunset(w.sys.sunset, w.timezone) if w.sys.sunset else "—"
    updated = datetime.fromtimestamp(w.dt + w.timezone, tz=timezone.utc).strftime("%H:%M")

    lines = [
        f"{emoji} <b>{name}</b>",
        f"<i>{cond.description.capitalize()}</i>",
        "",
        f"🌡️  <b>{temp:+.1f}°C</b>  (feels like {feels:+.1f}°C)",
        f"📊  Min {t_min:+.1f}°C  /  Max {t_max:+.1f}°C",
        "",
        f"💧 Humidity: <b>{w.main.humidity}%</b>",
        f"🌬️ Wind: <b>{wind_speed:.1f} m/s {wind_dir}</b> — {beaufort}",
    ]
    if w.wind.gust:
        lines.append(f"💨 Gusts: <b>{w.wind.gust:.1f} m/s</b>")
    lines += [
        f"🔵 Pressure: <b>{_pressure_hpa(w.main.pressure)}</b>",
        f"👁️ Visibility: <b>{_visibility_fmt(w.visibility)}</b>",
        f"☁️ Cloud cover: <b>{w.clouds.all}%</b>",
        "",
        f"🌅 Sunrise: <b>{sunrise}</b>   🌇 Sunset: <b>{sunset}</b>",
        "",
        f"<i>Updated at {updated} local time</i>",
    ]
    return "\n".join(lines)


def format_forecast_short(forecast: ForecastResponse) -> str:
    """Daily summary cards (one per calendar day, noon reading preferred)."""
    # Group by date, pick midday reading
    daily: dict[str, list] = {}
    for item in forecast.list:
        date = item.dt_txt[:10]
        daily.setdefault(date, []).append(item)

    lines = [f"📅 <b>5-day forecast — {forecast.city.name}, {forecast.city.country}</b>\n"]

    for date, items in list(daily.items())[:5]:
        # Prefer ~noon
        best = min(items, key=lambda x: abs(int(x.dt_txt[11:13]) - 12))
        cond = best.weather[0]
        emoji = weather_emoji(cond.id)
        temps = [i.main.temp for i in items]
        t_min, t_max = min(temps), max(temps)
        dt = datetime.strptime(date, "%Y-%m-%d")
        day_label = dt.strftime("%a, %d %b")
        lines.append(
            f"{emoji} <b>{day_label}</b>\n"
            f"   {cond.description.capitalize()}\n"
            f"   🌡️ {t_min:+.0f}°C … {t_max:+.0f}°C\n"
        )

    return "\n".join(lines)


def format_forecast_hourly(forecast: ForecastResponse, hours: int = 8) -> str:
    """Next N × 3-hour steps."""
    lines = [f"⏰ <b>Next {hours * 3}h — {forecast.city.name}, {forecast.city.country}</b>\n"]

    for item in forecast.list[:hours]:
        cond = item.weather[0]
        emoji = weather_emoji(cond.id)
        time_str = item.dt_txt[11:16]
        lines.append(
            f"{emoji} <b>{time_str}</b>  {item.main.temp:+.1f}°C"
            f"  {cond.description.capitalize()}"
            f"  💧{item.main.humidity}%"
        )

    return "\n".join(lines)
