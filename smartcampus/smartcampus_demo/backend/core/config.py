import os

# 数据库配置
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "localhost")
CLICKHOUSE_PORT = int(os.getenv("CLICKHOUSE_PORT", 8123))
CLICKHOUSE_DB = os.getenv("CLICKHOUSE_DB", "smart_campus")

# 业务常量
PROTOCOLS = ["HTTP", "HTTPS", "SSH", "DNS", "IMAP", "FTP", "SMTP", "POP3", "RDP", "SNMP"]
REGIONS = ["宿舍区", "教学区", "行政区", "图书馆", "科研楼"]
THREAT_TYPES = ["端口扫描", "蠕虫病毒", "DDoS攻击", "钓鱼攻击"]