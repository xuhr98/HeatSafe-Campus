"""HeatSafe Campus — Streamlit MVP (Open-Meteo + mock fallback)."""

import json
import os
import re

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from plotly.subplots import make_subplots

SCHOOL_TYPES = ["Kindergarten", "Primary School", "Middle School"]
FALLBACK_CITY = "Beijing"

CITY_COORDS = {
    "Beijing": (39.9042, 116.4074),
    "Shanghai": (31.2304, 121.4737),
    "Guangzhou": (23.1291, 113.2644),
    "Shenzhen": (22.5431, 114.0579),
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
DEEPSEEK_CHAT_URL = "https://api.deepseek.com/chat/completions"

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
        "label": "Level 1 · Low",
    },
    "Moderate": {
        "level": 2,
        "color": "#F9A825",
        "bg": "#FFF8E1",
        "label": "Level 2 · Moderate",
    },
    "High": {
        "level": 3,
        "color": "#EF6C00",
        "bg": "#FFF3E0",
        "label": "Level 3 · High",
    },
    "Extreme": {
        "level": 4,
        "color": "#C62828",
        "bg": "#FFEBEE",
        "label": "Level 4 · Extreme",
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
    for day in range(7):
        max_t = round(base["max_temp"] - day * 0.6 + (day % 2) * 0.5, 1)
        hum = int(max(30, min(95, base["humidity"] + day * 2 - 3)))
        # Mock “feels like” max when live apparent temp is unavailable
        apparent = round(max_t + 1.5 + (hum - 50) * 0.035, 1)
        rows.append(
            {
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
                "Day": pd.to_datetime(date_str).strftime("%a %d %b"),
                "Max Temp (°C)": round(max_temp, 1),
                "Apparent temp (°C)": round(apparent, 1) if apparent is not None else None,
                "Humidity (%)": humidity,
                "UV Index": round(uv_index, 1) if uv_index is not None else None,
                "Conditions": _conditions_label(uv_index),
            }
        )
    return pd.DataFrame(rows)


def get_live_weather(city_name: str) -> pd.DataFrame:
    location = geocode_city(city_name)
    return fetch_forecast(location["latitude"], location["longitude"])


def format_location(location: dict) -> str:
    country = location.get("country", "")
    name = location["display_name"]
    return f"{name}, {country}" if country else name


def load_forecast(city_name: str) -> tuple[pd.DataFrame, bool, dict, bool]:
    city_input = (city_name or "").strip() or FALLBACK_CITY
    geocode_failed = False

    try:
        location = geocode_city(city_input)
    except Exception:
        geocode_failed = True
        lat, lon = CITY_COORDS[FALLBACK_CITY]
        location = {
            "latitude": lat,
            "longitude": lon,
            "display_name": FALLBACK_CITY,
            "country": "China",
        }

    try:
        df = fetch_forecast(location["latitude"], location["longitude"])
        return df, True, location, geocode_failed
    except Exception:
        mock_city = FALLBACK_CITY if geocode_failed else _mock_city_key(city_input)
        return build_mock_forecast(mock_city), False, location, geocode_failed


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
) -> float:
    temp_component = max(0, (max_temp - 28) * 4)
    humidity_component = max(0, (humidity - 60) * 0.5)
    score = (temp_component + humidity_component) * SCHOOL_TYPE_FACTOR[school_type]
    if outdoor_activity:
        score *= 1.12
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


def render_risk_legend() -> None:
    levels = [
        ("Level 1 · Low", "#2E7D32", "#E8F5E9"),
        ("Level 2 · Moderate", "#F9A825", "#FFF8E1"),
        ("Level 3 · High", "#EF6C00", "#FFF3E0"),
        ("Level 4 · Extreme", "#C62828", "#FFEBEE"),
    ]
    chips = "".join(
        f'<span style="display:inline-block;margin:0 8px 6px 0;padding:4px 10px;'
        f'border-radius:6px;background:{bg};color:{fg};font-size:0.78rem;">{label}</span>'
        for label, fg, bg in levels
    )
    st.markdown(
        f'<p style="font-size:0.85rem;color:#607D8B;margin:0 0 1rem 0;">Risk scale: {chips}</p>',
        unsafe_allow_html=True,
    )


def build_forecast_chart(forecast: pd.DataFrame) -> go.Figure:
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(
        go.Scatter(
            x=forecast["Day"],
            y=forecast["Max Temp (°C)"],
            name="Max temperature (°C)",
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
            name="Humidity (%)",
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
        title_text="Temperature (°C)",
        secondary_y=False,
        showgrid=True,
        gridcolor="#EEF2F5",
        rangemode="tozero",
    )
    fig.update_yaxes(
        title_text="Humidity (%)",
        secondary_y=True,
        showgrid=False,
        rangemode="tozero",
    )
    return fig


# Rule-based guidance: base text per risk level + optional weather/activity add-ons.
GUIDANCE_BASE = {
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
}

GUIDANCE_ADDONS = {
    "high_uv": {
        "Teachers": "UV is very high: plan activities before 10 a.m. or after 4 p.m., require hats, and use shaded areas.",
        "Parents": "UV is very high: apply sunscreen, send a wide-brim hat, and avoid long sun exposure after school.",
        "School Nurses": "UV is very high: remind staff about sun protection and watch for sun-related discomfort on exposed skin.",
    },
    "high_humidity": {
        "Teachers": "Humidity is elevated: heat feels stronger—slow active games and allow more recovery time in shade.",
        "Parents": "Humidity is elevated: encourage frequent small sips of water; sweaty clothes dry more slowly today.",
        "School Nurses": "Humidity is elevated: combine heat and moisture increases strain—prioritize cooling breaks and fluids.",
    },
    "outdoor_planned": {
        "Teachers": "Outdoor activity is scheduled: assign a hydration leader, cap session length, and keep shade and water nearby.",
        "Parents": "Outdoor activity is scheduled: send extra water and confirm the school has shade or adjusted timing.",
        "School Nurses": "Outdoor activity is scheduled: be available during the session and review the plan for heat-related stops.",
    },
    "very_hot": {
        "Teachers": f"Temperature is high: avoid strenuous drills and watch for students who stop participating or look unwell.",
        "Parents": "Temperature is high: a light meal and water before school help; check in on how your child feels at pickup.",
        "School Nurses": "Temperature is high: treat heat discomfort seriously—move the child to cool space and notify guardians if needed.",
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
) -> str:
    """Build explainable, rule-based guidance from risk level and weather flags."""
    parts = [GUIDANCE_BASE[role][risk]]

    uv = _uv_numeric(uv_index)
    if uv is not None and uv > 8:
        parts.append(GUIDANCE_ADDONS["high_uv"][role])
    if humidity > 70:
        parts.append(GUIDANCE_ADDONS["high_humidity"][role])
    if outdoor_activity:
        parts.append(GUIDANCE_ADDONS["outdoor_planned"][role])
    if temperature >= 35:
        parts.append(GUIDANCE_ADDONS["very_hot"][role])

    return " ".join(parts)


def generate_ai_guidance(context: dict) -> dict[str, str]:
    """Call DeepSeek Chat Completions (OpenAI-compatible). Returns guidance per role."""
    api_key = (os.environ.get("DEEPSEEK_API_KEY") or "").strip()
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY is not set")

    system = (
        "You help schools plan for heat in a prototype called HeatSafe Campus. "
        "Write concise, practical, child-safety-focused advice in English. "
        "Do not diagnose medical conditions or give clinical treatment instructions. "
        "Respond with valid JSON only—no markdown fences or extra text."
    )
    user_payload = (
        "Using the following context, produce role-specific guidance.\n\n"
        f"Context:\n{json.dumps(context, indent=2)}\n\n"
        'Return a single JSON object with exactly these keys and string values '
        '(each value: 2–4 short sentences):\n'
        '"Teachers", "Parents", "School Nurses"\n'
        "Tailor tone to each audience. Be specific to the numbers when helpful."
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


def format_uv(uv_value) -> str:
    if uv_value is None or (isinstance(uv_value, float) and pd.isna(uv_value)):
        return "—"
    return f"{float(uv_value):.1f}"


st.set_page_config(
    page_title="HeatSafe Campus",
    page_icon="🌤️",
    layout="wide",
)

inject_theme_css()

with st.sidebar:
    st.markdown("### 🏫 School settings")
    st.caption("Enter your school and city to assess today's child heat health risk.")
    school_name = st.text_input("School name", placeholder="e.g. Sunshine Elementary")
    city = st.text_input("City name", value="Beijing", placeholder="e.g. Beijing, Tokyo, Shanghai")
    school_type = st.selectbox("School type", SCHOOL_TYPES)
    outdoor_activity = st.checkbox("Outdoor activity planned today")
    use_ai_guidance = st.checkbox("Use AI-generated guidance", value=False)
    st.markdown("---")
    st.markdown("🌡️ **Climate** · Live weather when available")
    st.markdown("🏫 **School** · Child-focused risk factors")
    st.markdown("⚠️ **Safety** · Early warning, not diagnosis")

st.markdown(
    """
    <div class="hero">
        <h1>🌤️ HeatSafe Campus</h1>
        <p class="zh">中国校园儿童高温健康风险 AI 预警系统</p>
        <p class="en">AI-powered heat health early warning system for schools and children.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

forecast, using_live, location, geocode_failed = load_forecast(city)

if geocode_failed:
    st.warning("City not found. Falling back to Beijing demo data.")
if using_live:
    st.success("Using live weather data from Open-Meteo.")
elif not geocode_failed:
    st.warning("Live weather data unavailable. Using demo mock data.")

location_label = format_location(location)
today = forecast.iloc[0]
max_temp = today["Max Temp (°C)"]
humidity = int(today["Humidity (%)"])
today_uv = today.get("UV Index")
apparent_max = today.get("Apparent temp (°C)")
risk_score = calculate_risk_score(max_temp, humidity, school_type, outdoor_activity)
today_risk = risk_level(risk_score)
risk_style = RISK_STYLES[today_risk]

display_school = school_name.strip() or "Your school"
data_source = "live Open-Meteo data" if using_live else "demo mock data"
activity_note = " · Outdoor activity planned" if outdoor_activity else ""

st.markdown(
    f"""
    <div class="context-bar">
        🏫 <strong>{display_school}</strong> &nbsp;·&nbsp;
        📍 {location_label} &nbsp;·&nbsp;
        {school_type} &nbsp;·&nbsp;
        Data: {data_source}{activity_note}
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<p class="section-title">📊 Today\'s heat health dashboard</p>', unsafe_allow_html=True)
render_risk_legend()

m1, m2, m3, m4 = st.columns(4)
with m1:
    render_metric_card(
        "Risk level",
        today_risk,
        "⚠️",
        f"{risk_style['label']} · Score {risk_score}/100",
        risk_style["color"],
    )
with m2:
    render_metric_card("Temperature", f"{max_temp} °C", "🌡️", "Today's forecast max", "#009EDC")
with m3:
    render_metric_card("Humidity", f"{humidity}%", "💧", "Daily maximum", "#5C9EAD")
with m4:
    render_metric_card("UV index", format_uv(today_uv), "☀️", "Peak UV today", "#F4A261")

st.markdown('<p class="section-title">📈 7-day weather trend</p>', unsafe_allow_html=True)
forecast_label = "live data" if using_live else "mock data"
st.caption(f"Temperature and humidity outlook · {forecast_label}")
st.plotly_chart(build_forecast_chart(forecast), width="stretch")

with st.expander("📋 View detailed 7-day forecast table"):
    st.dataframe(forecast, width="stretch", hide_index=True)

st.markdown('<p class="section-title">👧 Role-specific guidance for child safety</p>', unsafe_allow_html=True)

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
}

guidance_teachers = generate_guidance(
    "Teachers", today_risk, max_temp, humidity, today_uv, outdoor_activity
)
guidance_parents = generate_guidance(
    "Parents", today_risk, max_temp, humidity, today_uv, outdoor_activity
)
guidance_nurses = generate_guidance(
    "School Nurses", today_risk, max_temp, humidity, today_uv, outdoor_activity
)

if use_ai_guidance:
    if not (os.environ.get("DEEPSEEK_API_KEY") or "").strip():
        st.warning("DeepSeek API key not found. Using rule-based guidance.")
    else:
        try:
            ai_out = generate_ai_guidance(guidance_context)
            guidance_teachers = ai_out["Teachers"]
            guidance_parents = ai_out["Parents"]
            guidance_nurses = ai_out["School Nurses"]
            st.caption(
                "AI-generated guidance (DeepSeek) from today's context. "
                "Rule-based templates apply if AI is off or unavailable."
            )
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
            st.warning(
                f"AI guidance unavailable. Using rule-based guidance.\n\n**Debug ({type(exc).__name__}):** {detail}"
            )
            st.caption(
                "Rule-based actions from today's risk level, temperature, humidity, UV, and activity plan."
            )
else:
    st.caption(
        "Rule-based actions from today's risk level, temperature, humidity, UV, and activity plan."
    )

g1, g2, g3 = st.columns(3)
with g1:
    render_guide_card(
        "Teachers",
        "👩‍🏫",
        guidance_teachers,
        "#009EDC",
    )
with g2:
    render_guide_card(
        "Parents",
        "👨‍👩‍👧",
        guidance_parents,
        "#7CB9A8",
    )
with g3:
    render_guide_card(
        "School Nurses",
        "🏥",
        guidance_nurses,
        "#E76F51",
    )

st.markdown(
    """
    <div class="disclaimer">
        <strong>Disclaimer:</strong> This tool provides early warning and health education support only.
        It does not provide medical diagnosis.
    </div>
    """,
    unsafe_allow_html=True,
)
