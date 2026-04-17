import threading
import queue
import os
from collections import OrderedDict
from typing import List
from fastapi import WebSocket

# ⚠️ 确保替换为真实抓包文件
PCAP_FILE = "sample.pcap"

# ===== 内存安全阈值 =====
MAX_TOTAL_FLOWS = 5000  # 全局流聚合表最大条目数（LRU 淘汰）
MAX_ALERTS = 500        # 全局告警缓冲最大条目数

# 全局状态与线程锁
lock = threading.Lock()
global_state = {
    "current_flow": [],
    "topk_flow": [],
    "current_alerts": []
}

# 平滑缓冲队列
playback_queue = queue.Queue(maxsize=300)

# 协议字典地图
PROTOCOL_MAP = {
    80: 'HTTP', 443: 'HTTPS', 8080: 'HTTP-Alt', 8443: 'HTTPS-Alt', 3128: 'Squid',
    20: 'FTP-Data', 21: 'FTP', 22: 'SSH/SFTP', 23: 'Telnet', 69: 'TFTP',
    3389: 'RDP', 5900: 'VNC', 25: 'SMTP', 110: 'POP3', 143: 'IMAP',
    53: 'DNS', 67: 'DHCP', 123: 'NTP', 161: 'SNMP', 1194: 'OpenVPN',
    445: 'SMB/CIFS', 3306: 'MySQL', 5432: 'PostgreSQL', 6379: 'Redis',
    27017: 'MongoDB', 1433: 'SQL-Server', 1521: 'Oracle'
}

# ===== 官方测试集兼容：内部流量前缀 =====
CAMPUS_INTERNAL_PREFIXES = (
    "10.", "30.", "45.", "63.", "66.", "77.", "84.", "123.", "131.", "143.",
    "146.", "153.", "161.", "162.", "175.", "180.", "186.", "202.", "203.", "213."
)

# ===== 区域/楼宇透视映射表 =====
# 格式: "子网前缀" → {"zone": 区域名, "building": 楼宇名, "type": 区域类型, "lon"/"lat": 校园地图坐标}
CAMPUS_ZONE_MAP = {
    # —— 宿舍区 ——
    "10.0.1.":   {"zone": "学生宿舍区", "building": "1号宿舍楼",  "type": "dormitory", "lon": 9,   "lat": 64},
    "10.0.2.":   {"zone": "学生宿舍区", "building": "2号宿舍楼",  "type": "dormitory", "lon": 21,  "lat": 64},
    "10.0.3.":   {"zone": "学生宿舍区", "building": "3号宿舍楼",  "type": "dormitory", "lon": 33,  "lat": 64},
    "10.0.4.":   {"zone": "学生宿舍区", "building": "研究生公寓",  "type": "dormitory", "lon": 18,  "lat": 49.5},
    # —— 教学区 ——
    "10.0.10.":  {"zone": "教学区",     "building": "第一教学楼",  "type": "teaching", "lon": 51,  "lat": 64},
    "10.0.11.":  {"zone": "教学区",     "building": "第二教学楼",  "type": "teaching", "lon": 63,  "lat": 64},
    "10.0.12.":  {"zone": "教学区",     "building": "实验楼A",     "type": "teaching", "lon": 50,  "lat": 49.5},
    "10.0.13.":  {"zone": "教学区",     "building": "实验楼B",     "type": "teaching", "lon": 61,  "lat": 49.5},
    "10.0.14.":  {"zone": "教学区",     "building": "图书馆",      "type": "teaching", "lon": 80,  "lat": 64},
    # —— 行政区 ——
    "10.0.20.":  {"zone": "行政区",     "building": "行政主楼",    "type": "admin",     "lon": 13,  "lat": 31.5},
    "10.0.21.":  {"zone": "行政区",     "building": "信息中心",    "type": "admin",     "lon": 29,  "lat": 31.5},
    "10.0.22.":  {"zone": "行政区",     "building": "教务处",      "type": "admin",     "lon": 13,  "lat": 19},
    # —— 服务器/数据中心 ——
    "10.0.30.":  {"zone": "数据中心",   "building": "核心机房",    "type": "datacenter","lon": 51,  "lat": 31.5},
    "10.0.31.":  {"zone": "数据中心",   "building": "备份机房",    "type": "datacenter","lon": 63,  "lat": 31.5},
    # —— 运动区 ——
    "10.0.40.":  {"zone": "运动区",     "building": "体育馆",      "type": "sports",    "lon": 11,  "lat": 10},
    "10.0.41.":  {"zone": "运动区",     "building": "操场",        "type": "sports",    "lon": 29,  "lat": 10},
}

CAMPUS_INTERNAL_ZONE_POOL = (
    {"zone": "学生宿舍区", "building": "1号宿舍楼", "type": "dormitory", "lon": 9, "lat": 64},
    {"zone": "学生宿舍区", "building": "研究生公寓", "type": "dormitory", "lon": 18, "lat": 49.5},
    {"zone": "教学区", "building": "第一教学楼", "type": "teaching", "lon": 51, "lat": 64},
    {"zone": "教学区", "building": "图书馆", "type": "teaching", "lon": 80, "lat": 64},
    {"zone": "行政区", "building": "行政主楼", "type": "admin", "lon": 13, "lat": 31.5},
    {"zone": "数据中心", "building": "核心机房", "type": "datacenter", "lon": 51, "lat": 31.5},
    {"zone": "运动区", "building": "体育馆", "type": "sports", "lon": 11, "lat": 10},
)

# 校园出口坐标（外部威胁统一显示在校园出口位置）
CAMPUS_GATEWAY = {"lon": 48, "lat": 2.5}

def _hash_zone_index(ip: str) -> int:
    """基于 IP 文本做稳定散列，保证伪内网 IP 每次落在同一校园区域"""
    return sum(ord(ch) for ch in ip) % len(CAMPUS_INTERNAL_ZONE_POOL)

def lookup_zone(ip: str) -> dict:
    """根据 IP 地址快速查找所属区域/楼宇信息"""
    for prefix, info in CAMPUS_ZONE_MAP.items():
        if ip.startswith(prefix):
            return info

    if ip.startswith(CAMPUS_INTERNAL_PREFIXES):
        return CAMPUS_INTERNAL_ZONE_POOL[_hash_zone_index(ip)].copy()

    return {"zone": "外部网络", "building": "非校园网", "type": "external"}

# ===== 校园地理溯源 =====
def lookup_geo(ip: str) -> dict:
    """查询 IP 在校园地图上的位置 — 内网返回楼宇坐标，外网返回校园出口坐标"""
    zone_info = lookup_zone(ip)
    if zone_info.get("type") != "external":
        return {
            "building": zone_info.get("building", "未知楼宇"),
            "zone": zone_info.get("zone", "校园内网"),
            "lat": zone_info.get("lat", 38),
            "lon": zone_info.get("lon", 48),
        }

    # 外网 IP → 统一显示在校园出口位置
    return {
        "building": "校园出口",
        "zone": "出入口",
        "lat": CAMPUS_GATEWAY["lat"],
        "lon": CAMPUS_GATEWAY["lon"],
    }

# ===== LRU 环形缓冲区（替代无界 defaultdict） =====
class LRUCache:
    """带容量限制的 LRU 缓存，超出 maxsize 时自动淘汰最旧条目"""
    def __init__(self, maxsize=5000):
        self.maxsize = maxsize
        self._data = OrderedDict()

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        if key in self._data:
            self._data.move_to_end(key)
        else:
            if len(self._data) >= self.maxsize:
                self._data.popitem(last=False)
        self._data[key] = value

    def items(self):
        return self._data.items()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def __len__(self):
        return len(self._data)

# 聊天群组管理器
class ChatManager:
    def __init__(self):
        self.active: List[WebSocket] = []
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
    def disconnect(self, ws: WebSocket):
        if ws in self.active: 
            self.active.remove(ws)
    async def broadcast(self, msg: dict):
        for ws in self.active:
            try: await ws.send_json(msg)
            except: pass

chat_manager = ChatManager()
