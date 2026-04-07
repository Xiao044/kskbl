from fastapi import APIRouter
import time
from db.database import db_manager
from models.schemas import FlowSearchQuery

router = APIRouter()

@router.get("/topk")
async def get_topk(limit: int = 5):
    """从 Redis 读取 Top-K"""
    if not db_manager.redis_client: 
        return {"top_ips": []}
        
    current_ts = int(time.time()) - 1 
    top_ips = await db_manager.redis_client.zrevrange(f"traffic:topk:{current_ts}", 0, limit - 1, withscores=True)
    return {"top_ips": [{"ip": ip, "bytes": int(score)} for ip, score in top_ips]}

@router.get("/regions")
async def get_region_traffic():
    """从 ClickHouse 查询区域聚合"""
    if not db_manager.ch_client: 
        return {}
        
    query = """
        SELECT region, sum(bytes) as total_bytes, sum(packets) as total_packets 
        FROM network_flows 
        WHERE timestamp >= (now() - INTERVAL 5 MINUTE)
        GROUP BY region
    """
    result = db_manager.ch_client.query(query)
    return {row[0]: {"bytes": row[1], "packets": row[2]} for row in result.result_rows}

@router.post("/search")
async def search_flows(query: FlowSearchQuery):
    """微观流级检索"""
    if not db_manager.ch_client: 
        return {"data": []}
    
    where_clauses = ["1=1"]
    parameters = {}
    
    if query.src_ip:
        where_clauses.append("src_ip = %(src_ip)s")
        parameters["src_ip"] = query.src_ip
    if query.protocol:
        where_clauses.append("protocol = %(protocol)s")
        parameters["protocol"] = query.protocol
        
    where_sql = " AND ".join(where_clauses)
    sql = f"SELECT * FROM network_flows WHERE {where_sql} ORDER BY timestamp DESC LIMIT %(limit)s"
    
    result = db_manager.ch_client.query(sql, parameters={"limit": query.limit, **parameters})
    columns = result.column_names
    data = [dict(zip(columns, row)) for row in result.result_rows]
    return {"total": len(data), "data": data}