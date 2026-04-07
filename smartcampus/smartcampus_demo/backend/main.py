from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import uvicorn

from db.database import db_manager
from api.endpoints import traffic
from websockets import flow_ws
from services.ingestion import data_ingestion_pipeline

app = FastAPI(title="智慧校园网络流量监控与安全态势感知系统 API")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由组 (设置了统一前缀)
app.include_router(traffic.router, prefix="/api/traffic", tags=["Traffic"])

# 注册 WebSocket 路由组
app.include_router(flow_ws.router, prefix="/ws", tags=["WebSocket"])

@app.on_event("startup")
async def startup_event():
    # 1. 启动并挂载数据库
    await db_manager.connect_redis()
    db_manager.connect_clickhouse()
    
    # 2. 挂载后台数据流注入引擎
    asyncio.create_task(data_ingestion_pipeline())

@app.on_event("shutdown")
async def shutdown_event():
    # 优雅关闭，释放资源
    await db_manager.close()

if __name__ == "__main__":
    # 使用 reload=True 开启热更新，方便后续调试
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)