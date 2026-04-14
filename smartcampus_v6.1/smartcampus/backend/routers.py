import asyncio
import time
import os
from fastapi import APIRouter, WebSocket
from core import lock, global_state, chat_manager
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
