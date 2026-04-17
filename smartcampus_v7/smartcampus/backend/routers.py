import asyncio
import time
import os
from fastapi import APIRouter, WebSocket
from core import lock, global_state, chat_manager, playback_queue
from openai import AsyncOpenAI

# 初始化 DeepSeek 客户端
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-b70a25dd21b44629ab4b6e11412654c6")
client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

router = APIRouter()

# --- 1. 大流排行数据接口 ---
@router.get("/api/topk")
async def get_topk():
    with lock:
        return {
            "top10": global_state["topk_flow"]
        }

# --- 2. 流量数据 WebSocket ---
@router.websocket("/ws/flow")
async def websocket_flow(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            with lock:
                payload = {
                    "flow": global_state["current_flow"].copy(),
                    "alerts": global_state["current_alerts"].copy()
                }
                # 推送后清空当前告警缓冲，防止重复触发
                global_state["current_alerts"] = []
            await ws.send_json(payload)
            await asyncio.sleep(1)
    except:
        pass

# --- 3. DeepSeek AI 运维对话接口 ---
@router.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    await chat_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            await chat_manager.broadcast(data)

            if data.get("targetId") == "ai":
                user_text = data['text']

                # 构建 AI 实时语境
                with lock:
                    recent_alerts = global_state.get("current_alerts", [])
                    if recent_alerts:
                        alert_details = [f"[{a['time']}] {a['type']} (来源:{a['src_ip']})" for a in recent_alerts[-3:]]
                        context_str = "【实时告警】：" + "；".join(alert_details)
                    else:
                        context_str = "【系统状态】：运行平稳，无安全威胁。"

                system_prompt = f"""你是一个高级网安 AIOps 助手。请基于以下数据简短回答问题：{context_str}
要求：专业、干练，100字以内。"""

                try:
                    response = await client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_text}
                        ],
                        max_tokens=300,
                        temperature=0.3
                    )
                    reply_text = response.choices[0].message.content
                except Exception as e:
                    reply_text = f"⚠️ 诊断引擎暂时不可用 ({str(e)[:50]})"

                ai_reply = {
                    "id": str(time.time()),
                    "senderId": "ai",
                    "targetId": "me",
                    "senderName": "DeepSeek 安全分析官",
                    "text": reply_text,
                    "time": time.strftime("%H:%M")
                }
                await chat_manager.broadcast(ai_reply)

    except:
        chat_manager.disconnect(ws)

# --- 4. 区域流量透视接口 ---
@router.get("/api/zone-stats")
async def get_zone_stats():
    """区域流量透视数据 — 按区域聚合流量统计"""
    with lock:
        flows = global_state["current_flow"].copy()

    zone_agg = {}
    for item in flows:
        zone = item.get("src_zone", "未知")
        if zone not in zone_agg:
            zone_agg[zone] = {"bytes": 0, "packets": 0, "flows": 0, "buildings": set()}
        zone_agg[zone]["bytes"] += item.get("bytes", 0)
        zone_agg[zone]["packets"] += item.get("packets", 0)
        zone_agg[zone]["flows"] += 1
        zone_agg[zone]["buildings"].add(item.get("src_building", "未知"))

    result = []
    for zone, stats in zone_agg.items():
        result.append({
            "zone": zone,
            "bytes": stats["bytes"],
            "packets": stats["packets"],
            "flows": stats["flows"],
            "buildings": list(stats["buildings"]),
            "mbps": round(stats["bytes"] * 8 / 1024 / 1024, 2)
        })
    result.sort(key=lambda x: x["bytes"], reverse=True)
    return {"zones": result}

# --- 5. 系统资源监控接口 ---
@router.get("/api/system-stats")
async def get_system_stats():
    """系统资源占用实时监控"""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_mb = round(mem_info.rss / 1024 / 1024, 1)
        cpu_pct = process.cpu_percent(interval=0.1)
        threads = process.num_threads()
    except ImportError:
        mem_mb, cpu_pct, threads = -1, -1, -1

    with lock:
        flow_count = len(global_state["current_flow"])
        alert_count = len(global_state["current_alerts"])

    return {
        "memory_mb": mem_mb,
        "cpu_percent": cpu_pct,
        "threads": threads,
        "queue_size": playback_queue.qsize(),
        "active_flows": flow_count,
        "total_alerts": alert_count,
        "status": "healthy" if mem_mb < 300 or mem_mb == -1 else "warning"
    }

# --- 6. 威胁地理溯源接口（校园地图） ---
@router.get("/api/threat-geo")
async def get_threat_geo():
    """告警校园分布数据 — 供前端校园地图组件使用"""
    with lock:
        alerts = global_state.get("current_alerts", []).copy()

    geo_points = []
    seen = {}
    for alert in alerts:
        geo = alert.get("geo", {})
        lat = geo.get("lat", 0)
        lon = geo.get("lon", 0)
        if lat == 0 and lon == 0:
            continue
        key = f"{round(lat, 1)}_{round(lon, 1)}"
        building = geo.get("building", "未知")
        zone = geo.get("zone", "未知")
        if key not in seen:
            point = {
                "name": f"{building} ({alert.get('src_ip', '')})",
                "value": [lon, lat, 1],
                "threat_type": alert.get("category", ""),
                "level": alert.get("level", "medium"),
                "building": building,
                "zone": zone,
                "src_ip": alert.get("src_ip", ""),
                "src_zone": alert.get("src_zone", "未知"),
            }
            geo_points.append(point)
            seen[key] = len(geo_points) - 1
        else:
            idx = seen[key]
            geo_points[idx]["value"][2] += 1

    return {"geo_points": geo_points}
