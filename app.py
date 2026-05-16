"""HeatSafe Campus — Streamlit MVP (Open-Meteo + mock fallback)."""

import folium
import html
import json
import math
import os
import re
from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from streamlit_folium import st_folium
from plotly.subplots import make_subplots

SCHOOL_TYPES = ["Kindergarten", "Primary School", "Middle School"]
FALLBACK_CITY = "Beijing"

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

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
AMAP_GEOCODE_URL = "https://restapi.amap.com/v3/geocode/geo"
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"

LANG_FROM_LABEL = {"中文": "zh", "English": "en"}

SCHOOL_TYPE_LABELS = {
    "zh": {
        "Kindergarten": "幼儿园",
        "Primary School": "小学",
        "Middle School": "初中",
    },
    "en": {
        "Kindergarten": "Kindergarten",
        "Primary School": "Primary School",
        "Middle School": "Middle School",
    },
}

RISK_SHORT = {
    "zh": {"Low": "低", "Moderate": "中等", "High": "高", "Extreme": "极高"},
    "en": {"Low": "Low", "Moderate": "Moderate", "High": "High", "Extreme": "Extreme"},
}

RISK_LEGEND_CHIPS = {
    "zh": [
        ("一级 · 低", "#2E7D32", "#E8F5E9"),
        ("二级 · 中等", "#F9A825", "#FFF8E1"),
        ("三级 · 高", "#EF6C00", "#FFF3E0"),
        ("四级 · 极高", "#C62828", "#FFEBEE"),
    ],
    "en": [
        ("Level 1 · Low", "#2E7D32", "#E8F5E9"),
        ("Level 2 · Moderate", "#F9A825", "#FFF8E1"),
        ("Level 3 · High", "#EF6C00", "#FFF3E0"),
        ("Level 4 · Extreme", "#C62828", "#FFEBEE"),
    ],
}

RISK_LEVEL_LONG = {
    "zh": {"Low": "一级 · 低", "Moderate": "二级 · 中等", "High": "三级 · 高", "Extreme": "四级 · 极高"},
    "en": {
        "Low": "Level 1 · Low",
        "Moderate": "Level 2 · Moderate",
        "High": "Level 3 · High",
        "Extreme": "Level 4 · Extreme",
    },
}

STRINGS = {
    "zh": {
        "sidebar_header": "### 🏫 学校设置",
        "sidebar_caption": "请输入学校与城市，评估今日儿童高温健康风险。",
        "lang_label": "Language / 语言",
        "school_name": "学校名称",
        "school_ph": "例如：阳光小学",
        "city_name": "城市名称",
        "city_ph": "例如：北京、东京、上海",
        "school_type": "学段 / 学校类型",
        "outdoor": "今日计划开展户外活动",
        "use_ai": "使用 AI 生成建议",
        "tip_climate": "🌡️ **气象** · 尽量使用实时天气数据",
        "tip_school": "🏫 **学校** · 面向儿童的综合风险因素",
        "tip_safety": "⚠️ **安全** · 预警与健康教育，非医学诊断",
        "hero_title": "🌤️ 热浪安全校园 (HeatSafe Campus)",
        "hero_sub": "中国校园儿童高温健康风险 AI 预警系统",
        "hero_desc": "面向学校与儿童的 AI 驱动高温健康预警系统。",
        "warn_city": "未找到城市，已改用北京演示数据。",
        "ok_amap": "已使用高德地图定位学校位置",
        "amap_addr_prefix": "高德返回地址：",
        "warn_amap_fallback": "高德地图未能定位该学校，已改用城市坐标。",
        "ok_live": "正在使用 Open-Meteo 实时天气数据。",
        "warn_mock": "无法获取实时天气，使用演示模拟数据。",
        "warn_aq": "Open-Meteo 空气质量接口不可用，正在继续使用不含空气质量因子的预警。",
        "warn_no_key": "未检测到 DeepSeek API 密钥，改用规则模板建议。",
        "warn_ai_fail": "AI 建议不可用，改用规则模板建议。",
        "ctx_data": "数据",
        "ctx_live": "Open-Meteo 实时",
        "ctx_demo": "演示模拟",
        "ctx_outdoor": "· 今日计划户外活动",
        "sec_dash": "📊 今日高温健康看板",
        "risk_scale": "风险等级：",
        "metric_risk": "风险等级",
        "metric_temp": "气温",
        "metric_hum": "湿度",
        "metric_uv": "紫外线指数",
        "metric_temp_sub": "今日预报最高气温",
        "metric_hum_sub": "日最高相对湿度",
        "metric_uv_sub": "今日紫外线峰值",
        "metric_aqi": "US AQI",
        "metric_pm25": "PM2.5",
        "metric_aqi_sub": "当日小时最大值（美国 AQI）",
        "metric_pm25_sub": "当日最大浓度（µg/m³）",
        "metric_score": "得分",
        "sec_chart": "📈 七日天气趋势",
        "chart_cap": "气温与湿度展望 ·",
        "chart_live": "实时",
        "chart_mock": "模拟",
        "exp_table": "📋 查看七日预报明细表",
        "sec_guide": "👧 分角色儿童安全建议",
        "cap_ai_ok": "基于今日上下文由 DeepSeek 生成的建议。关闭 AI 或请求失败时使用规则模板。",
        "cap_rules": "基于今日风险等级、气温、湿度、紫外线、空气质量（若可用）与活动安排的规则建议。",
        "role_teachers": "教师",
        "role_parents": "家长",
        "role_nurses": "校医",
        "placeholder_school": "您的学校",
        "disclaimer": (
            "<strong>免责声明：</strong>本工具仅提供预警与健康教育支持，不提供医学诊断。"
        ),
        "chart_legend_max_temp": "最高气温 (°C)",
        "chart_legend_hum": "相对湿度 (%)",
        "chart_y_temp": "气温 (°C)",
        "chart_y_hum": "相对湿度 (%)",
        "sec_map": "学校位置地图",
        "map_unavailable": "当前无法显示学校位置地图。成功通过高德地图定位学校后即可查看。",
    },
    "en": {
        "sidebar_header": "### 🏫 School settings",
        "sidebar_caption": "Enter your school and city to assess today's child heat health risk.",
        "lang_label": "Language / 语言",
        "school_name": "School name",
        "school_ph": "e.g. Sunshine Elementary",
        "city_name": "City name",
        "city_ph": "e.g. Beijing, Tokyo, Shanghai",
        "school_type": "School type",
        "outdoor": "Outdoor activity planned today",
        "use_ai": "Use AI-generated guidance",
        "tip_climate": "🌡️ **Climate** · Live weather when available",
        "tip_school": "🏫 **School** · Child-focused risk factors",
        "tip_safety": "⚠️ **Safety** · Early warning, not diagnosis",
        "hero_title": "🌤️ HeatSafe Campus",
        "hero_sub": "AI-powered heat health early warning system for schools and children.",
        "hero_desc": "School-focused prototype for heat planning and child safety.",
        "warn_city": "City not found. Falling back to Beijing demo data.",
        "ok_amap": "School location resolved by Amap",
        "amap_addr_prefix": "Amap address:",
        "warn_amap_fallback": "Could not locate the school via Amap. Using city-level coordinates.",
        "ok_live": "Using live weather data from Open-Meteo.",
        "warn_mock": "Live weather data unavailable. Using demo mock data.",
        "warn_aq": "Air Quality API unavailable. Continuing without air quality in the risk score.",
        "warn_no_key": "DeepSeek API key not found. Using rule-based guidance.",
        "warn_ai_fail": "AI guidance unavailable. Using rule-based guidance.",
        "ctx_data": "Data",
        "ctx_live": "live Open-Meteo data",
        "ctx_demo": "demo mock data",
        "ctx_outdoor": " · Outdoor activity planned",
        "sec_dash": "📊 Today's heat health dashboard",
        "risk_scale": "Risk scale:",
        "metric_risk": "Risk level",
        "metric_temp": "Temperature",
        "metric_hum": "Humidity",
        "metric_uv": "UV index",
        "metric_temp_sub": "Today's forecast max",
        "metric_hum_sub": "Daily maximum",
        "metric_uv_sub": "Peak UV today",
        "metric_aqi": "US AQI",
        "metric_pm25": "PM2.5",
        "metric_aqi_sub": "Daily max (hourly)",
        "metric_pm25_sub": "Daily max concentration (µg/m³)",
        "metric_score": "Score",
        "sec_chart": "📈 7-day weather trend",
        "chart_cap": "Temperature and humidity outlook ·",
        "chart_live": "live data",
        "chart_mock": "mock data",
        "exp_table": "📋 View detailed 7-day forecast table",
        "sec_guide": "👧 Role-specific guidance for child safety",
        "cap_ai_ok": "AI-generated guidance (DeepSeek) from today's context. "
        "Rule-based templates apply if AI is off or unavailable.",
        "cap_rules": "Rule-based actions from today's risk level, temperature, humidity, UV, "
        "air quality (when available), and activity plan.",
        "role_teachers": "Teachers",
        "role_parents": "Parents",
        "role_nurses": "School Nurses",
        "placeholder_school": "Your school",
        "disclaimer": (
            "<strong>Disclaimer:</strong> This tool provides early warning and health education support only. "
            "It does not provide medical diagnosis."
        ),
        "chart_legend_max_temp": "Max temperature (°C)",
        "chart_legend_hum": "Humidity (%)",
        "chart_y_temp": "Temperature (°C)",
        "chart_y_hum": "Humidity (%)",
        "sec_map": "School Location Map",
        "map_unavailable": "School location map is unavailable. Resolve the school with Amap to view the map.",
    },
}

FORECAST_COLUMN_NAMES = {
    "zh": {
        "Day": "日期",
        "Max Temp (°C)": "最高气温 (°C)",
        "Apparent temp (°C)": "体感最高温 (°C)",
        "Humidity (%)": "相对湿度 (%)",
        "UV Index": "紫外线指数",
        "Conditions": "天气状况",
        "US AQI (max)": "US AQI（日最大）",
        "PM2.5 max (µg/m³)": "PM2.5 日最大（µg/m³）",
        "PM10 max (µg/m³)": "PM10 日最大（µg/m³）",
        "Ozone max (µg/m³)": "臭氧日最大（µg/m³）",
    },
}

CONDITION_LABELS_ZH = {
    "Forecast": "预报",
    "Sunny": "晴",
    "Partly cloudy": "多云",
    "Cloudy": "阴",
    "Overcast": "阴天",
    "Light rain": "小雨",
}


def localize_forecast_display(df: pd.DataFrame, lang: str) -> pd.DataFrame:
    """Rename columns / condition strings for display only."""
    df = df.drop(columns=["ISO date"], errors="ignore")
    if lang == "en":
        return df
    out = df.rename(columns=FORECAST_COLUMN_NAMES["zh"])
    cond_src = "Conditions"
    if cond_src in df.columns:
        zh_col = FORECAST_COLUMN_NAMES["zh"][cond_src]
        out[zh_col] = df[cond_src].map(lambda x: CONDITION_LABELS_ZH.get(str(x), x))
    return out


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

RISK_STYLES = {
    "Low": {
        "level": 1,
        "color": "#2E7D32",
        "bg": "#E8F5E9",
    },
    "Moderate": {
        "level": 2,
        "color": "#F9A825",
        "bg": "#FFF8E1",
    },
    "High": {
        "level": 3,
        "color": "#EF6C00",
        "bg": "#FFF3E0",
    },
    "Extreme": {
        "level": 4,
        "color": "#C62828",
        "bg": "#FFEBEE",
    },
}


def _match_predefined_city(city_name: str) -> str | None:
    query = city_name.strip().lower()
    for name in CITY_COORDS:
        if name.lower() == query:
            return name
    return None


def _mock_city_key(city_name: str) -> str:
    return _match_predefined_city(city_name) or FALLBACK_CITY


def build_mock_forecast(city_name: str) -> pd.DataFrame:
    base = CITY_WEATHER[_mock_city_key(city_name)]
    mock_uv = [7.2, 8.1, 6.5, 5.0, 7.0, 6.2, 4.8]
    rows = []
    today = date.today()
    for day in range(7):
        max_t = round(base["max_temp"] - day * 0.6 + (day % 2) * 0.5, 1)
        hum = int(max(30, min(95, base["humidity"] + day * 2 - 3)))
        # Mock “feels like” max when live apparent temp is unavailable
        apparent = round(max_t + 1.5 + (hum - 50) * 0.035, 1)
        iso_d = (today + timedelta(days=day)).isoformat()
        rows.append(
            {
                "ISO date": iso_d,
                "Day": f"Day {day + 1}",
                "Max Temp (°C)": max_t,
                "Apparent temp (°C)": apparent,
                "Humidity (%)": hum,
                "UV Index": mock_uv[day],
                "Conditions": ["Sunny", "Partly cloudy", "Cloudy", "Light rain"][day % 4],
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


def _daily_max_humidity(hourly_times: list[str], humidity_values: list) -> dict[str, int]:
    daily_max: dict[str, float] = {}
    for time_str, humidity in zip(hourly_times, humidity_values):
        if humidity is None:
            continue
        day = time_str[:10]
        daily_max[day] = max(daily_max.get(day, 0), humidity)
    return {day: int(round(value)) for day, value in daily_max.items()}


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


def fetch_forecast(latitude: float, longitude: float) -> pd.DataFrame:
    response = requests.get(
        OPEN_METEO_URL,
        params={
            "latitude": latitude,
            "longitude": longitude,
            "daily": "temperature_2m_max,apparent_temperature_max,uv_index_max",
            "hourly": "relative_humidity_2m",
            "timezone": "auto",
            "forecast_days": 7,
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()

    daily = payload["daily"]
    hourly = payload["hourly"]
    humidity_by_day = _daily_max_humidity(
        hourly["time"], hourly["relative_humidity_2m"]
    )

    rows = []
    for i, date_str in enumerate(daily["time"]):
        max_temp = daily["temperature_2m_max"][i]
        apparent = daily["apparent_temperature_max"][i]
        humidity = humidity_by_day.get(date_str, 50)
        uv_index = daily["uv_index_max"][i]
        rows.append(
            {
                "ISO date": date_str,
                "Day": pd.to_datetime(date_str).strftime("%a %d %b"),
                "Max Temp (°C)": round(max_temp, 1),
                "Apparent temp (°C)": round(apparent, 1) if apparent is not None else None,
                "Humidity (%)": humidity,
                "UV Index": round(uv_index, 1) if uv_index is not None else None,
                "Conditions": _conditions_label(uv_index),
            }
        )
    return pd.DataFrame(rows)


AQ_COL_PM25 = "PM2.5 max (µg/m³)"
AQ_COL_PM10 = "PM10 max (µg/m³)"
AQ_COL_OZONE = "Ozone max (µg/m³)"
AQ_COL_US_AQI = "US AQI (max)"


def _aggregate_air_quality_hourly_to_daily(payload: dict) -> dict[str, dict[str, float]]:
    """Map calendar date (YYYY-MM-DD) -> daily maximum per pollutant."""
    hourly = payload.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        return {}

    vars_track = ["pm2_5", "pm10", "ozone", "us_aqi"]
    daily: dict[str, dict[str, float]] = {}

    for var in vars_track:
        series = hourly.get(var)
        if series is None:
            continue
        for t_str, val in zip(times, series):
            if val is None:
                continue
            day_key = t_str[:10]
            bucket = daily.setdefault(day_key, {})
            prev = bucket.get(var)
            if prev is None or float(val) > prev:
                bucket[var] = float(val)

    return daily


def merge_air_quality_into_forecast(df: pd.DataFrame, latitude: float, longitude: float) -> tuple[pd.DataFrame, bool]:
    """Attach daily-max air quality columns aligned by ISO date. Returns (df, ok)."""
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

    daily_maps = _aggregate_air_quality_hourly_to_daily(payload)
    if not daily_maps:
        return out, False

    if "ISO date" not in out.columns:
        return out, False

    out[AQ_COL_PM25] = math.nan
    out[AQ_COL_PM10] = math.nan
    out[AQ_COL_OZONE] = math.nan
    out[AQ_COL_US_AQI] = math.nan

    for idx in range(len(out)):
        dk = str(out.iloc[idx]["ISO date"])[:10]
        dm = daily_maps.get(dk)
        if not dm:
            continue
        if "pm2_5" in dm:
            out.loc[out.index[idx], AQ_COL_PM25] = round(dm["pm2_5"], 1)
        if "pm10" in dm:
            out.loc[out.index[idx], AQ_COL_PM10] = round(dm["pm10"], 1)
        if "ozone" in dm:
            out.loc[out.index[idx], AQ_COL_OZONE] = round(dm["ozone"], 1)
        if "us_aqi" in dm:
            out.loc[out.index[idx], AQ_COL_US_AQI] = round(dm["us_aqi"], 1)

    out = out.drop(columns=["ISO date"], errors="ignore")
    return out, True


def get_live_weather(city_name: str) -> pd.DataFrame:
    q = normalize_city_name((city_name or "").strip() or FALLBACK_CITY)
    if len(q) < 2:
        q = FALLBACK_CITY
    location = geocode_city(q)
    return fetch_forecast(location["latitude"], location["longitude"])


def format_location(location: dict) -> str:
    country = location.get("country", "")
    name = location["display_name"]
    return f"{name}, {country}" if country else name


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

    amap_key = (os.environ.get("AMAP_API_KEY") or "").strip()
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


def risk_level(score: float) -> str:
    if score < 30:
        return "Low"
    if score < 55:
        return "Moderate"
    if score < 75:
        return "High"
    return "Extreme"


def calculate_risk_score(
    max_temp: float,
    humidity: int,
    school_type: str,
    outdoor_activity: bool,
    us_aqi: float | None = None,
) -> float:
    temp_component = max(0, (max_temp - 28) * 4)
    humidity_component = max(0, (humidity - 60) * 0.5)
    score = (temp_component + humidity_component) * SCHOOL_TYPE_FACTOR[school_type]
    if outdoor_activity:
        score *= 1.12
    if us_aqi is not None and us_aqi >= 100:
        score += 10
    return round(min(100, score), 1)


def inject_theme_css() -> None:
    st.markdown(
        """
        <style>
        .block-container { padding-top: 1.25rem; padding-bottom: 2rem; }
        .hero {
            background: linear-gradient(135deg, #E8F4FC 0%, #FDF8F0 100%);
            border-radius: 12px;
            padding: 1.5rem 1.75rem;
            border-left: 5px solid #009EDC;
            margin-bottom: 1.25rem;
        }
        .hero h1 { margin: 0 0 0.35rem 0; font-size: 1.85rem; color: #1A3A52; }
        .hero .zh { margin: 0 0 0.5rem 0; font-size: 1.05rem; color: #37474F; }
        .hero .en { margin: 0; color: #546E7A; font-size: 0.95rem; line-height: 1.5; }
        .section-title {
            font-size: 1.15rem; font-weight: 600; color: #1A3A52;
            margin: 1.5rem 0 0.75rem 0;
        }
        .context-bar {
            background: #F7FAFC; border-radius: 8px; padding: 0.75rem 1rem;
            border: 1px solid #E3EDF3; color: #455A64; font-size: 0.9rem;
            margin-bottom: 1rem;
        }
        .metric-card {
            background: #FFFFFF; border-radius: 10px; padding: 1rem 1.1rem;
            border: 1px solid #E6EEF3; min-height: 108px;
            box-shadow: 0 1px 2px rgba(26, 58, 82, 0.06);
        }
        .metric-card .label {
            font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.04em;
            color: #78909C; margin: 0 0 0.35rem 0;
        }
        .metric-card .value { font-size: 1.45rem; font-weight: 600; color: #1A3A52; margin: 0; }
        .metric-card .sub { font-size: 0.82rem; color: #607D8B; margin: 0.25rem 0 0 0; }
        .metric-card .metric-icon { font-size: 1.25rem; margin: 0 0 0.25rem 0; }
        .guide-card {
            background: #FFFFFF; border-radius: 10px; padding: 1.1rem 1.2rem;
            border: 1px solid #E6EEF3; height: 100%;
        }
        .guide-card h4 { margin: 0 0 0.5rem 0; color: #1A3A52; font-size: 1rem; }
        .guide-card p { margin: 0; color: #546E7A; font-size: 0.9rem; line-height: 1.55; }
        .disclaimer {
            background: #F5F7F8; border-radius: 8px; padding: 0.9rem 1rem;
            border-left: 4px solid #90A4AE; color: #546E7A;
            font-size: 0.85rem; line-height: 1.5; margin-top: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(title: str, value: str, icon: str, sub: str = "", accent: str = "#009EDC") -> None:
    sub_html = f'<p class="sub">{sub}</p>' if sub else ""
    st.markdown(
        f"""
        <div class="metric-card" style="border-top: 3px solid {accent};">
            <p class="metric-icon">{icon}</p>
            <p class="label">{title}</p>
            <p class="value">{value}</p>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_guide_card(title: str, icon: str, body: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="guide-card" style="border-left: 4px solid {accent};">
            <h4>{icon} {title}</h4>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_risk_legend(lang: str) -> None:
    chips = "".join(
        f'<span style="display:inline-block;margin:0 8px 6px 0;padding:4px 10px;'
        f'border-radius:6px;background:{bg};color:{fg};font-size:0.78rem;">{label}</span>'
        for label, fg, bg in RISK_LEGEND_CHIPS[lang]
    )
    prefix = STRINGS[lang]["risk_scale"]
    st.markdown(
        f'<p style="font-size:0.85rem;color:#607D8B;margin:0 0 1rem 0;">{prefix} {chips}</p>',
        unsafe_allow_html=True,
    )


def build_forecast_chart(forecast: pd.DataFrame, lang: str) -> go.Figure:
    T = STRINGS[lang]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=forecast["Day"],
            y=forecast["Max Temp (°C)"],
            name=T["chart_legend_max_temp"],
            mode="lines+markers",
            line=dict(color="#009EDC", width=2.5),
            marker=dict(size=7, color="#009EDC"),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["Day"],
            y=forecast["Humidity (%)"],
            name=T["chart_legend_hum"],
            mode="lines+markers",
            line=dict(color="#7CB9A8", width=2, dash="dot"),
            marker=dict(size=6, color="#7CB9A8"),
        ),
        secondary_y=True,
    )
    fig.update_layout(
        height=340,
        margin=dict(l=24, r=24, t=48, b=48),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        plot_bgcolor="#FAFCFD",
        paper_bgcolor="#FFFFFF",
        font=dict(family="Segoe UI, Arial, sans-serif", size=12, color="#455A64"),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#EEF2F5", title="")
    fig.update_yaxes(
        title_text=T["chart_y_temp"],
        secondary_y=False,
        showgrid=True,
        gridcolor="#EEF2F5",
        rangemode="tozero",
    )
    fig.update_yaxes(
        title_text=T["chart_y_hum"],
        secondary_y=True,
        showgrid=False,
        rangemode="tozero",
    )
    return fig


# Rule-based guidance per language: base text + optional weather/activity add-ons.
GUIDANCE_BASE = {
    "en": {
        "Teachers": {
            "Low": (
                "Level 1 (Low): Usual outdoor classes and recess are fine. "
                "Remind students to drink water at breaks and watch for normal tiredness."
            ),
            "Moderate": (
                "Level 2 (Moderate): Shorten high-intensity games and add shade breaks every 25–30 minutes. "
                "Keep drinking water visible in the classroom before afternoon sessions."
            ),
            "High": (
                "Level 3 (High): Move PE and assemblies to shaded or indoor areas where possible. "
                "Schedule a hydration pause every 20 minutes and reduce running drills."
            ),
            "Extreme": (
                "Level 4 (Extreme): Postpone or cancel outdoor PE, sports day, and long assemblies. "
                "Keep children in cool indoor spaces and check on them during transitions."
            ),
        },
        "Parents": {
            "Low": (
                "Level 1 (Low): Send your child with a full water bottle and breathable clothing. "
                "Normal school routines are appropriate for today's conditions."
            ),
            "Moderate": (
                "Level 2 (Moderate): Pack extra water and a light hat. "
                "Ask your child to drink before leaving home and again when they return."
            ),
            "High": (
                "Level 3 (High): Choose loose, light-coloured clothes and two water bottles if possible. "
                "Avoid extra outdoor play right after school; offer a cool drink and rest indoors."
            ),
            "Extreme": (
                "Level 4 (Extreme): Limit time outdoors before and after school during peak heat. "
                "Ensure your child rests in a cool place and drinks water regularly through the day."
            ),
        },
        "School Nurses": {
            "Low": (
                "Level 1 (Low): Confirm drinking water is available in corridors and playgrounds. "
                "Share routine heat-awareness tips with staff—no escalation needed today."
            ),
            "Moderate": (
                "Level 2 (Moderate): Brief teachers on early signs of heat discomfort (flushing, headache, thirst). "
                "Stock oral rehydration and rest space for any student who feels unwell."
            ),
            "High": (
                "Level 3 (High): Increase visibility during recess; note students who sit out or appear sluggish. "
                "Prepare a cool rest area, fluids, and contact protocol if a child does not recover quickly."
            ),
            "Extreme": (
                "Level 4 (Extreme): Activate your school heat-response checklist and coordinate with leadership. "
                "Monitor high-risk students closely and support staff with clear rest-and-hydration rules."
            ),
        },
    },
    "zh": {
        "Teachers": {
            "Low": (
                "一级（低）：可按常规安排室外课与课间活动。"
                "提醒学生在休息时补水，留意一般性疲倦即可。"
            ),
            "Moderate": (
                "二级（中等）：缩短剧烈运动时间，每25–30分钟安排阴凉处休息。"
                "下午课前确保教室内有饮用水提示。"
            ),
            "High": (
                "三级（高）：尽量将体育课与集会安排在树荫或室内。"
                "每20分钟安排补水停顿，减少长跑类训练。"
            ),
            "Extreme": (
                "四级（极高）：推迟或取消室外体育课、运动会及长时间集会。"
                "让学生留在凉爽室内，走廊切换时多加照看。"
            ),
        },
        "Parents": {
            "Low": (
                "一级（低）：为孩子准备装满水的杯子与透气衣物。"
                "今日可按正常作息到校。"
            ),
            "Moderate": (
                "二级（中等）：多备一瓶水并携带轻便遮阳帽。"
                "出门前与放学后提醒孩子补水。"
            ),
            "High": (
                "三级（高）：尽量选择宽松浅色衣物，条件允许可备两瓶水。"
                "放学后避免额外户外活动，回家后及时补水并在阴凉处休息。"
            ),
            "Extreme": (
                "四级（极高）：早晚高峰尽量少在烈日下停留。"
                "确保孩子有凉爽休息环境并全日规律饮水。"
            ),
        },
        "School Nurses": {
            "Low": (
                "一级（低）：确认走廊与操场饮水点可用。"
                "向教职工简单提示防暑常识即可。"
            ),
            "Moderate": (
                "二级（中等）：向教师强调早期不适迹象（面红、头痛、口渴）。"
                "备好口服补液与临时休息区域。"
            ),
            "High": (
                "三级（高）：课间加强巡查，留意久坐旁观或精神不振的学生。"
                "准备凉爽休息区、饮水及家长联络流程。"
            ),
            "Extreme": (
                "四级（极高）：启动校园高温应对清单并与校方协同。"
                "重点关注体弱学生，协助落实明确的休息与补水规则。"
            ),
        },
    },
}

GUIDANCE_ADDONS = {
    "en": {
        "high_uv": {
            "Teachers": "UV is very high: plan activities before 10 a.m. or after 4 p.m., require hats, and use shaded areas.",
            "Parents": "UV is very high: apply sunscreen, send a wide-brim hat, and avoid long sun exposure after school.",
            "School Nurses": "UV is very high: remind staff about sun protection and watch for sun-related discomfort on exposed skin.",
        },
        "high_humidity": {
            "Teachers": "Humidity is elevated: heat feels stronger—slow active games and allow more recovery time in shade.",
            "Parents": "Humidity is elevated: encourage frequent small sips of water; sweaty clothes dry more slowly today.",
            "School Nurses": "Humidity is elevated: heat plus moisture increases strain—prioritize cooling breaks and fluids.",
        },
        "outdoor_planned": {
            "Teachers": "Outdoor activity is scheduled: assign a hydration leader, cap session length, and keep shade and water nearby.",
            "Parents": "Outdoor activity is scheduled: send extra water and confirm the school has shade or adjusted timing.",
            "School Nurses": "Outdoor activity is scheduled: be available during the session and review the plan for heat-related stops.",
        },
        "very_hot": {
            "Teachers": "Temperature is high: avoid strenuous drills and watch for students who stop participating or look unwell.",
            "Parents": "Temperature is high: a light meal and water before school help; check in on how your child feels at pickup.",
            "School Nurses": "Temperature is high: treat heat discomfort seriously—move the child to cool space and notify guardians if needed.",
        },
    },
    "zh": {
        "high_uv": {
            "Teachers": "紫外线很强：尽量安排在上午10点前或下午4点后活动，要求学生戴帽并优先使用阴凉处。",
            "Parents": "紫外线很强：涂抹防晒霜、准备宽檐帽，放学后避免长时间暴晒。",
            "School Nurses": "紫外线很强：提醒教职工防晒措施，留意暴露皮肤的晒伤不适迹象（非诊断）。",
        },
        "high_humidity": {
            "Teachers": "湿度偏高：体感更闷热，放慢对抗类游戏并在阴凉处增加恢复时间。",
            "Parents": "湿度偏高：鼓励孩子少量多次饮水；衣物不易干透，可多备一件替换上衣。",
            "School Nurses": "湿度偏高：闷热叠加潮湿更易不适，优先安排降温补水休息。",
        },
        "outdoor_planned": {
            "Teachers": "今日安排户外活动：指定补水负责人，控制单次时长，就近备好阴凉与饮用水。",
            "Parents": "今日安排户外活动：多带水并与学校确认是否有遮阳或错峰安排。",
            "School Nurses": "今日安排户外活动：活动期间保持联络，预先约定出现不适时的暂停与处置流程。",
        },
        "very_hot": {
            "Teachers": "气温偏高：避免高强度操练，留意退出活动或面色异常的学生。",
            "Parents": "气温偏高：早餐清淡并适量饮水；放学时问问孩子有无头晕乏力等不适（非诊断）。",
            "School Nurses": "气温偏高：出现明显不适应尽快转移至阴凉处补水并视情况联系家长（不提供诊断）。",
        },
    },
}


def _uv_numeric(uv_index) -> float | None:
    if uv_index is None or (isinstance(uv_index, float) and pd.isna(uv_index)):
        return None
    return float(uv_index)


def generate_guidance(
    role: str,
    risk: str,
    temperature: float,
    humidity: int,
    uv_index,
    outdoor_activity: bool,
    lang: str,
) -> str:
    """Build explainable, rule-based guidance from risk level and weather flags."""
    base = GUIDANCE_BASE[lang][role][risk]
    addons = GUIDANCE_ADDONS[lang]
    parts = [base]

    uv = _uv_numeric(uv_index)
    if uv is not None and uv > 8:
        parts.append(addons["high_uv"][role])
    if humidity > 70:
        parts.append(addons["high_humidity"][role])
    if outdoor_activity:
        parts.append(addons["outdoor_planned"][role])
    if temperature >= 35:
        parts.append(addons["very_hot"][role])

    return " ".join(parts)


def generate_ai_guidance(context: dict, lang: str) -> dict[str, str]:
    """Call DeepSeek Chat Completions (OpenAI-compatible). Returns guidance per role."""
    api_key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is not set")

    if lang == "zh":
        system = (
            "你是 HeatSafe Campus 校园防暑原型项目的助手。"
            "请用简体中文撰写简明、可操作、以儿童安全为导向的建议。"
            "不进行医学诊断，不提供治疗方案。"
            "仅输出合法 JSON，不要使用 markdown 代码块或其他多余文字。"
        )
        lang_instr = (
            "所有字符串值必须为简体中文；每条建议约 2–4 句。"
            'JSON 键名必须为英文："Teachers", "Parents", "School Nurses"。'
        )
    else:
        system = (
            "You help schools plan for heat in a prototype called HeatSafe Campus. "
            "Write concise, practical, child-safety-focused advice in English. "
            "Do not diagnose medical conditions or give clinical treatment instructions. "
            "Respond with valid JSON only—no markdown fences or extra text."
        )
        lang_instr = (
            "Each string value must be English (2–4 short sentences). "
            'JSON keys must be exactly: "Teachers", "Parents", "School Nurses".'
        )

    user_payload = (
        "Using the following context, produce role-specific guidance.\n\n"
        f"Context:\n{json.dumps(context, indent=2)}\n\n"
        f"{lang_instr}\n"
        "Tailor tone to teachers, parents, and school nurses respectively. "
        "Reference numbers from context when helpful."
    )

    response = requests.post(
        DEEPSEEK_CHAT_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_payload},
            ],
            "temperature": 0.35,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    parsed = json.loads(content)
    return {
        "Teachers": str(parsed["Teachers"]).strip(),
        "Parents": str(parsed["Parents"]).strip(),
        "School Nurses": str(parsed["School Nurses"]).strip(),
    }


def format_uv(uv_value, _lang: str = "en") -> str:
    dash = "—"
    if uv_value is None or (isinstance(uv_value, float) and pd.isna(uv_value)):
        return dash
    return f"{float(uv_value):.1f}"


def format_air_metric(value) -> str:
    dash = "—"
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return dash
    try:
        x = float(value)
    except (TypeError, ValueError):
        return dash
    if abs(x - round(x)) < 1e-6:
        return str(int(round(x)))
    return f"{x:.1f}"


def optional_float(cell) -> float | None:
    if cell is None or (isinstance(cell, float) and pd.isna(cell)):
        return None
    try:
        return float(cell)
    except (TypeError, ValueError):
        return None


def render_school_location_map(
    lang: str,
    amap_ok: bool,
    location: dict,
    school_label: str,
    formatted_address: str | None,
) -> None:
    """Folium map centered on Amap coordinates; info message if unavailable."""
    T = STRINGS[lang]
    st.markdown(f'<p class="section-title">{T["sec_map"]}</p>', unsafe_allow_html=True)
    if not amap_ok:
        st.info(T["map_unavailable"])
        return

    lat = location.get("latitude")
    lon = location.get("longitude")
    if lat is None or lon is None:
        st.info(T["map_unavailable"])
        return

    addr = (formatted_address or "").strip() or format_location(location)
    popup_html = (
        "<div style='min-width:160px;'>"
        f"<b>{html.escape(school_label)}</b><br>"
        f"{html.escape(addr)}"
        "</div>"
    )
    fmap = folium.Map(location=[float(lat), float(lon)], zoom_start=15, tiles="OpenStreetMap")
    folium.Marker(
        location=[float(lat), float(lon)],
        tooltip=school_label,
        popup=folium.Popup(popup_html, max_width=320),
    ).add_to(fmap)
    st_folium(fmap, height=380, use_container_width=True)


st.set_page_config(
    page_title="热浪安全校园 | HeatSafe Campus",
    page_icon="🌤️",
    layout="wide",
)

inject_theme_css()

with st.sidebar:
    lang_label = st.selectbox(
        "Language / 语言",
        options=["中文", "English"],
        index=0,
    )
    lang = LANG_FROM_LABEL[lang_label]
    T = STRINGS[lang]

    st.markdown(T["sidebar_header"])
    st.caption(T["sidebar_caption"])
    school_name = st.text_input(T["school_name"], placeholder=T["school_ph"])
    city = st.text_input(T["city_name"], value="Beijing", placeholder=T["city_ph"])
    st.caption(
        "中文界面支持中文城市名，例如：北京、上海、广州。\n"
        "English city names are also supported."
    )
    school_options = [(SCHOOL_TYPE_LABELS[lang][s], s) for s in SCHOOL_TYPES]
    school_labels = [o[0] for o in school_options]
    chosen_label = st.selectbox(T["school_type"], school_labels)
    school_type = next(val for lab, val in school_options if lab == chosen_label)
    outdoor_activity = st.checkbox(T["outdoor"])
    use_ai_guidance = st.checkbox(T["use_ai"], value=False)
    st.markdown("---")
    st.markdown(T["tip_climate"])
    st.markdown(T["tip_school"])
    st.markdown(T["tip_safety"])

hero_html = f"""
    <div class="hero">
        <h1>{T["hero_title"]}</h1>
        <p class="zh">{T["hero_sub"]}</p>
        <p class="en">{T["hero_desc"]}</p>
    </div>
    """
st.markdown(hero_html, unsafe_allow_html=True)

forecast, using_live, location, geocode_failed, location_meta = load_forecast(
    city, school_name
)
forecast, air_quality_ok = merge_air_quality_into_forecast(
    forecast, location["latitude"], location["longitude"]
)

if geocode_failed:
    st.warning(T["warn_city"])
if location_meta.get("amap_ok"):
    st.success(T["ok_amap"])
    if location_meta.get("formatted_address"):
        st.caption(f"{T['amap_addr_prefix']} {location_meta['formatted_address']}")
elif location_meta.get("amap_fail"):
    st.warning(T["warn_amap_fallback"])
if using_live:
    st.success(T["ok_live"])
elif not geocode_failed:
    st.warning(T["warn_mock"])
if not air_quality_ok:
    st.warning(T["warn_aq"])

display_school = school_name.strip() or T["placeholder_school"]

render_school_location_map(
    lang,
    location_meta.get("amap_ok", False),
    location,
    display_school,
    location_meta.get("formatted_address"),
)

city_disp = (location_meta.get("city_display") or "").strip()
loc_fmt = format_location(location)
if city_disp and normalize_city_name(city_disp) != city_disp:
    location_label = f"{city_disp} · {loc_fmt}"
else:
    location_label = loc_fmt
today = forecast.iloc[0]
max_temp = today["Max Temp (°C)"]
humidity = int(today["Humidity (%)"])
today_uv = today.get("UV Index")
apparent_max = today.get("Apparent temp (°C)")
today_us_aqi = optional_float(today.get(AQ_COL_US_AQI))
today_pm25 = optional_float(today.get(AQ_COL_PM25))
risk_score = calculate_risk_score(
    max_temp, humidity, school_type, outdoor_activity, us_aqi=today_us_aqi
)
today_risk = risk_level(risk_score)
risk_style = RISK_STYLES[today_risk]

data_live_key = "ctx_live" if using_live else "ctx_demo"
data_source = T[data_live_key]
activity_note = T["ctx_outdoor"] if outdoor_activity else ""

st.markdown(
    f"""
    <div class="context-bar">
        🏫 <strong>{display_school}</strong> &nbsp;·&nbsp;
        📍 {location_label} &nbsp;·&nbsp;
        {SCHOOL_TYPE_LABELS[lang][school_type]} &nbsp;·&nbsp;
        {T["ctx_data"]}: {data_source}{activity_note}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(f'<p class="section-title">{T["sec_dash"]}</p>', unsafe_allow_html=True)
render_risk_legend(lang)

risk_label_long = RISK_LEVEL_LONG[lang][today_risk]
risk_sub = f"{risk_label_long} · {T['metric_score']} {risk_score}/100"

m1, m2, m3, m4, m5, m6 = st.columns(6)
with m1:
    render_metric_card(
        T["metric_risk"],
        RISK_SHORT[lang][today_risk],
        "⚠️",
        risk_sub,
        risk_style["color"],
    )
with m2:
    render_metric_card(T["metric_temp"], f"{max_temp} °C", "🌡️", T["metric_temp_sub"], "#009EDC")
with m3:
    render_metric_card(T["metric_hum"], f"{humidity}%", "💧", T["metric_hum_sub"], "#5C9EAD")
with m4:
    render_metric_card(T["metric_uv"], format_uv(today_uv, lang), "☀️", T["metric_uv_sub"], "#F4A261")
with m5:
    render_metric_card(
        T["metric_aqi"],
        format_air_metric(today.get(AQ_COL_US_AQI)),
        "🌫️",
        T["metric_aqi_sub"],
        "#6B5B95",
    )
with m6:
    render_metric_card(
        T["metric_pm25"],
        format_air_metric(today.get(AQ_COL_PM25)),
        "😷",
        T["metric_pm25_sub"],
        "#8E7CC3",
    )

st.markdown(f'<p class="section-title">{T["sec_chart"]}</p>', unsafe_allow_html=True)
forecast_kind = T["chart_live"] if using_live else T["chart_mock"]
st.caption(f'{T["chart_cap"]} {forecast_kind}')
st.plotly_chart(build_forecast_chart(forecast, lang), width="stretch")

with st.expander(T["exp_table"]):
    st.dataframe(localize_forecast_display(forecast, lang), width="stretch", hide_index=True)

st.markdown(f'<p class="section-title">{T["sec_guide"]}</p>', unsafe_allow_html=True)

guidance_context = {
    "school_name": display_school,
    "city": location_label,
    "school_type": school_type,
    "outdoor_activity_planned": bool(outdoor_activity),
    "today_max_temperature_c": float(max_temp),
    "today_apparent_temperature_max_c": (
        float(apparent_max)
        if apparent_max is not None
        and not (isinstance(apparent_max, float) and pd.isna(apparent_max))
        else None
    ),
    "humidity_percent": int(humidity),
    "uv_index": _uv_numeric(today_uv),
    "risk_score": float(risk_score),
    "risk_level": today_risk,
    "language": "Chinese" if lang == "zh" else "English",
    "us_aqi_daily_max": today_us_aqi,
    "pm25_daily_max_ug_m3": today_pm25,
    "geocoding_source": location.get("source", ""),
}

guidance_teachers = generate_guidance(
    "Teachers", today_risk, max_temp, humidity, today_uv, outdoor_activity, lang
)
guidance_parents = generate_guidance(
    "Parents", today_risk, max_temp, humidity, today_uv, outdoor_activity, lang
)
guidance_nurses = generate_guidance(
    "School Nurses", today_risk, max_temp, humidity, today_uv, outdoor_activity, lang
)

if use_ai_guidance:
    if not (os.environ.get("DEEPSEEK_API_KEY") or "").strip():
        st.warning(T["warn_no_key"])
    else:
        try:
            ai_out = generate_ai_guidance(guidance_context, lang)
            guidance_teachers = ai_out["Teachers"]
            guidance_parents = ai_out["Parents"]
            guidance_nurses = ai_out["School Nurses"]
            st.caption(T["cap_ai_ok"])
        except Exception as exc:
            detail = str(exc)
            if isinstance(exc, requests.HTTPError) and exc.response is not None:
                try:
                    body = exc.response.text.strip()
                    if body:
                        snippet = body[:800] + ("…" if len(body) > 800 else "")
                        detail = f"{detail}\n\nResponse:\n{snippet}"
                except Exception:
                    pass
            st.warning(f"{T['warn_ai_fail']}\n\n**Debug ({type(exc).__name__}):** {detail}")
            st.caption(T["cap_rules"])
else:
    st.caption(T["cap_rules"])

g1, g2, g3 = st.columns(3)
with g1:
    render_guide_card(
        T["role_teachers"],
        "👩‍🏫",
        guidance_teachers,
        "#009EDC",
    )
with g2:
    render_guide_card(
        T["role_parents"],
        "👨‍👩‍👧",
        guidance_parents,
        "#7CB9A8",
    )
with g3:
    render_guide_card(
        T["role_nurses"],
        "🏥",
        guidance_nurses,
        "#E76F51",
    )

st.markdown(
    f"""
    <div class="disclaimer">
        {T["disclaimer"]}
    </div>
    """,
    unsafe_allow_html=True,
)
