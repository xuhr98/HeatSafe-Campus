import os

import requests

from config import AMAP_GEOCODE_URL, FALLBACK_CITY, GEOCODING_URL

CITY_COORDS = {
    "Beijing": (39.9042, 116.4074),
    "Shanghai": (31.2304, 121.4737),
    "Guangzhou": (23.1291, 113.2644),
    "Shenzhen": (22.5431, 114.0579),
}

# Chinese → ASCII names for Open-Meteo geocoding (Amap uses the user-entered city string).
CITY_NAME_ALIASES = {
    "北京": "Beijing",
    "上海": "Shanghai",
    "广州": "Guangzhou",
    "深圳": "Shenzhen",
    "杭州": "Hangzhou",
    "成都": "Chengdu",
    "重庆": "Chongqing",
    "南京": "Nanjing",
    "武汉": "Wuhan",
    "西安": "Xi'an",
    "天津": "Tianjin",
    "苏州": "Suzhou",
    "青岛": "Qingdao",
    "厦门": "Xiamen",
    "长沙": "Changsha",
    "郑州": "Zhengzhou",
    "昆明": "Kunming",
    "沈阳": "Shenyang",
    "大连": "Dalian",
    "哈尔滨": "Harbin",
}
def normalize_city_name(city_name: str) -> str:
    """Strip whitespace; map known Chinese labels to English for Open-Meteo APIs."""
    s = city_name.strip()
    return CITY_NAME_ALIASES.get(s, s)
def _match_predefined_city(city_name: str) -> str | None:
    query = city_name.strip().lower()
    for name in CITY_COORDS:
        if name.lower() == query:
            return name
    return None


def _mock_city_key(city_name: str) -> str:
    return _match_predefined_city(city_name) or FALLBACK_CITY
def geocode_school_with_amap(school_name: str, city_name: str) -> dict:
    """
    Resolve school coordinates via Amap Geocode API.
    Requires AMAP_API_KEY. Returns latitude, longitude, formatted_address, source=\"Amap\".
    """
    key = (os.environ.get("AMAP_API_KEY") or "").strip()
    if not key:
        raise ValueError("AMAP_API_KEY not set")

    city = (city_name or "").strip()
    school = school_name.strip()
    address = f"{city}{school}"

    response = requests.get(
        AMAP_GEOCODE_URL,
        params={
            "key": key,
            "address": address,
            "city": city,
            "output": "JSON",
        },
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    if str(data.get("status")) != "1":
        reason = data.get("info") or data.get("infocode") or "Amap geocode error"
        raise ValueError(str(reason))

    geocodes = data.get("geocodes") or []
    if not geocodes:
        raise ValueError("Amap returned no geocodes")

    loc_str = geocodes[0].get("location") or ""
    parts = loc_str.split(",")
    if len(parts) != 2:
        raise ValueError("Invalid Amap location format")
    longitude, latitude = float(parts[0]), float(parts[1])
    formatted_address = geocodes[0].get("formatted_address") or ""

    return {
        "latitude": latitude,
        "longitude": longitude,
        "formatted_address": formatted_address,
        "source": "Amap",
    }


def geocode_city(city_name: str) -> dict:
    query = city_name.strip()
    if len(query) < 2:
        raise ValueError("City name too short")

    predefined = _match_predefined_city(query)
    if predefined:
        lat, lon = CITY_COORDS[predefined]
        return {
            "latitude": lat,
            "longitude": lon,
            "display_name": predefined,
            "country": "China",
        }

    response = requests.get(
        GEOCODING_URL,
        params={"name": query, "count": 1, "language": "en"},
        timeout=10,
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        raise ValueError(f"City not found: {query}")

    place = results[0]
    return {
        "latitude": place["latitude"],
        "longitude": place["longitude"],
        "display_name": place["name"],
        "country": place.get("country", ""),
    }


def format_location(location: dict) -> str:
    country = location.get("country", "")
    name = location["display_name"]
    return f"{name}, {country}" if country else name
