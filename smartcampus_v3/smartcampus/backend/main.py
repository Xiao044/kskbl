from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import threading
import asyncio

from core import PCAP_FILE
from engine import parse_pcap_worker, queue_consumer
from routers import router

# 🌟 核心升级：使用最新的 lifespan 特性管理启动和关闭任务
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ================= 启动前执行 =================
    # 启动抓包解析引擎线程
    threading.Thread(target=parse_pcap_worker, args=(PCAP_FILE,), daemon=True).start()
    # 启动队列消费者异步任务
    consumer_task = asyncio.create_task(queue_consumer())
    
    yield # 把控制权交还给 FastAPI 正常运行
    
    # ================= 停止时执行 =================
    consumer_task.cancel() # 安全取消队列消费任务

# 将 lifespan 绑定到 FastAPI 实例
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)