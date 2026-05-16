"""HeatSafe Campus — Streamlit MVP entry point."""

import os

import requests
import streamlit as st

from config import (
    AQ_COL_PM25_DAY,
    AQ_COL_PM25_MAX,
    AQ_COL_US_AQI_DAY,
    AQ_COL_US_AQI_MAX,
    COL_DAYTIME_APPARENT,
    COL_DAYTIME_HUM,
    COL_DAYTIME_TEMP,
    COL_DAYTIME_UV,
    COL_MAX_APPARENT,
    COL_MAX_HUM,
    COL_MAX_TEMP,
    COL_MAX_UV,
    FALLBACK_CITY,
    LANG_FROM_LABEL,
    SCHOOL_TYPES,
)
from geocoding import format_location, normalize_city_name
from guidance import generate_ai_guidance, generate_guidance, uv_numeric
from parent_notice import generate_parent_notice, render_copy_notice_button
from risk import calculate_risk_score, risk_level
from student_health import (
    generate_student_health_guidance_ai,
    generate_student_health_guidance_rules,
)
from map_utils import render_school_location_map
from text_strings import (
    RISK_LEVEL_LONG,
    RISK_SHORT,
    RISK_STYLES,
    SCHOOL_TYPE_LABELS,
    STRINGS,
    STUDENT_SYMPTOM_KEYS,
    STUDENT_SYMPTOM_LABELS,
)
from ui_components import (
    build_forecast_chart,
    format_air_metric,
    format_uv,
    inject_theme_css,
    localize_forecast_display,
    metric_reference_sub,
    optional_float,
    render_guide_card,
    render_metric_card,
    render_risk_legend,
)
from weather import load_forecast, merge_air_quality_into_forecast, primary_series_value

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
    "daytime_avg_uv_index": uv_numeric(today_uv),
    "daytime_avg_us_aqi": today_us_aqi,
    "daytime_avg_pm25_ug_m3": today_pm25,
    "daily_max_temperature_c": optional_float(today.get(COL_MAX_TEMP)),
    "daily_max_apparent_temperature_c": optional_float(today.get(COL_MAX_APPARENT)),
    "daily_max_humidity_percent": optional_float(today.get(COL_MAX_HUM)),
    "daily_max_uv_index": uv_numeric(today.get(COL_MAX_UV)),
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
