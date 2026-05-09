from pydantic import BaseModel

class WeatherCondition(BaseModel):
    id: int
    main: str
    description: str
    icon: str

class MainWeather(BaseModel):
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int

class Wind(BaseModel):
    speed: float
    deg: int
    gust: float | None = None

class Clouds(BaseModel):
    all: int

class Sys(BaseModel):
    country: str | None = None
    sunrise: int | None = None
    sunset: int | None = None

class CurrentWeather(BaseModel):
    name: str
    weather: list[WeatherCondition]
    main: MainWeather
    wind: Wind
    clouds: Clouds
    sys: Sys
    visibility: int | None = None
    dt: int
    timezone: int

class ForecastItem(BaseModel):
    dt: int
    main: MainWeather
    weather: list[WeatherCondition]
    wind: Wind
    clouds: Clouds
    visibility: int | None = None
    dt_txt: str

class ForecastCity(BaseModel):
    name: str
    country: str
    sunrise: int
    sunset: int
    timezone: int

class ForecastResponse(BaseModel):
    list: list[ForecastItem]
    city: ForecastCity

class GeoLocation(BaseModel):
    name: str
    local_names: dict[str, str] | None = None
    lat: float
    lon: float
    country: str
    state: str | None = None

    @property
    def display_name(self):
        parts = [self.name]
        if self.state:
            parts.append(self.state)
        parts.append(self.country)
        return ", ".join(parts)