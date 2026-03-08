SKILLS = {
    "empathetic_listener": "擅长共情倾听，复述感受并给出安抚。",
    "mood_booster": "擅长把对话引导到积极方向，提供轻量鼓励与行动建议。",
    "life_coach": "擅长把目标拆解成可执行的下一步。",
    "info_assistant": "擅长调用工具查询事实信息（天气、时间、新闻、计算）。",
}


def pick_skill(message: str) -> str:
    text = message.lower()
    if any(k in text for k in ["天气", "几点", "时间", "新闻", "算", "计算", "weather", "news", "time"]):
        return "info_assistant"
    if any(k in text for k in ["计划", "目标", "执行", "拖延", "学习", "work", "plan"]):
        return "life_coach"
    if any(k in text for k in ["难过", "焦虑", "伤心", "emo", "孤独", "stress", "sad", "anxious"]):
        return "empathetic_listener"
    return "mood_booster"
