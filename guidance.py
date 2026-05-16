import json
import os
import re

import pandas as pd
import requests

from config import DEEPSEEK_CHAT_URL
from text_strings import GUIDANCE_ADDONS, GUIDANCE_BASE

def uv_numeric(uv_index) -> float | None:
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

    uv = uv_numeric(uv_index)
    if uv is not None and uv > 8:
        parts.append(addons["high_uv"][role])
    if humidity >= 65:
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
