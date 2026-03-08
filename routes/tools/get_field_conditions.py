from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests

router = APIRouter(tags=["tools"])


class LocationRequest(BaseModel):
    lat: float
    lon: float


def _first_hourly_value(hourly_data: dict, key: str):
    values = hourly_data.get(key) or []
    return values[0] if values else None


@router.post("/get_field_conditions")
def get_field_conditions(location: LocationRequest) -> dict:
    endpoint = "https://api.open-meteo.com/v1/forecast"
    hourly_fields = [
        "temperature_2m",
        "relativehumidity_2m",
        "apparent_temperature",
        "precipitation",
        "rain",
        "snowfall",
        "uv_index",
        "cloudcover",
        "winddirection_10m",
        "soil_temperature_0cm",
        "soil_moisture_0_1cm",
        "evapotranspiration",
    ]
    params = {
        "latitude": location.lat,
        "longitude": location.lon,
        "current_weather": "true",
        "hourly": ",".join(hourly_fields),
    }

    try:
        response = requests.get(endpoint, params=params, timeout=(10, 30))
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Weather service request failed: {exc}") from exc

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Weather service unavailable")

    data = response.json()
    current = data.get("current_weather") or {}
    hourly = data.get("hourly") or {}

    return {
        "latitude": location.lat,
        "longitude": location.lon,
        "temperature_c": current.get("temperature"),
        "windspeed_kmh": current.get("windspeed"),
        "condition_code": current.get("weathercode"),
        "is_day": bool(current.get("is_day", 0)),
        "humidity_%": _first_hourly_value(hourly, "relativehumidity_2m"),
        "feels_like_c": _first_hourly_value(hourly, "apparent_temperature"),
        "precipitation_mm": _first_hourly_value(hourly, "precipitation"),
        "rain_mm": _first_hourly_value(hourly, "rain"),
        "snowfall_cm": _first_hourly_value(hourly, "snowfall"),
        "uv_index": _first_hourly_value(hourly, "uv_index"),
        "cloudcover_%": _first_hourly_value(hourly, "cloudcover"),
        "windirection_deg": _first_hourly_value(hourly, "winddirection_10m"),
        "soil_temperature_c": _first_hourly_value(hourly, "soil_temperature_0cm"),
        "soil_moisture_%": _first_hourly_value(hourly, "soil_moisture_0_1cm"),
        "evapotranspiration_mm": _first_hourly_value(hourly, "evapotranspiration"),
    }
