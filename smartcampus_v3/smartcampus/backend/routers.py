import asyncio
import time
import os
from fastapi import APIRouter, WebSocket
from core import lock, global_state, chat_manager

# 🌟 1. 引入 OpenAI 的异步客户端 (DeepSeek 完全兼容此 SDK)
from openai import AsyncOpenAI

# 从环境变量读取，或直接填写你的 DeepSeek API Key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-b70a25dd21b44629ab4b6e11412654c6") 

# 🌟 2. 初始化客户端，将基础 URL 指向 DeepSeek 官方接口
client = AsyncOpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com/v1"
)

router = APIRouter()

@router.get("/api/topk")
async def get_topk():
    with lock: return {"top10": global_state["topk_flow"]}

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
                global_state["current_alerts"] = []
            await ws.send_json(payload)
            await asyncio.sleep(1) 
    except: pass

@router.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    await chat_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            await chat_manager.broadcast(data)
            
            if data.get("targetId") == "ai":
                user_text = data['text']
                
                with lock:
                    recent_alerts = global_state.get("current_alerts", [])
                    if recent_alerts:
                        alert_details = [f"时间:{a['time']} | 攻击源:{a['src_ip']} | 类型:{a['type']}" for a in recent_alerts[-5:]]
                        context_str = "【当前网络异常告警】：\n" + "\n".join(alert_details)
                    else:
                        context_str = "【当前网络状态】：非常安全，暂无任何异常告警。"

                # 🌟 3. 构建 DeepSeek 的 System Prompt
                system_prompt = f"""你是一个高级网络安全运维 AI 助手，集成在一个叫 Net Monitor 的流量分析大屏中。
请用简短、专业、干练的中文回答用户的网络运维问题（尽量控制在100字以内，除非需要详细解释）。
如果用户询问网络状况，请严格结合下方的【实时数据上下文】进行回答。

{context_str}
"""
                try:
                    # 🌟 4. 调用 DeepSeek 接口 (推荐使用 deepseek-chat，速度极快)
                    response = await client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_text}
                        ],
                        max_tokens=300,
                        temperature=0.3 # 稍微降低温度，让运维回答更严谨
                    )
                    reply_text = response.choices[0].message.content
                    
                except Exception as e:
                    reply_text = f"⚠️ DeepSeek 引擎调用失败，请检查网络或 API Key。日志：{str(e)[:100]}"

                ai_reply = {
                    "id": str(time.time()), 
                    "senderId": "ai", 
                    "targetId": "me",
                    "senderName": "网络运维 AI (DeepSeek)", 
                    "text": reply_text,
                    "time": time.strftime("%H:%M", time.localtime())
                }
                await chat_manager.broadcast(ai_reply)
                
    except Exception as e:
        chat_manager.disconnect(ws)