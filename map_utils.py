import html

import folium
import streamlit as st
from streamlit_folium import st_folium

from geocoding import format_location
from text_strings import STRINGS

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
