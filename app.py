"""HeatSafe Campus — Streamlit MVP (mock weather, no backend)."""

import pandas as pd
import streamlit as st

CITIES = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen"]
SCHOOL_TYPES = ["Kindergarten", "Primary School", "Middle School"]

# Base mock conditions per city (today); 7-day series built from these.
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


def build_mock_forecast(city: str) -> pd.DataFrame:
    """Return a 7-day mock weather dataframe for the selected city."""
    base = CITY_WEATHER[city]
    rows = []
    for day in range(7):
        offset = day * 0.4
        rows.append(
            {
                "Day": f"Day {day + 1}",
                "Max Temp (°C)": round(base["max_temp"] - day * 0.6 + (day % 2) * 0.5, 1),
                "Humidity (%)": int(max(30, min(95, base["humidity"] + day * 2 - 3))),
                "Conditions": ["Sunny", "Partly cloudy", "Cloudy", "Light rain"][day % 4],
            }
        )
    return pd.DataFrame(rows)


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
    """Simple demo risk score from weather and school context."""
    temp_component = max(0, (max_temp - 28) * 4)
    humidity_component = max(0, (humidity - 60) * 0.5)
    score = (temp_component + humidity_component) * SCHOOL_TYPE_FACTOR[school_type]
    if outdoor_activity:
        score *= 1.12
    return round(min(100, score), 1)


st.set_page_config(
    page_title="HeatSafe Campus",
    page_icon="🌡️",
    layout="wide",
)

st.title("HeatSafe Campus")
st.markdown(
    "AI-powered heat risk alerts for schools. This prototype helps teachers, "
    "parents, and school nurses plan safer outdoor activities using child-specific "
    "heat risk guidance (demo uses mock weather data)."
)

with st.sidebar:
    st.header("School settings")
    school_name = st.text_input("School name", placeholder="e.g. Sunshine Elementary")
    city = st.selectbox("City", CITIES)
    school_type = st.selectbox("School type", SCHOOL_TYPES)
    outdoor_activity = st.checkbox("Outdoor activity planned today")

forecast = build_mock_forecast(city)
today = forecast.iloc[0]
max_temp = today["Max Temp (°C)"]
humidity = today["Humidity (%)"]
risk_score = calculate_risk_score(
    max_temp, humidity, school_type, outdoor_activity
)
today_risk = risk_level(risk_score)

display_school = school_name.strip() or "Your school"
st.subheader(f"Dashboard — {display_school}, {city}")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Today risk level", today_risk)
col2.metric("Today risk score", f"{risk_score}/100")
col3.metric("Max temperature", f"{max_temp} °C")
col4.metric("Humidity", f"{humidity}%")

st.divider()
st.subheader("7-day forecast (mock data)")
st.dataframe(forecast, use_container_width=True, hide_index=True)

st.divider()
st.subheader("Role-specific guidance")
st.caption("Placeholder content — guidance will be generated from risk level and school context.")

guide_col1, guide_col2, guide_col3 = st.columns(3)

with guide_col1:
    st.markdown("**Teachers**")
    st.info(
        "Monitor students during outdoor breaks. Adjust activity intensity based on "
        "today's risk level. Hydration breaks every 20–30 minutes when risk is elevated."
    )

with guide_col2:
    st.markdown("**Parents**")
    st.info(
        "Ensure children wear light clothing and bring water. Consider pickup or "
        "indoor play when risk is High or Extreme."
    )

with guide_col3:
    st.markdown("**School nurses**")
    st.info(
        "Watch for heat-related symptoms (dizziness, nausea, excessive fatigue). "
        "Keep first-aid and cooling supplies ready during peak heat hours."
    )
