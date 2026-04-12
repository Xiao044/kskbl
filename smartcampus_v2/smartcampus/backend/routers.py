import asyncio
import time
import os
from fastapi import APIRouter, WebSocket
from core import lock, global_state, chat_manager

# 导入全新的官方推荐 SDK
from google import genai

# 优先从 Linux 环境变量读取，如果没有则使用默认字符串
# 强烈建议在运行脚本前执行: export GEMINI_API_KEY="你的真实Key"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyBq58gsG7VgV-W5t1QTHsUSOuZVtKqwrB8") 

# 初始化新版客户端
client = genai.Client(api_key=GEMINI_API_KEY)

router = APIRouter()

@router.get("/api/topk")
async def get_topk():
    """全网 Top-K 历史累计排行"""
    with lock: 
        return {"top10": global_state["topk_flow"]}

@router.websocket("/ws/flow")
async def websocket_flow(ws: WebSocket):
    """大屏实时流与告警推送通道"""
    await ws.accept()
    try:
        while True:
            with lock:
                payload = {
                    "flow": global_state["current_flow"].copy(),
                    "alerts": global_state["current_alerts"].copy()
                }
                # 发送完后清空缓冲，避免重复告警
                global_state["current_alerts"] = []
            await ws.send_json(payload)
            await asyncio.sleep(1) 
    except: 
        pass

@router.websocket("/ws/chat")
async def websocket_chat(ws: WebSocket):
    """运维 AI 协同助手通道 (接入 Gemini 大模型)"""
    await chat_manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            # 广播用户的消息给所有打开大屏的人
            await chat_manager.broadcast(data)
            
            # 拦截发送给 AI 的指令
            if data.get("targetId") == "ai":
                user_text = data['text']
                
                # --- 注入实时网络态势上下文 ---
                with lock:
                    recent_alerts = global_state.get("current_alerts", [])
                    if recent_alerts:
                        alert_details = [f"时间:{a['time']} | 攻击源:{a['src_ip']} | 类型:{a['type']}" for a in recent_alerts[-5:]]
                        context_str = "【当前网络异常告警】：\n" + "\n".join(alert_details)
                    else:
                        context_str = "【当前网络状态】：非常安全，暂无任何异常告警。"

                prompt = f"""你是一个高级网络安全运维 AI 助手，集成在一个叫 Net Monitor 的流量分析大屏中。
请用简短、专业、干练的中文回答用户的网络运维问题（尽量控制在100字以内，除非需要详细解释）。
如果用户询问网络状况，请结合下方的【实时数据上下文】进行回答。

{context_str}

【用户指令】：
{user_text}
"""
                try:
                    # 首选方案：尝试调用最新、最强的 2.5 模型
                    response = await client.aio.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=prompt
                    )
                    reply_text = response.text
                    
                except Exception as e:
                    error_msg = str(e)
                    # 捕获 503 拥堵报错，触发自动降级策略
                    if "503" in error_msg or "high demand" in error_msg:
                        print(f"\n[⚠️ 流量洪峰] 2.5 模型当前拥堵，触发高可用策略，自动降级至 1.5-flash...")
                        try:
                            # 备用方案：无缝切换到极其稳定、高并发的 1.5-flash 模型
                            response = await client.aio.models.generate_content(
                                model='gemini-1.5-flash',
                                contents=prompt
                            )
                            reply_text = response.text
                        except Exception as e2:
                            reply_text = "⚠️ 警报：AI 算力集群当前全线拥挤，已触发限流保护，请稍后再试。"
                    else:
                        # 其他非拥堵类的错误（比如断网、Key 错误等）
                        reply_text = f"⚠️ AI 引擎内部错误，请检查网络连接或 API Key。日志：{error_msg[:100]}"

                # 将 AI 的回复打包发回前端
                ai_reply = {
                    "id": str(time.time()), 
                    "senderId": "ai", 
                    "targetId": "me",
                    "senderName": "网络运维 AI (Gemini)", 
                    "text": reply_text,
                    "time": time.strftime("%H:%M", time.localtime())
                }
                await chat_manager.broadcast(ai_reply)
                
    except Exception as e:
        chat_manager.disconnect(ws)