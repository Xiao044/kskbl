from fastapi import APIRouter, WebSocket
import asyncio
import time
from db.database import db_manager

router = APIRouter()

@router.websocket("/flow")
async def websocket_flow(ws: WebSocket):
    """解耦后的 WebSocket：只负责读 Redis 推送"""
    await ws.accept()
    try:
        while True:
            target_ts = int(time.time()) - 1 
            
            if db_manager.redis_client:
                pipe = db_manager.redis_client.pipeline()
                pipe.get(f"traffic:bytes:{target_ts}")
                pipe.get(f"traffic:packets:{target_ts}")
                pipe.pfcount(f"traffic:active_ips:{target_ts}")
                results = await pipe.execute()
                
                total_bytes = int(results[0] or 0)
                total_packets = int(results[1] or 0)
                active_ips = int(results[2] or 0)
                
                payload = {
                    "timestamp": target_ts * 1000,
                    "throughput_mbps": round((total_bytes * 8) / 1024 / 1024, 2),
                    "throughput_pps": total_packets,
                    "active_ips": active_ips
                }
                await ws.send_json(payload)
                
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket 异常断开: {e}")