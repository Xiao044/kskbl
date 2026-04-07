import asyncio
import time
import random
from core.config import PROTOCOLS, REGIONS
from db.database import db_manager

def generate_mock_flow(current_ts):
    """生成单条流数据"""
    return {
        "timestamp": current_ts,
        "flow_id": f"flow_{random.randint(10000, 99999)}",
        "src_ip": f"10.1.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "dst_ip": f"10.2.{random.randint(1, 255)}.{random.randint(1, 255)}",
        "src_port": random.randint(1024, 65535),
        "dst_port": random.choice([80, 443, 22, 53, 143]),
        "protocol": random.choice(PROTOCOLS),
        "region": random.choice(REGIONS),
        "bytes": random.randint(500, 50000),
        "packets": random.randint(10, 500)
    }

async def data_ingestion_pipeline():
    """模拟底层探针，将流量高速写入 Redis 和 ClickHouse"""
    while True:
        current_ts = int(time.time())
        flows = [generate_mock_flow(current_ts) for _ in range(random.randint(100, 300))]
        
        # 1. Redis 高频聚合写入 (Pipeline)
        if db_manager.redis_client:
            pipe = db_manager.redis_client.pipeline()
            for flow in flows:
                pipe.incrby(f"traffic:bytes:{current_ts}", flow["bytes"])
                pipe.incrby(f"traffic:packets:{current_ts}", flow["packets"])
                pipe.pfadd(f"traffic:active_ips:{current_ts}", flow["src_ip"], flow["dst_ip"])
                pipe.zincrby(f"traffic:topk:{current_ts}", flow["bytes"], flow["src_ip"])
            
            # 设置过期时间
            pipe.expire(f"traffic:bytes:{current_ts}", 60)
            pipe.expire(f"traffic:packets:{current_ts}", 60)
            pipe.expire(f"traffic:active_ips:{current_ts}", 60)
            pipe.expire(f"traffic:topk:{current_ts}", 60)
            await pipe.execute()

        # 2. ClickHouse 明细批量写入
        if db_manager.ch_client:
            column_names = ["timestamp", "flow_id", "src_ip", "dst_ip", "src_port", "dst_port", "protocol", "region", "bytes", "packets"]
            data_rows = [[f[col] for col in column_names] for f in flows]
            try:
                db_manager.ch_client.insert('network_flows', data_rows, column_names=column_names)
            except Exception as e:
                pass 
                
        await asyncio.sleep(1)