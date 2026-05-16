import os

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"
SCHOOL_TYPES = ["Kindergarten", "Primary School", "Middle School"]
FALLBACK_CITY = "Beijing"
LANG_FROM_LABEL = {"中文": "zh", "English": "en"}
CITY_WEATHER = {
    "Beijing": {"max_temp": 34, "humidity": 45},
    "Shanghai": {"max_temp": 36, "humidity": 72},
    "Guangzhou": {"max_temp": 38, "humidity": 78},
    "Shenzhen": {"max_temp": 37, "humidity": 75},
}

SCHOOL_TYPE_FACTOR = {
    "Kindergarten": 1.15,
    "Primary School": 1.05,
    "Middle School": 1.0,
}
DAYTIME_HOUR_START = 10
DAYTIME_HOUR_END = 16  # inclusive local hours for school exposure window
PM25_DAYTIME_RISK_THRESHOLD_UG_M3 = 35.0

COL_DAYTIME_TEMP = "Daytime Avg Temp (°C)"
COL_MAX_TEMP = "Max Temp (°C)"
COL_DAYTIME_APPARENT = "Daytime Avg Feels-like (°C)"
COL_MAX_APPARENT = "Apparent temp (°C)"
COL_DAYTIME_HUM = "Daytime Avg Humidity (%)"
COL_MAX_HUM = "Humidity (%)"
COL_DAYTIME_UV = "Daytime Avg UV Index"
COL_MAX_UV = "UV Index"

AQ_COL_PM25_DAY = "Daytime Avg PM2.5 (µg/m³)"
AQ_COL_PM25_MAX = "PM2.5 max (µg/m³)"
AQ_COL_PM10_DAY = "Daytime Avg PM10 (µg/m³)"
AQ_COL_PM10_MAX = "PM10 max (µg/m³)"
AQ_COL_OZONE_DAY = "Daytime Avg Ozone (µg/m³)"
AQ_COL_OZONE_MAX = "Ozone max (µg/m³)"
AQ_COL_US_AQI_DAY = "Daytime Avg US AQI"
AQ_COL_US_AQI_MAX = "US AQI (max)"


def get_deepseek_api_key() -> str:
    return (os.environ.get("DEEPSEEK_API_KEY") or "").strip()


def get_amap_api_key() -> str:
    return (os.environ.get("AMAP_API_KEY") or "").strip()


def has_deepseek_api_key() -> bool:
    return bool(get_deepseek_api_key())
