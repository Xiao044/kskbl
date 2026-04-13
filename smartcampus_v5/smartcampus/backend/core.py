import threading
import queue
from typing import List
from fastapi import WebSocket

# ⚠️ 确保替换为真实抓包文件
PCAP_FILE = "sample.pcap"  

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