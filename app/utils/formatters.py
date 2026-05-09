from datetime import datetime, timezone

from app.models.schemas import CurrentWeather, ForecastResponse

WEATHER_EMOJI = {
    200: "⛈️", 201: "⛈️", 202: "⛈️", 210: "🌩️", 211: "🌩️", 212: "🌩️", 221: "🌩️",
    230: "⛈️", 231: "⛈️", 232: "⛈️", 300: "🌦️", 301: "🌦️", 302: "🌦️", 310: "🌦️",
    311: "🌦️", 312: "🌦️", 313: "🌦️", 314: "🌦️", 321: "🌦️", 500: "🌧️", 501: "🌧️",
    502: "🌧️", 503: "🌧️", 504: "🌧️", 511: "🌨️", 520: "🌧️", 521: "🌧️", 522: "🌧️",
    531: "🌧️", 600: "❄️", 601: "❄️", 602: "❄️", 611: "🌨️", 612: "🌨️", 613: "🌨️",
    615: "🌨️", 616: "🌨️", 620: "🌨️", 621: "🌨️", 622: "🌨️", 701: "🌫️", 711: "🌫️",
    721: "🌫️", 731: "🌫️", 741: "🌫️", 751: "🌫️", 761: "🌫️", 762: "🌋", 771: "🌬️",
    781: "🌪️", 800: "☀️", 801: "🌤️", 802: "⛅", 803: "🌥️", 804: "☁️",
}

WIND_DIRS = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]

def _wind_dir(deg):
    return WIND_DIRS[round(deg / 45) % 8]

def _beaufort(speed):
    
    if speed < 0.3:
        return "Штиль"
    if speed < 1.5:
        return "Тихий"
    if speed < 3.3:
        return "Лёгкий"
    if speed < 5.5:
        return "Слабый"
    if speed < 7.9:
        return "Умеренный"
    if speed < 10.7:
        return "Свежий"
    if speed < 13.8:
        return "Сильный"
    return "Ураган"

def weather_emoji(condition_id):
    return WEATHER_EMOJI.get(condition_id, "🌡️")

def format_current(w, city_name=None):
    name = city_name or w.name
    cond = w.weather[0]
    
    # проверка на дурака
    if not w.main:
        return "Ошибка: нет данных о погоде"
    
    lines = []
    lines.append(f"{weather_emoji(cond.id)} <b>{name}</b>")
    lines.append(f"<i>{cond.description.capitalize()}</i>")
    lines.append("")
    lines.append(f"🌡️  <b>{w.main.temp:+.1f}°C</b>  (ощущается как {w.main.feels_like:+.1f}°C)")
    lines.append(f"📊  Мин {w.main.temp_min:+.1f}°C  /  Макс {w.main.temp_max:+.1f}°C")
    lines.append("")
    lines.append(f"💧 Влажность: <b>{w.main.humidity}%</b>")
    
    wind_speed = w.wind.speed
    wind_dir = _wind_dir(w.wind.deg)
    lines.append(f"🌬️ Ветер: <b>{wind_speed:.1f} м/с {wind_dir}</b> — {_beaufort(wind_speed)}")
    
    if hasattr(w.wind, 'gust') and w.wind.gust:
        lines.append(f"💨 Порывы: <b>{w.wind.gust:.1f} м/с</b>")
    
    
    p = w.main.pressure
    if p < 1000:
        p_str = f"{p} hPa ⬇️"
    elif p > 1020:
        p_str = f"{p} hPa ⬆️"
    else:
        p_str = f"{p} hPa ➡️"
    lines.append(f"🔵 Давление: <b>{p_str}</b>")
    
    
    if w.visibility:
        lines.append(f"👁️ Видимость: <b>{w.visibility/1000:.1f} км</b>")
    else:
        lines.append("👁️ Видимость: N/A")
    
    lines.append(f"☁️ Облачность: <b>{w.clouds.all}%</b>")
    lines.append("")
    
    
    dt = datetime.fromtimestamp(w.dt + w.timezone, tz=timezone.utc)
    lines.append(f"<i>Обновлено в {dt.strftime('%H:%M')}</i>")
    
    return "\n".join(lines)

def format_forecast_short(fc):
    
    days = {}
    for item in fc.list:
        d = item.dt_txt[:10]
        if d not in days:
            days[d] = []
        days[d].append(item)
    
    out = [f"📅 <b>Прогноз на 5 дней — {fc.city.name}, {fc.city.country}</b>\n"]
    
    for date, items in list(days.items())[:5]:
        
        best = items[0]
        for i in items:
            if abs(int(i.dt_txt[11:13]) - 12) < abs(int(best.dt_txt[11:13]) - 12):
                best = i
        cond = best.weather[0]
        temps = [i.main.temp for i in items]
        t_min = min(temps)
        t_max = max(temps)
        dt = datetime.strptime(date, "%Y-%m-%d")
        out.append(
            f"{weather_emoji(cond.id)} <b>{dt.strftime('%a, %d %b')}</b>\n"
            f"   {cond.description.capitalize()}\n"
            f"   🌡️ {t_min:+.0f}°C … {t_max:+.0f}°C\n"
        )
    return "\n".join(out)

def format_forecast_hourly(fc, hours=8):
    out = [f"⏰ <b>Ближайшие {hours*3} ч — {fc.city.name}, {fc.city.country}</b>\n"]
    for i, item in enumerate(fc.list[:hours]):
        cond = item.weather[0]
        out.append(
            f"{weather_emoji(cond.id)} <b>{item.dt_txt[11:16]}</b>  {item.main.temp:+.1f}°C"
            f"  {cond.description.capitalize()}  💧{item.main.humidity}%"
        )
        if (i+1) % 4 == 0 and i+1 < hours:
            out.append("-" * 20)
    return "\n".join(out)