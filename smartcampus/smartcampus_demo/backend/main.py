from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import random

app = FastAPI()

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 模拟秒级流量数据
flow_data = [{"src_ip": f"10.0.0.{i}", "bytes": random.randint(100, 1000)} for i in range(1, 6)]

@app.get("/api/topk")
async def get_topk():
    """返回 Top-K 流量 IP"""
    # 按 bytes 排序
    sorted_data = sorted(flow_data, key=lambda x: x["bytes"], reverse=True)
    return {"top10": sorted_data[:5]}

@app.websocket("/ws/flow")
async def websocket_flow(ws: WebSocket):
    """WebSocket 实时推送秒级流量"""
    await ws.accept()
    while True:
        # 每秒更新模拟流量
        for record in flow_data:
            record["bytes"] = random.randint(100, 1000)
        await ws.send_json(flow_data)
        await asyncio.sleep(1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
