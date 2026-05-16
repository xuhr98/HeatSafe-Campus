import math
from datetime import date, timedelta

import pandas as pd
import requests

from config import (
    AIR_QUALITY_URL,
    AQ_COL_OZONE_DAY,
    AQ_COL_OZONE_MAX,
    AQ_COL_PM10_DAY,
    AQ_COL_PM10_MAX,
    AQ_COL_PM25_DAY,
    AQ_COL_PM25_MAX,
    AQ_COL_US_AQI_DAY,
    AQ_COL_US_AQI_MAX,
    CITY_WEATHER,
    COL_DAYTIME_APPARENT,
    COL_DAYTIME_HUM,
    COL_DAYTIME_TEMP,
    COL_DAYTIME_UV,
    COL_MAX_APPARENT,
    COL_MAX_HUM,
    COL_MAX_TEMP,
    COL_MAX_UV,
    DAYTIME_HOUR_END,
    DAYTIME_HOUR_START,
    FALLBACK_CITY,
    OPEN_METEO_URL,
)
from geocoding import (
    CITY_COORDS,
    _mock_city_key,
    geocode_city,
    geocode_school_with_amap,
    normalize_city_name,
)
from config import get_amap_api_key

def load_forecast(
    city_name: str, school_name: str = "",
) -> tuple[pd.DataFrame, bool, dict, bool, dict]:
    """
    Load 7-day forecast. Tries Amap school geocode when AMAP_API_KEY and school name exist;
    otherwise uses Open-Meteo city geocoding (normalize_city_name for Chinese city names).
    """
    city_original = (city_name or "").strip()
    city_openmeteo = normalize_city_name(city_original or FALLBACK_CITY)
    if len(city_openmeteo) < 2:
        city_openmeteo = FALLBACK_CITY
    city_for_amap = city_original or FALLBACK_CITY

    geocode_failed = False
    meta: dict = {
        "amap_ok": False,
        "amap_fail": False,
        "formatted_address": None,
        "city_display": city_original,
    }

    amap_key = get_amap_api_key()
    school_trim = (school_name or "").strip()

    location: dict | None = None
    if amap_key and school_trim:
        try:
            amap_loc = geocode_school_with_amap(school_trim, city_for_amap)
            fa = amap_loc["formatted_address"]
            location = {
                "latitude": amap_loc["latitude"],
                "longitude": amap_loc["longitude"],
                "display_name": fa or f"{school_trim}, {city_for_amap}",
                "country": "",
                "source": "Amap",
                "formatted_address": fa,
            }
            meta["amap_ok"] = True
            meta["formatted_address"] = fa or None
        except Exception:
            meta["amap_fail"] = True

    if location is None:
        try:
            location = geocode_city(city_openmeteo)
            location.setdefault("source", "Open-Meteo")
            location.setdefault("formatted_address", None)
        except Exception:
            geocode_failed = True
            lat, lon = CITY_COORDS[FALLBACK_CITY]
            location = {
                "latitude": lat,
                "longitude": lon,
                "display_name": FALLBACK_CITY,
                "country": "China",
                "source": "fallback",
                "formatted_address": None,
            }

    try:
        df = fetch_forecast(location["latitude"], location["longitude"])
        return df, True, location, geocode_failed, meta
    except Exception:
        mock_city = FALLBACK_CITY if geocode_failed else _mock_city_key(city_openmeteo)
        return build_mock_forecast(mock_city), False, location, geocode_failed, meta
def build_mock_forecast(city_name: str) -> pd.DataFrame:
    base = CITY_WEATHER[_mock_city_key(city_name)]
    mock_uv_max = [7.2, 8.1, 6.5, 5.0, 7.0, 6.2, 4.8]
    rows = []
    today = date.today()
    for day in range(7):
        max_t = round(base["max_temp"] - day * 0.6 + (day % 2) * 0.5, 1)
        hum_max = int(max(30, min(95, base["humidity"] + day * 2 - 3)))
        apparent_max = round(max_t + 1.5 + (hum_max - 50) * 0.035, 1)
        daytime_t = round(max_t - 1.2, 1)
        daytime_apparent = round(apparent_max - 1.0, 1)
        daytime_hum = int(max(30, min(95, hum_max - 5)))
        daytime_uv = round(mock_uv_max[day] - 0.6, 1)
        iso_d = (today + timedelta(days=day)).isoformat()
        rows.append(
            {
                "ISO date": iso_d,
                "Day": f"Day {day + 1}",
                COL_DAYTIME_TEMP: daytime_t,
                COL_MAX_TEMP: max_t,
                COL_DAYTIME_APPARENT: daytime_apparent,
                COL_MAX_APPARENT: apparent_max,
                COL_DAYTIME_HUM: daytime_hum,
                COL_MAX_HUM: hum_max,
                COL_DAYTIME_UV: daytime_uv,
                COL_MAX_UV: mock_uv_max[day],
                "Conditions": _conditions_label(daytime_uv),
            }
        )
    return pd.DataFrame(rows)


def _conditions_label(uv_index: float | None) -> str:
    if uv_index is None:
        return "Forecast"
    if uv_index >= 8:
        return "Sunny"
    if uv_index >= 5:
        return "Partly cloudy"
    if uv_index >= 2:
        return "Cloudy"
    return "Overcast"
def _hour_from_local_timestamp(time_str: str) -> int:
    return int(time_str[11:13])


def _is_daytime_hour(time_str: str) -> bool:
    h = _hour_from_local_timestamp(time_str)
    return DAYTIME_HOUR_START <= h <= DAYTIME_HOUR_END


def _aggregate_hourly_daytime_avg(
    hourly_times: list[str],
    series_by_key: dict[str, list | None],
) -> dict[str, dict[str, float]]:
    """Per calendar day (YYYY-MM-DD), mean of hourly values from 10:00–16:00 local."""
    sums: dict[str, dict[str, float]] = {}
    counts: dict[str, dict[str, int]] = {}
    for i, time_str in enumerate(hourly_times):
        if not _is_daytime_hour(time_str):
            continue
        day = time_str[:10]
        for key, series in series_by_key.items():
            if series is None or i >= len(series):
                continue
            val = series[i]
            if val is None:
                continue
            sums.setdefault(day, {})[key] = sums.get(day, {}).get(key, 0.0) + float(val)
            counts.setdefault(day, {})[key] = counts.get(day, {}).get(key, 0) + 1
    out: dict[str, dict[str, float]] = {}
    for day, keys in sums.items():
        out[day] = {}
        for key, total in keys.items():
            n = counts[day][key]
            if n:
                out[day][key] = total / n
    return out


def _aggregate_hourly_daily_max(
    hourly_times: list[str],
    series_by_key: dict[str, list | None],
) -> dict[str, dict[str, float]]:
    daily: dict[str, dict[str, float]] = {}
    for i, time_str in enumerate(hourly_times):
        day = time_str[:10]
        for key, series in series_by_key.items():
            if series is None or i >= len(series):
                continue
            val = series[i]
            if val is None:
                continue
            bucket = daily.setdefault(day, {})
            prev = bucket.get(key)
            fv = float(val)
            if prev is None or fv > prev:
                bucket[key] = fv
    return daily


def _daily_max_humidity(hourly_times: list[str], humidity_values: list) -> dict[str, int]:
    daily_max: dict[str, float] = {}
    for time_str, humidity in zip(hourly_times, humidity_values):
        if humidity is None:
            continue
        day = time_str[:10]
        daily_max[day] = max(daily_max.get(day, 0), float(humidity))
    return {day: int(round(value)) for day, value in daily_max.items()}


def primary_series_value(row: pd.Series, daytime_col: str, fallback_col: str):
    """Prefer daytime average; fall back to daily max when hourly daytime data is missing."""
    v = row.get(daytime_col)
    if v is not None and not (isinstance(v, float) and pd.isna(v)):
        return v
    return row.get(fallback_col)

def fetch_forecast(latitude: float, longitude: float) -> pd.DataFrame:
    response = requests.get(
        OPEN_METEO_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,apparent_temperature_max,uv_index_max",
            "hourly": (
                "temperature_2m,apparent_temperature,relative_humidity_2m,uv_index"
            ),
            "timezone": "auto",
            "forecast_days": 7,
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()

    daily = payload["daily"]
    hourly = payload["hourly"]
    times = hourly["time"]
    weather_keys = {
        "temperature_2m": hourly.get("temperature_2m"),
        "apparent_temperature": hourly.get("apparent_temperature"),
        "relative_humidity_2m": hourly.get("relative_humidity_2m"),
        "uv_index": hourly.get("uv_index"),
    }
    daytime_avg = _aggregate_hourly_daytime_avg(times, weather_keys)
    humidity_max_by_day = _daily_max_humidity(
        times, hourly.get("relative_humidity_2m") or []
    )

    rows = []
    for i, date_str in enumerate(daily["time"]):
        max_temp = daily["temperature_2m_max"][i]
        apparent_max = daily["apparent_temperature_max"][i]
        uv_max = daily["uv_index_max"][i]
        hum_max = humidity_max_by_day.get(date_str, 50)
        day_avg = daytime_avg.get(date_str, {})

        def _avg(key: str, fallback):
            if key in day_avg:
                return day_avg[key]
            return fallback

        dt = _avg("temperature_2m", max_temp)
        da = _avg("apparent_temperature", apparent_max)
        dh = _avg("relative_humidity_2m", hum_max)
        duv = _avg("uv_index", uv_max)

        rows.append(
            {
                "ISO date": date_str,
                "Day": pd.to_datetime(date_str).strftime("%a %d %b"),
                COL_DAYTIME_TEMP: round(dt, 1) if dt is not None else None,
                COL_MAX_TEMP: round(max_temp, 1),
                COL_DAYTIME_APPARENT: round(da, 1) if da is not None else None,
                COL_MAX_APPARENT: round(apparent_max, 1) if apparent_max is not None else None,
                COL_DAYTIME_HUM: int(round(dh)) if dh is not None else hum_max,
                COL_MAX_HUM: hum_max,
                COL_DAYTIME_UV: round(duv, 1) if duv is not None else None,
                COL_MAX_UV: round(uv_max, 1) if uv_max is not None else None,
                "Conditions": _conditions_label(duv if duv is not None else uv_max),
            }
        )
    return pd.DataFrame(rows)


def _aggregate_air_quality_hourly(payload: dict) -> tuple[dict[str, dict[str, float]], dict[str, dict[str, float]]]:
    """Return (10:00–16:00 daytime averages, daily maxima) per pollutant by date."""
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        return {}, {}

    series = {
        "pm2_5": hourly.get("pm2_5"),
        "pm10": hourly.get("pm10"),
        "ozone": hourly.get("ozone"),
        "us_aqi": hourly.get("us_aqi"),
    }
    return (
        _aggregate_hourly_daytime_avg(times, series),
        _aggregate_hourly_daily_max(times, series),
    )


def merge_air_quality_into_forecast(df: pd.DataFrame, latitude: float, longitude: float) -> tuple[pd.DataFrame, bool]:
    """Attach daytime-average and daily-max air quality columns. Returns (df, ok)."""
    out = df.copy()
    try:
        response = requests.get(
            AIR_QUALITY_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "hourly": "pm2_5,pm10,ozone,us_aqi",
                "timezone": "auto",
                "forecast_days": 7,
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return out, False

    daytime_maps, max_maps = _aggregate_air_quality_hourly(payload)
    if not daytime_maps and not max_maps:
        return out, False

    if "ISO date" not in out.columns:
        return out, False

    for col in (
        AQ_COL_PM25_DAY,
        AQ_COL_PM25_MAX,
        AQ_COL_PM10_DAY,
        AQ_COL_PM10_MAX,
        AQ_COL_OZONE_DAY,
        AQ_COL_OZONE_MAX,
        AQ_COL_US_AQI_DAY,
        AQ_COL_US_AQI_MAX,
    ):
        out[col] = math.nan

    for idx in range(len(out)):
        dk = str(out.iloc[idx]["ISO date"])[:10]
        d_avg = daytime_maps.get(dk, {})
        d_max = max_maps.get(dk, {})
        if "pm2_5" in d_avg:
            out.loc[out.index[idx], AQ_COL_PM25_DAY] = round(d_avg["pm2_5"], 1)
        elif "pm2_5" in d_max:
            out.loc[out.index[idx], AQ_COL_PM25_DAY] = round(d_max["pm2_5"], 1)
        if "pm2_5" in d_max:
            out.loc[out.index[idx], AQ_COL_PM25_MAX] = round(d_max["pm2_5"], 1)
        if "pm10" in d_avg:
            out.loc[out.index[idx], AQ_COL_PM10_DAY] = round(d_avg["pm10"], 1)
        elif "pm10" in d_max:
            out.loc[out.index[idx], AQ_COL_PM10_DAY] = round(d_max["pm10"], 1)
        if "pm10" in d_max:
            out.loc[out.index[idx], AQ_COL_PM10_MAX] = round(d_max["pm10"], 1)
        if "ozone" in d_avg:
            out.loc[out.index[idx], AQ_COL_OZONE_DAY] = round(d_avg["ozone"], 1)
        elif "ozone" in d_max:
            out.loc[out.index[idx], AQ_COL_OZONE_DAY] = round(d_max["ozone"], 1)
        if "ozone" in d_max:
            out.loc[out.index[idx], AQ_COL_OZONE_MAX] = round(d_max["ozone"], 1)
        if "us_aqi" in d_avg:
            out.loc[out.index[idx], AQ_COL_US_AQI_DAY] = round(d_avg["us_aqi"], 1)
        elif "us_aqi" in d_max:
            out.loc[out.index[idx], AQ_COL_US_AQI_DAY] = round(d_max["us_aqi"], 1)
        if "us_aqi" in d_max:
            out.loc[out.index[idx], AQ_COL_US_AQI_MAX] = round(d_max["us_aqi"], 1)

    out = out.drop(columns=["ISO date"], errors="ignore")
    return out, True


def get_live_weather(city_name: str) -> pd.DataFrame:
    q = normalize_city_name((city_name or "").strip() or FALLBACK_CITY)
    if len(q) < 2:
        q = FALLBACK_CITY
    location = geocode_city(q)
    return fetch_forecast(location["latitude"], location["longitude"])
