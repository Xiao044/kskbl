import redis.asyncio as redis
import clickhouse_connect
from core.config import REDIS_URL, CLICKHOUSE_HOST, CLICKHOUSE_PORT, CLICKHOUSE_DB

class DatabaseManager:
    def __init__(self):
        self.redis_client = None
        self.ch_client = None

    async def connect_redis(self):
        """初始化异步 Redis 连接池"""
        self.redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        print("Redis 连接池初始化完成")

    def connect_clickhouse(self):
        """初始化 ClickHouse 连接"""
        try:
            self.ch_client = clickhouse_connect.get_client(
                host=CLICKHOUSE_HOST,
                port=CLICKHOUSE_PORT,
                database=CLICKHOUSE_DB
            )
            print("ClickHouse 连接成功")
        except Exception as e:
            print(f"ClickHouse 连接失败，请确保数据库已启动: {e}")

    async def close(self):
        """安全关闭连接"""
        if self.redis_client:
            await self.redis_client.close()

# 导出单例对象供全局使用
db_manager = DatabaseManager()