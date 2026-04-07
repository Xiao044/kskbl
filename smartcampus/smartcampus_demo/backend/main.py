from fastapi import FastAPI, WebSocket, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import random
import time
from typing import List, Optional

app = FastAPI()

# 允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 扩展基础数据模型与模拟数据 ---
# 满足不少于10种应用识别 [cite: 1]
PROTOCOLS = ["HTTP", "HTTPS", "SSH", "DNS", "IMAP", "FTP", "SMTP", "POP3", "RDP", "SNMP"] 
REGIONS = ["宿舍区", "教学区", "行政区", "图书馆", "科研楼"]
# 满足至少4种典型威胁 [cite: 1]
THREAT_TYPES = ["端口扫描", "蠕虫病毒", "DDoS攻击", "钓鱼攻击"] 

def generate_mock_flow():
    """生成符合网络五元组和双维度的细粒度流数据"""
    return {
        "flow_id": f"flow_{random.randint(10000, 99999)}",
        "timestamp": int(time.time() * 1000),
        "src_ip": f"10.1.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "dst_ip": f"10.2.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "src_port": random.randint(1024, 65535),
        "dst_port": random.choice([80, 443, 22, 53, 143]),
        "protocol": random.choice(PROTOCOLS),
        "bytes": random.randint(500, 50000),
        "packets": random.randint(10, 500),
        "region": random.choice(REGIONS)
    }

# 维护一个全局的历史流数据池（模拟数据库暂存）
history_flows = [generate_mock_flow() for _ in range(1000)]

# --- 核心业务 RESTful API ---

@app.get("/api/topk")
async def get_topk(limit: int = 5):
    """返回 Top-K 大流监控 [cite: 1]"""
    sorted_data = sorted(history_flows, key=lambda x: x["bytes"], reverse=True)
    return {"top_ips": sorted_data[:limit]}

@app.get("/api/traffic/regions")
async def get_region_traffic():
    """按区域展示流量差异 [cite: 1]"""
    region_stats = {region: {"bytes": 0, "packets": 0} for region in REGIONS}
    for flow in history_flows[-500:]: # 取最近500条样本统计
        region_stats[flow["region"]]["bytes"] += flow["bytes"]
        region_stats[flow["region"]]["packets"] += flow["packets"]
    return region_stats

@app.get("/api/traffic/protocols")
async def get_protocol_distribution():
    """展示应用协议分布 [cite: 1]"""
    proto_stats = {proto: 0 for proto in PROTOCOLS}
    for flow in history_flows[-500:]:
        proto_stats[flow["protocol"]] += flow["bytes"]
    return proto_stats

@app.get("/api/security/threats")
async def get_threat_logs():
    """生成包含时间、类型、源目IP的安全日志列表 [cite: 1]"""
    logs = []
    for _ in range(random.randint(2, 5)):
        logs.append({
            "timestamp": int(time.time() * 1000) - random.randint(0, 60000),
            "threat_type": random.choice(THREAT_TYPES),
            "src_ip": f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "dst_ip": f"10.0.{random.randint(1, 255)}.{random.randint(1, 255)}",
            "level": random.choice(["HIGH", "CRITICAL"])
        })
    return {"threats": logs}

class FlowSearchQuery(BaseModel):
    src_ip: Optional[str] = None
    dst_ip: Optional[str] = None
    protocol: Optional[str] = None

@app.post("/api/flows/search")
async def search_flows(query: FlowSearchQuery):
    """根据源/目IP、端口、时间范围查询具体的通信流记录 [cite: 1]"""
    results = []
    for flow in history_flows:
        if query.src_ip and query.src_ip not in flow["src_ip"]:
            continue
        if query.dst_ip and query.dst_ip not in flow["dst_ip"]:
            continue
        if query.protocol and flow["protocol"] != query.protocol:
            continue
        results.append(flow)
    return {"total": len(results), "data": results[:50]} # 限制返回条数

# --- WebSocket 实时推送逻辑升级 ---

@app.websocket("/ws/flow")
async def websocket_flow(ws: WebSocket):
    """展示全网实时吞吐量（Mbps/PPS）、活跃IP总数 [cite: 1]"""
    await ws.accept()
    try:
        while True:
            # 1. 生成最新一秒的增量流数据
            new_flows = [generate_mock_flow() for _ in range(random.randint(50, 150))]
            global history_flows
            history_flows = (history_flows + new_flows)[-5000:] # 维持池子大小防内存溢出

            # 2. 实时全景指标计算
            total_bytes = sum(f["bytes"] for f in new_flows)
            total_packets = sum(f["packets"] for f in new_flows)
            active_ips = len(set([f["src_ip"] for f in new_flows] + [f["dst_ip"] for f in new_flows]))
            
            # 3. 构造推送载荷
            payload = {
                "timestamp": int(time.time() * 1000),
                "throughput_mbps": round((total_bytes * 8) / 1024 / 1024, 2), # 转换为 Mbps
                "throughput_pps": total_packets,
                "active_ips": active_ips,
                "latest_flows": new_flows[:5] # 推送部分明细用于前端滚动展示
            }
            await ws.send_json(payload)
            await asyncio.sleep(1)
    except Exception as e:
        print(f"WebSocket Error: {e}")
    finally:
        pass
#wdf
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)