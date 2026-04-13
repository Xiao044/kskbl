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
    print("[*] 正在启动后台服务，监听所有局域网地址...")
    # ================= 启动前执行 =================
    # 启动抓包解析引擎线程
    threading.Thread(target=parse_pcap_worker, args=(PCAP_FILE,), daemon=True).start()
    # 启动队列消费者异步任务
    consumer_task = asyncio.create_task(queue_consumer())
    print("[OK] 高敏嗅探引擎已挂载到后台。")
    
    yield # 把控制权交还给 FastAPI 正常运行
    
    # ================= 停止时执行 =================
    print("[!] 接收到关闭信号，正在清理系统资源...")
    consumer_task.cancel() # 安全取消队列消费任务

# 将 lifespan 绑定到 FastAPI 实例
app = FastAPI(lifespan=lifespan)

# 🌟 补充完善 CORS 配置，确保跨域请求（含 Token 和 WS）顺畅
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  # 新增：允许携带凭证（如 Cookie, Authorization Header 等）
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # 这里的 0.0.0.0 保证了局域网的其他电脑能够连接你的 8000 端口
    uvicorn.run(app, host="0.0.0.0", port=8000)