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
import streamlit.components.v1 as components
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
        "insufficient_shade": "校园遮阳不足",
        "insufficient_water": "饮水设施不足",
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
        "risk_factors_title": "风险得分因素说明",
        "risk_factors_body": (
            "得分由下列因素**累加**（上限 100 分），评分使用**日最高气温**、**相对湿度**、"
            "**体感温度（热指数代理）**及 **US AQI**（不含紫外线、PM2.5）：\n\n"
            "- 日最高气温 ≥ 35°C：+20\n"
            "- 日最高气温 ≥ 38°C：+35\n"
            "- 相对湿度 ≥ 65%：+15\n"
            "- 体感温度（热指数代理）≥ 40°C：+25\n"
            "- US AQI ≥ 100：+10\n"
            "- 今日计划户外活动：+15\n"
            "- 幼儿园或小学学段：+10\n"
            "- 校园遮阳不足：+10\n"
            "- 饮水设施不足：+10"
        ),
        "metric_risk": "风险等级",
        "metric_temp": "白天平均气温（10:00–16:00）",
        "metric_hum": "白天平均湿度（10:00–16:00）",
        "metric_uv": "白天平均紫外线指数（10:00–16:00）",
        "metric_temp_sub": "日最高气温（参考）",
        "metric_hum_sub": "日最高相对湿度（参考）",
        "metric_uv_sub": "日紫外线峰值（参考）",
        "metric_aqi": "US AQI",
        "metric_pm25": "白天平均 PM2.5（10:00–16:00）",
        "metric_aqi_sub": "白天平均 US AQI（10:00–16:00）",
        "metric_pm25_sub": "日最大 PM2.5（参考，µg/m³）",
        "daytime_exposure_note": (
            "本系统优先使用 10:00–16:00 白天时段平均值，以更贴近学校户外活动和上下学时段的儿童暴露风险。"
        ),
        "metric_score": "得分",
        "sec_chart": "📈 七日天气趋势",
        "chart_cap": "气温与湿度展望 ·",
        "chart_live": "实时",
        "chart_mock": "模拟",
        "exp_table": "📋 查看七日预报明细表",
        "sec_guide": "👧 分角色儿童安全建议",
        "sec_parent_notice": "📢 家校通知一键生成",
        "parent_notice_label": "通知正文",
        "copy_notice": "复制通知",
        "copy_notice_ok": "已复制到剪贴板，可直接粘贴至家长群。",
        "notice_disclaimer": "本通知仅用于学校健康提醒参考，不构成医疗建议。",
        "sec_student_ai": "🧒 学生高温健康 AI 助手",
        "student_age": "学生年龄",
        "student_outdoor": "今日是否有户外活动",
        "student_symptoms": "不适症状（可多选）",
        "student_notes": "补充说明（选填）",
        "student_notes_ph": "例如：体育课时间较长、午休出汗较多等",
        "student_generate": "生成健康建议",
        "student_disclaimer": "本功能仅用于高温健康教育与风险提醒，不构成医疗诊断。",
        "student_ai_ok": "由 DeepSeek 生成的健康教育建议（非诊断）。",
        "student_rules_ok": "规则模板建议（DeepSeek 不可用或请求失败时）。",
        "yes": "是",
        "no": "否",
        "cap_ai_ok": "基于今日上下文由 DeepSeek 生成的建议。关闭 AI 或请求失败时使用规则模板。",
        "cap_rules": "基于今日风险等级、10:00–16:00 白天平均气温/湿度/紫外线/空气质量（若可用）与活动安排的规则建议。",
        "role_teachers": "教师",
        "role_parents": "家长",
        "role_nurses": "校医",
        "placeholder_school": "您的学校",
        "disclaimer": (
            "<strong>免责声明：</strong>本工具仅提供预警与健康教育支持，不提供医学诊断。"
        ),
        "chart_legend_daytime_temp": "白天平均气温（10:00–16:00）",
        "chart_legend_daytime_hum": "白天平均湿度（10:00–16:00）",
        "chart_y_temp": "白天平均气温 (°C)",
        "chart_y_hum": "白天平均湿度 (%)",
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
        "insufficient_shade": "Insufficient campus shade",
        "insufficient_water": "Insufficient drinking water facilities",
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
        "risk_factors_title": "How the risk score is calculated",
        "risk_factors_body": (
            "Points **add up** (cap 100). Scoring uses **daily max temperature**, **humidity**, "
            "**apparent temperature (heat-index proxy)**, and **US AQI** (UV and PM2.5 are excluded):\n\n"
            "- Max temperature ≥ 35°C: +20\n"
            "- Max temperature ≥ 38°C: +35\n"
            "- Humidity ≥ 65%: +15\n"
            "- Apparent temperature (heat-index proxy) ≥ 40°C: +25\n"
            "- US AQI ≥ 100: +10\n"
            "- Outdoor PE / outdoor activity planned: +15\n"
            "- Kindergarten or primary school: +10\n"
            "- Insufficient campus shade: +10\n"
            "- Insufficient drinking water facilities: +10"
        ),
        "metric_risk": "Risk level",
        "metric_temp": "Daytime Avg Temp (10:00–16:00)",
        "metric_hum": "Daytime Avg Humidity (10:00–16:00)",
        "metric_uv": "Daytime Avg UV Index (10:00–16:00)",
        "metric_temp_sub": "Daily max (reference)",
        "metric_hum_sub": "Daily max humidity (reference)",
        "metric_uv_sub": "Daily peak UV (reference)",
        "metric_aqi": "US AQI",
        "metric_pm25": "Daytime Avg PM2.5 (10:00–16:00)",
        "metric_aqi_sub": "Daytime avg US AQI (10:00–16:00)",
        "metric_pm25_sub": "Daily max PM2.5 (reference, µg/m³)",
        "daytime_exposure_note": (
            "This prototype prioritizes 10:00–16:00 daytime averages to better reflect "
            "children’s exposure during school activity and commuting hours."
        ),
        "metric_score": "Score",
        "sec_chart": "📈 7-day weather trend",
        "chart_cap": "Temperature and humidity outlook ·",
        "chart_live": "live data",
        "chart_mock": "mock data",
        "exp_table": "📋 View detailed 7-day forecast table",
        "sec_guide": "👧 Role-specific guidance for child safety",
        "sec_parent_notice": "📢 Parent Notice Generator",
        "parent_notice_label": "Notice text",
        "copy_notice": "Copy Notice",
        "copy_notice_ok": "Copied to clipboard — paste into your parent group or messaging app.",
        "notice_disclaimer": (
            "This notice is for school health awareness only and does not constitute medical advice."
        ),
        "sec_student_ai": "🧒 Student Heat-Health AI Assistant",
        "student_age": "Student age",
        "student_outdoor": "Outdoor activity today",
        "student_symptoms": "Symptoms (select any that apply)",
        "student_notes": "Additional notes (optional)",
        "student_notes_ph": "e.g. long PE session, heavy sweating at lunch",
        "student_generate": "Generate Guidance",
        "student_disclaimer": (
            "This feature is for heat-health awareness only and does not provide medical diagnosis."
        ),
        "student_ai_ok": "Educational guidance from DeepSeek (not a diagnosis).",
        "student_rules_ok": "Rule-based guidance (DeepSeek unavailable or request failed).",
        "yes": "Yes",
        "no": "No",
        "cap_ai_ok": "AI-generated guidance (DeepSeek) from today's context. "
        "Rule-based templates apply if AI is off or unavailable.",
        "cap_rules": "Rule-based actions from today's risk level, 10:00–16:00 daytime-average "
        "temperature, humidity, UV, air quality (when available), and activity plan.",
        "role_teachers": "Teachers",
        "role_parents": "Parents",
        "role_nurses": "School Nurses",
        "placeholder_school": "Your school",
        "disclaimer": (
            "<strong>Disclaimer:</strong> This tool provides early warning and health education support only. "
            "It does not provide medical diagnosis."
        ),
        "chart_legend_daytime_temp": "Daytime avg temp (10:00–16:00)",
        "chart_legend_daytime_hum": "Daytime avg humidity (10:00–16:00)",
        "chart_y_temp": "Daytime avg temp (°C)",
        "chart_y_hum": "Daytime avg humidity (%)",
        "sec_map": "School Location Map",
        "map_unavailable": "School location map is unavailable. Resolve the school with Amap to view the map.",
    },
}

FORECAST_COLUMN_NAMES = {
    "zh": {
        "Day": "日期",
        "Daytime Avg Temp (°C)": "白天平均气温（10:00–16:00）",
        "Max Temp (°C)": "最高气温 (°C)",
        "Daytime Avg Feels-like (°C)": "白天平均体感温度（10:00–16:00）",
        "Apparent temp (°C)": "体感最高温 (°C)",
        "Daytime Avg Humidity (%)": "白天平均湿度（10:00–16:00）",
        "Humidity (%)": "日最高相对湿度 (%)",
        "Daytime Avg UV Index": "白天平均紫外线指数（10:00–16:00）",
        "UV Index": "紫外线峰值",
        "Conditions": "天气状况",
        "Daytime Avg US AQI": "白天平均 US AQI（10:00–16:00）",
        "US AQI (max)": "US AQI（日最大）",
        "Daytime Avg PM2.5 (µg/m³)": "白天平均 PM2.5（10:00–16:00）",
        "PM2.5 max (µg/m³)": "PM2.5 日最大（µg/m³）",
        "Daytime Avg PM10 (µg/m³)": "白天平均 PM10（10:00–16:00）",
        "PM10 max (µg/m³)": "PM10 日最大（µg/m³）",
        "Daytime Avg Ozone (µg/m³)": "白天平均臭氧（10:00–16:00）",
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


YOUNG_SCHOOL_TYPES = frozenset({"Kindergarten", "Primary School"})


def calculate_risk_score(
    max_temp: float,
    humidity: int,
    apparent_temp: float | None,
    us_aqi: float | None,
    school_type: str,
    outdoor_activity: bool,
    insufficient_shade: bool,
    insufficient_water: bool,
) -> float:
    """HeatSafe Campus MVP additive risk score (0–100). Uses daily max weather metrics."""
    score = 0.0
    if max_temp >= 35:
        score += 20
    if max_temp >= 38:
        score += 35
    if humidity >= 65:
        score += 15
    if apparent_temp is not None and apparent_temp >= 40:
        score += 25
    if us_aqi is not None and us_aqi >= 100:
        score += 10
    if outdoor_activity:
        score += 15
    if school_type in YOUNG_SCHOOL_TYPES:
        score += 10
    if insufficient_shade:
        score += 10
    if insufficient_water:
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
    temp_col = COL_DAYTIME_TEMP if COL_DAYTIME_TEMP in forecast.columns else COL_MAX_TEMP
    hum_col = COL_DAYTIME_HUM if COL_DAYTIME_HUM in forecast.columns else COL_MAX_HUM
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=forecast["Day"],
            y=forecast[temp_col],
            name=T["chart_legend_daytime_temp"],
            mode="lines+markers",
            line=dict(color="#009EDC", width=2.5),
            marker=dict(size=7, color="#009EDC"),
        ),
        secondary_y=False,
    )
    fig.add_trace(
        go.Scatter(
            x=forecast["Day"],
            y=forecast[hum_col],
            name=T["chart_legend_daytime_hum"],
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
    if humidity >= 65:
        parts.append(addons["high_humidity"][role])
    if outdoor_activity:
        parts.append(addons["outdoor_planned"][role])
    if temperature >= 35:
        parts.append(addons["very_hot"][role])

    return " ".join(parts)


PARENT_NOTICE_ACTIONS = {
    "zh": {
        "Low": (
            "目前气候条件总体适宜正常到校与课间活动。请为孩子准备足量温水、透气衣物，"
            "并提醒课间及时补水，关注是否有口渴、疲倦等一般不适表现。"
        ),
        "Moderate": (
            "今日体感偏闷热，请为孩子多备饮水，穿着透气浅色衣物，并佩戴遮阳帽。"
            "建议减少放学后在烈日下的长时间停留，回家后及时补水、在阴凉处休息。"
        ),
        "High": (
            "今日高温风险较高，请家长配合学校合理安排作息：尽量避免高强度户外活动，"
            "关注孩子是否有面红、头痛、恶心、精神不振等情况；如有明显不适，请及时与班主任联系。"
        ),
        "Extreme": (
            "今日高温风险极高，请家长务必重视：减少不必要外出，确保孩子全天规律饮水，"
            "尽量待在凉爽通风环境。如学校调整户外活动或体育课安排，请以班级通知为准，"
            "并随时关注孩子身体状况，有异常及时联系学校。"
        ),
    },
    "en": {
        "Low": (
            "Conditions are generally suitable for normal attendance and recess. "
            "Please send a full water bottle, breathable clothing, and remind your child "
            "to drink regularly and tell an adult if they feel unusually tired or thirsty."
        ),
        "Moderate": (
            "It will feel warm and humid today. Pack extra water, light-coloured clothing, "
            "and a hat. Limit prolonged sun exposure after school and encourage rest in a cool place."
        ),
        "High": (
            "Heat risk is elevated today. Please support the school’s adjusted routines, "
            "avoid strenuous outdoor play when possible, and watch for flushing, headache, "
            "dizziness, or unusual fatigue. Contact the homeroom teacher if your child feels unwell."
        ),
        "Extreme": (
            "Extreme heat risk today. Minimize unnecessary outdoor time, ensure regular hydration, "
            "and keep your child in a cool, ventilated space. Follow any class-level changes to PE "
            "or outdoor events, and contact the school promptly if your child shows significant discomfort."
        ),
    },
}


def _parent_notice_weather_block(
    lang: str,
    max_temp: float,
    apparent_temp: float | None,
    humidity: int,
    us_aqi: float | None,
) -> str:
    if lang == "zh":
        lines = [
            f"· 日最高气温：{max_temp:.1f}℃",
        ]
        if apparent_temp is not None:
            lines.append(f"· 体感温度：{apparent_temp:.1f}℃")
        else:
            lines.append("· 体感温度：暂无")
        lines.append(f"· 相对湿度：{humidity}%")
        if us_aqi is not None:
            lines.append(f"· 空气质量（US AQI）：{int(round(us_aqi))}")
        return "\n".join(lines)

    lines = [
        f"· Forecast max temperature: {max_temp:.1f}°C",
    ]
    if apparent_temp is not None:
        lines.append(f"· Apparent (feels-like) temperature: {apparent_temp:.1f}°C")
    else:
        lines.append("· Apparent (feels-like) temperature: not available")
    lines.append(f"· Relative humidity: {humidity}%")
    if us_aqi is not None:
        lines.append(f"· Air quality (US AQI): {int(round(us_aqi))}")
    return "\n".join(lines)


def _parent_notice_outdoor_line(lang: str, outdoor_activity: bool) -> str:
    if not outdoor_activity:
        return ""
    if lang == "zh":
        return (
            "\n🏃 补充说明：今日学校计划开展户外活动，请为孩子多备饮水，"
            "并留意班级群老师发布的实时安排。\n"
        )
    return (
        "\n🏃 Note: Outdoor activities are scheduled today. "
        "Please send extra water and watch for updates from your child’s teacher.\n"
    )


def generate_parent_notice(
    lang: str,
    school_name: str,
    city: str,
    risk: str,
    max_temp: float,
    apparent_temp: float | None,
    humidity: int,
    us_aqi: float | None,
    outdoor_activity: bool,
) -> str:
    """Build a copy-ready parent-group notice from current heat-health context."""
    risk_label = RISK_LEVEL_LONG[lang][risk]
    weather = _parent_notice_weather_block(lang, max_temp, apparent_temp, humidity, us_aqi)
    outdoor_line = _parent_notice_outdoor_line(lang, outdoor_activity)
    actions = PARENT_NOTICE_ACTIONS[lang][risk]
    today_str = date.today().strftime("%Y年%m月%d日" if lang == "zh" else "%d %B %Y")

    if lang == "zh":
        return (
            f"【{school_name}】家长群通知｜今日儿童高温健康提示\n\n"
            f"各位家长，大家好！👋\n\n"
            f"根据校园高温健康评估，{city} 今日儿童高温健康风险等级为【{risk_label}】。\n\n"
            f"📊 今日气象参考：\n{weather}\n"
            f"{outdoor_line}\n"
            f"✅ 家校协同提示：\n{actions}\n\n"
            f"感谢各位家长配合，共同守护孩子夏季健康！🙏\n\n"
            f"—— {school_name}\n"
            f"{today_str}"
        )

    return (
        f"[{school_name}] Parent notice — child heat-health update\n\n"
        f"Dear parents and guardians,\n\n"
        f"Based on today’s campus heat-health assessment for {city}, "
        f"the child heat-health risk level is **{risk_label}**.\n\n"
        f"Today’s weather reference:\n{weather}\n"
        f"{outdoor_line}\n"
        f"Please support the following:\n{actions}\n\n"
        f"Thank you for partnering with us to keep children safe in hot weather.\n\n"
        f"— {school_name}\n"
        f"{today_str}"
    )


def render_copy_notice_button(label: str, text: str, button_id: str) -> None:
    """Copy notice text to the clipboard (no messaging APIs)."""
    payload = json.dumps(text)
    label_js = json.dumps(label)
    components.html(
        f"""
        <button type="button" id="{button_id}" style="
            padding: 0.5rem 1.15rem; background: #009EDC; color: white; border: none;
            border-radius: 8px; cursor: pointer; font-size: 0.92rem; font-family: inherit;">
            {html.escape(label)}
        </button>
        <script>
        (function() {{
            var btn = document.getElementById("{button_id}");
            var txt = {payload};
            var defaultLabel = {label_js};
            btn.onclick = function() {{
                navigator.clipboard.writeText(txt).then(function() {{
                    btn.innerText = "✓ " + defaultLabel;
                    setTimeout(function() {{ btn.innerText = defaultLabel; }}, 2200);
                }}).catch(function() {{}});
            }};
        }})();
        </script>
        """,
        height=52,
    )


STUDENT_SYMPTOM_KEYS = (
    "dizziness",
    "fatigue",
    "headache",
    "nausea",
    "excessive_sweating",
)

STUDENT_SYMPTOM_LABELS = {
    "zh": {
        "dizziness": "头晕",
        "fatigue": "乏力 / 疲倦",
        "headache": "头痛",
        "nausea": "恶心",
        "excessive_sweating": "出汗过多",
    },
    "en": {
        "dizziness": "Dizziness",
        "fatigue": "Fatigue",
        "headache": "Headache",
        "nausea": "Nausea",
        "excessive_sweating": "Excessive sweating",
    },
}


def generate_student_health_guidance_rules(context: dict, lang: str) -> str:
    """Rule-based child heat-health suggestions (non-diagnostic)."""
    symptoms = context.get("symptoms") or []
    age = int(context.get("student_age", 8))
    outdoor = bool(context.get("outdoor_activity_today"))
    risk = context.get("campus_risk_level", "Low")
    notes = (context.get("notes") or "").strip()
    max_t = context.get("max_temperature_c")
    humidity = context.get("humidity_percent")

    if lang == "zh":
        lines = [
            "【高温健康提示】以下内容仅供校园高温健康教育参考，不能替代医生诊断或治疗。",
            f"今日校园综合风险等级：{RISK_LEVEL_LONG['zh'].get(risk, risk)}。",
        ]
        if max_t is not None:
            lines.append(f"参考日最高气温约 {max_t:.1f}℃，相对湿度约 {humidity}%。")
        if outdoor:
            lines.append("今日有户外活动安排：请避免在烈日下长时间运动，活动间隙到阴凉处休息并补水。")
        if age <= 6:
            lines.append("低龄儿童对高温更敏感，建议教师/家长缩短户外停留时间并增加补水频次。")
        if symptoms:
            lines.append(f"已反馈不适：{'、'.join(symptoms)}。")
            lines.append(
                "建议立即停止剧烈活动，转移到通风阴凉处，解开过多衣物，少量多次饮用温水；"
                "请教师或家长陪同观察，若不适加重、意识模糊或持续呕吐等，请尽快联系校医并告知家长就医。"
            )
        else:
            lines.append(
                "暂未反馈明显不适：请继续保持规律饮水、透气衣物与适当休息，"
                "户外活动前后留意是否有头晕、乏力、头痛、恶心或出汗异常等情况。"
            )
        if risk in ("High", "Extreme"):
            lines.append(
                "当前校园高温风险偏高：学校可适当缩短户外课时，增加室内通风与补水提醒。"
            )
        if notes:
            lines.append(f"补充说明：{notes}")
        lines.append("如出现紧急危险情况，请立即联系学校工作人员并拨打当地急救电话。")
        return "\n\n".join(lines)

    lines = [
        "[Heat-health notice] For school awareness and education only — not a medical diagnosis.",
        f"Today's campus risk level: {RISK_LEVEL_LONG['en'].get(risk, risk)}.",
    ]
    if max_t is not None:
        lines.append(
            f"Reference conditions: max temperature about {max_t:.1f}°C, humidity about {humidity}%."
        )
    if outdoor:
        lines.append(
            "Outdoor activity is planned today: avoid long sun exposure, take shade breaks, and drink water regularly."
        )
    if age <= 6:
        lines.append(
            "Younger children are more heat-sensitive; shorten outdoor time and offer water more often."
        )
    if symptoms:
        lines.append(f"Reported symptoms: {', '.join(symptoms)}.")
        lines.append(
            "Stop strenuous activity, move to a cool shaded place, loosen clothing, and sip water slowly. "
            "An adult should stay with the child. If symptoms worsen, consciousness changes, or vomiting persists, "
            "contact the school nurse and seek medical care promptly."
        )
    else:
        lines.append(
            "No symptoms selected: continue hydration, breathable clothing, and rest breaks; "
            "watch for dizziness, fatigue, headache, nausea, or unusual sweating during outdoor time."
        )
    if risk in ("High", "Extreme"):
        lines.append(
            "Campus heat risk is elevated — consider shorter outdoor sessions and extra hydration reminders."
        )
    if notes:
        lines.append(f"Additional notes: {notes}")
    lines.append("In an emergency, contact school staff and local emergency services immediately.")
    return "\n\n".join(lines)


def generate_student_health_guidance_ai(context: dict, lang: str) -> str:
    """Single-turn DeepSeek response for student heat-health education (non-diagnostic)."""
    api_key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is not set")

    if lang == "zh":
        system = (
            "你是 HeatSafe Campus 学生高温健康教育助手。"
            "根据输入信息，用简体中文给出简短、冷静、专业的儿童防暑建议（约 120–200 字）。"
            "仅做健康教育与风险提醒：不得进行疾病诊断、不得开具药物或治疗方案。"
            "若出现严重不适，应建议联系教师、校医或家长并及时就医。"
            "直接输出正文，不要使用 markdown 标题或 JSON。"
        )
        user = (
            "请根据以下信息生成学生高温健康建议：\n\n"
            f"{json.dumps(context, ensure_ascii=False, indent=2)}"
        )
    else:
        system = (
            "You are the HeatSafe Campus student heat-health education assistant. "
            "Provide concise, calm, professional child-safety guidance in English (about 80–140 words). "
            "Educational only — no medical diagnosis, no prescriptions or treatment plans. "
            "If symptoms are serious, advise contacting a teacher, school nurse, or parent and seeking care. "
            "Output plain text only — no markdown headings or JSON."
        )
        user = (
            "Generate student heat-health guidance from this context:\n\n"
            f"{json.dumps(context, indent=2)}"
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
                {"role": "user", "content": user},
            ],
            "temperature": 0.35,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    content = data["choices"][0]["message"]["content"].strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:\w+)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    return content.strip()


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


def metric_reference_sub(label: str, value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return label
    return f"{label}: {value}"


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
    insufficient_shade = st.checkbox(T["insufficient_shade"])
    insufficient_water = st.checkbox(T["insufficient_water"])
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
st.caption(T["daytime_exposure_note"])
render_risk_legend(lang)
with st.expander(T["risk_factors_title"], expanded=False):
    st.markdown(T["risk_factors_body"])

today_temp = float(primary_series_value(today, COL_DAYTIME_TEMP, COL_MAX_TEMP))
today_humidity = int(primary_series_value(today, COL_DAYTIME_HUM, COL_MAX_HUM))
today_uv = primary_series_value(today, COL_DAYTIME_UV, COL_MAX_UV)
today_apparent = optional_float(primary_series_value(today, COL_DAYTIME_APPARENT, COL_MAX_APPARENT))
today_us_aqi = optional_float(primary_series_value(today, AQ_COL_US_AQI_DAY, AQ_COL_US_AQI_MAX))
today_pm25 = optional_float(primary_series_value(today, AQ_COL_PM25_DAY, AQ_COL_PM25_MAX))
max_temp_ref = today.get(COL_MAX_TEMP)
hum_max_ref = today.get(COL_MAX_HUM)
uv_max_ref = today.get(COL_MAX_UV)

risk_max_temp = float(max_temp_ref if max_temp_ref is not None else today_temp)
risk_humidity = int(hum_max_ref if hum_max_ref is not None else today_humidity)
risk_apparent = optional_float(today.get(COL_MAX_APPARENT))
if risk_apparent is None:
    risk_apparent = today_apparent
risk_aqi = optional_float(primary_series_value(today, AQ_COL_US_AQI_MAX, AQ_COL_US_AQI_DAY))

risk_score = calculate_risk_score(
    risk_max_temp,
    risk_humidity,
    risk_apparent,
    risk_aqi,
    school_type,
    outdoor_activity,
    insufficient_shade,
    insufficient_water,
)
today_risk = risk_level(risk_score)
risk_style = RISK_STYLES[today_risk]

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
    render_metric_card(
        T["metric_temp"],
        f"{today_temp} °C",
        "🌡️",
        metric_reference_sub(
            T["metric_temp_sub"], f"{max_temp_ref} °C" if max_temp_ref is not None else None
        ),
        "#009EDC",
    )
with m3:
    render_metric_card(
        T["metric_hum"],
        f"{today_humidity}%",
        "💧",
        metric_reference_sub(
            T["metric_hum_sub"], f"{hum_max_ref}%" if hum_max_ref is not None else None
        ),
        "#5C9EAD",
    )
with m4:
    render_metric_card(
        T["metric_uv"],
        format_uv(today_uv, lang),
        "☀️",
        metric_reference_sub(
            T["metric_uv_sub"],
            format_uv(uv_max_ref, lang) if uv_max_ref is not None else None,
        ),
        "#F4A261",
    )
with m5:
    render_metric_card(
        T["metric_aqi"],
        format_air_metric(primary_series_value(today, AQ_COL_US_AQI_DAY, AQ_COL_US_AQI_MAX)),
        "🌫️",
        T["metric_aqi_sub"],
        "#6B5B95",
    )
with m6:
    render_metric_card(
        T["metric_pm25"],
        format_air_metric(primary_series_value(today, AQ_COL_PM25_DAY, AQ_COL_PM25_MAX)),
        "😷",
        metric_reference_sub(
            T["metric_pm25_sub"],
            format_air_metric(today.get(AQ_COL_PM25_MAX))
            if AQ_COL_PM25_MAX in today.index
            else None,
        ),
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
    "insufficient_campus_shade": bool(insufficient_shade),
    "insufficient_drinking_water_facilities": bool(insufficient_water),
    "exposure_window": "10:00–16:00 local daytime average",
    "risk_scoring_note": "Risk score uses daily max temperature, humidity, apparent temp, and AQI",
    "risk_max_temperature_c": risk_max_temp,
    "risk_humidity_percent": risk_humidity,
    "risk_apparent_temperature_c": risk_apparent,
    "risk_us_aqi": risk_aqi,
    "daytime_avg_temperature_c": float(today_temp),
    "daytime_avg_apparent_temperature_c": today_apparent,
    "daytime_avg_humidity_percent": int(today_humidity),
    "daytime_avg_uv_index": _uv_numeric(today_uv),
    "daytime_avg_us_aqi": today_us_aqi,
    "daytime_avg_pm25_ug_m3": today_pm25,
    "daily_max_temperature_c": optional_float(today.get(COL_MAX_TEMP)),
    "daily_max_apparent_temperature_c": optional_float(today.get(COL_MAX_APPARENT)),
    "daily_max_humidity_percent": optional_float(today.get(COL_MAX_HUM)),
    "daily_max_uv_index": _uv_numeric(today.get(COL_MAX_UV)),
    "risk_score": float(risk_score),
    "risk_level": today_risk,
    "language": "Chinese" if lang == "zh" else "English",
    "geocoding_source": location.get("source", ""),
}

guidance_teachers = generate_guidance(
    "Teachers", today_risk, today_temp, today_humidity, today_uv, outdoor_activity, lang
)
guidance_parents = generate_guidance(
    "Parents", today_risk, today_temp, today_humidity, today_uv, outdoor_activity, lang
)
guidance_nurses = generate_guidance(
    "School Nurses", today_risk, today_temp, today_humidity, today_uv, outdoor_activity, lang
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

notice_city = (city_disp or (city or "").strip() or loc_fmt.split(",")[0]).strip()
parent_notice_text = generate_parent_notice(
    lang,
    display_school,
    notice_city,
    today_risk,
    risk_max_temp,
    risk_apparent,
    risk_humidity,
    risk_aqi,
    outdoor_activity,
)

st.markdown(f'<p class="section-title">{T["sec_parent_notice"]}</p>', unsafe_allow_html=True)
st.text_area(
    T["parent_notice_label"],
    value=parent_notice_text,
    height=320,
)
render_copy_notice_button(
    T["copy_notice"],
    parent_notice_text,
    "heatsafe_copy_parent_notice",
)
st.caption(T["notice_disclaimer"])

st.markdown(f'<p class="section-title">{T["sec_student_ai"]}</p>', unsafe_allow_html=True)
st.caption(T["student_disclaimer"])

with st.form("student_heat_health_form", clear_on_submit=False):
    age_col, outdoor_col = st.columns(2)
    with age_col:
        student_age_input = st.number_input(
            T["student_age"],
            min_value=3,
            max_value=18,
            value=8,
            step=1,
        )
    with outdoor_col:
        student_outdoor_choice = st.radio(
            T["student_outdoor"],
            options=[T["yes"], T["no"]],
            horizontal=True,
            index=0,
        )

    st.markdown(f"**{T['student_symptoms']}**")
    sym_cols = st.columns(3)
    symptom_checked: dict[str, bool] = {}
    for i, key in enumerate(STUDENT_SYMPTOM_KEYS):
        with sym_cols[i % 3]:
            symptom_checked[key] = st.checkbox(STUDENT_SYMPTOM_LABELS[lang][key])
    student_notes_input = st.text_area(
        T["student_notes"],
        placeholder=T["student_notes_ph"],
        height=72,
    )
    student_form_submitted = st.form_submit_button(
        T["student_generate"],
        type="primary",
        use_container_width=True,
    )

if student_form_submitted:
    selected_symptoms = [
        STUDENT_SYMPTOM_LABELS[lang][key]
        for key in STUDENT_SYMPTOM_KEYS
        if symptom_checked.get(key)
    ]
    student_health_context = {
        "student_age": int(student_age_input),
        "outdoor_activity_today": student_outdoor_choice == T["yes"],
        "symptoms": selected_symptoms,
        "notes": student_notes_input.strip(),
        "campus_risk_level": today_risk,
        "campus_risk_score": float(risk_score),
        "max_temperature_c": risk_max_temp,
        "apparent_temperature_c": risk_apparent,
        "humidity_percent": risk_humidity,
        "us_aqi": risk_aqi,
        "city": notice_city,
        "school_name": display_school,
    }
    student_guidance_text = ""
    student_guidance_source = ""
    api_key_set = bool((os.environ.get("DEEPSEEK_API_KEY") or "").strip())
    if api_key_set:
        try:
            student_guidance_text = generate_student_health_guidance_ai(
                student_health_context, lang
            )
            student_guidance_source = T["student_ai_ok"]
        except Exception as exc:
            student_guidance_text = generate_student_health_guidance_rules(
                student_health_context, lang
            )
            student_guidance_source = f"{T['student_rules_ok']} ({type(exc).__name__})"
    else:
        student_guidance_text = generate_student_health_guidance_rules(
            student_health_context, lang
        )
        student_guidance_source = T["student_rules_ok"]

    st.info(student_guidance_text)
    st.caption(student_guidance_source)

st.markdown(
    f"""
    <div class="disclaimer">
        {T["disclaimer"]}
    </div>
    """,
    unsafe_allow_html=True,
)
