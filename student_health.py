import json
import os
import re

import requests

from config import DEEPSEEK_CHAT_URL
from text_strings import RISK_LEVEL_LONG

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
