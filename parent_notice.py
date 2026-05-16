import html
import json
from datetime import date

import streamlit.components.v1 as components

from text_strings import PARENT_NOTICE_ACTIONS, RISK_LEVEL_LONG

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
