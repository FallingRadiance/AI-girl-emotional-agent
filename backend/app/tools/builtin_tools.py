import ast
import operator as op
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Any, Dict, List

import httpx

from app.config import settings

SAFE_OPS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}


async def weather_tool(city: str) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        geo = await client.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "zh", "format": "json"},
        )
        gdata = geo.json()
        if not gdata.get("results"):
            return {"ok": False, "error": f"未找到城市: {city}"}
        c = gdata["results"][0]
        lat, lon = c["latitude"], c["longitude"]
        weather = await client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            },
        )
        wdata = weather.json().get("current", {})
        return {
            "ok": True,
            "city": c.get("name"),
            "country": c.get("country"),
            "temperature_c": wdata.get("temperature_2m"),
            "humidity": wdata.get("relative_humidity_2m"),
            "wind_kmh": wdata.get("wind_speed_10m"),
            "weather_code": wdata.get("weather_code"),
        }


def datetime_tool() -> Dict[str, Any]:
    now = datetime.now(ZoneInfo(settings.app_timezone))
    return {
        "ok": True,
        "timezone": settings.app_timezone,
        "iso": now.isoformat(),
        "human": now.strftime("%Y-%m-%d %H:%M:%S"),
        "weekday": now.strftime("%A"),
    }


async def news_tool(limit: int = 5) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://hn.algolia.com/api/v1/search",
            params={"tags": "front_page", "hitsPerPage": limit},
        )
        hits = r.json().get("hits", [])
        items: List[Dict[str, str]] = []
        for h in hits[:limit]:
            items.append(
                {
                    "title": h.get("title") or "(no title)",
                    "url": h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}",
                    "source": "Hacker News",
                }
            )
        return {"ok": True, "items": items}


def _eval_ast(node):
    if isinstance(node, ast.Num):
        return node.n
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp):
        return SAFE_OPS[type(node.op)](_eval_ast(node.left), _eval_ast(node.right))
    if isinstance(node, ast.UnaryOp):
        return SAFE_OPS[type(node.op)](_eval_ast(node.operand))
    raise ValueError("Unsupported expression")


def math_tool(expression: str) -> Dict[str, Any]:
    try:
        node = ast.parse(expression, mode="eval").body
        val = _eval_ast(node)
        return {"ok": True, "expression": expression, "result": val}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


TOOL_REGISTRY = {
    "weather": {
        "description": "查询城市天气。参数: city",
        "args": {"city": "str"},
        "handler": weather_tool,
    },
    "datetime": {
        "description": "查询当前日期和时间。不需要参数。",
        "args": {},
        "handler": datetime_tool,
    },
    "news": {
        "description": "查询最新科技新闻头条。参数可选: limit",
        "args": {"limit": "int"},
        "handler": news_tool,
    },
    "math": {
        "description": "数学计算。参数: expression，比如 (2+3)*4",
        "args": {"expression": "str"},
        "handler": math_tool,
    },
}


async def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    if name not in TOOL_REGISTRY:
        return {"ok": False, "error": f"Unknown tool: {name}"}
    handler = TOOL_REGISTRY[name]["handler"]
    if callable(handler):
        if name == "datetime":
            return handler()
        result = handler(**args)
        if hasattr(result, "__await__"):
            return await result
        return result
    return {"ok": False, "error": "Tool handler invalid"}
