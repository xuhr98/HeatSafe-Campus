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
