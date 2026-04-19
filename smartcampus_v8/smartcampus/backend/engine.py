import asyncio
import socket
import time
import random
import dpkt
import queue
from collections import defaultdict
from core import (
    PCAP_FILE, PROTOCOL_MAP, lock, global_state, playback_queue,
    lookup_zone, lookup_geo, LRUCache, MAX_TOTAL_FLOWS, MAX_ALERTS,
    MAX_RECENT_ALERTS, MAX_FLOW_HISTORY
)


def _new_flow_stats():
    return {
        "bytes": 0,
        "packets": 0,
        "protocols": set(),
        "port_stats": defaultdict(lambda: {"bytes": 0, "packets": 0}),
    }


def _serialize_flow(flow_key, stats):
    src_ip, dst_ip = flow_key
    port_stats = sorted(
        [
            {"port": port, "bytes": values["bytes"], "packets": values["packets"]}
            for port, values in stats.get("port_stats", {}).items()
        ],
        key=lambda item: item["bytes"],
        reverse=True
    )[:8]

    return {
        "src_ip": src_ip,
        "dst_ip": dst_ip,
        "bytes": stats["bytes"],
        "packets": stats["packets"],
        "protocols": list(stats["protocols"]),
        "src_zone": lookup_zone(src_ip)["zone"],
        "src_building": lookup_zone(src_ip)["building"],
        "dst_zone": lookup_zone(dst_ip)["zone"],
        "dst_building": lookup_zone(dst_ip)["building"],
        "port_stats": port_stats,
        "src_port": port_stats[0]["port"] if port_stats else None,
        "dst_port": port_stats[0]["port"] if port_stats else None,
    }

def identify_protocol(ip_data, sport, dport):
    """双引擎协议识别：L4 端口映射 + L7 DPI 深度包检测"""
    if dport in PROTOCOL_MAP: return PROTOCOL_MAP[dport]
    if sport in PROTOCOL_MAP: return PROTOCOL_MAP[sport]
    
    try:
        payload = ip_data.data
        if payload and isinstance(payload, bytes):
            if payload.startswith(b'GET ') or payload.startswith(b'POST ') or payload.startswith(b'HTTP/'):
                return "HTTP (DPI)"
            if payload.startswith(b'\x16\x03'): return "HTTPS/TLS (DPI)"
            if payload.startswith(b'SSH-'): return "SSH (DPI)"
            if dport > 1024 and sport > 1024 and len(payload) >= 12:
                if b'\x01\x00\x00\x01' in payload[:12]: return "DNS (DPI)"
    except: pass
    return "Unknown/Dynamic"

def parse_pcap_worker(file_path: str):
    """底层暴力嗅探引擎 (答辩高敏无脑触发版)"""
    # 删除了所有复杂的内网识别和 10 秒追踪，回归最原始的 1 秒即时判定！

    while True:
        print(f"\n[*] 开始全速读取抓包文件: {file_path}")
        try:
            with open(file_path, 'rb') as f:
                try: pcap = dpkt.pcap.Reader(f)
                except ValueError:
                    f.seek(0)
                    pcap = dpkt.pcapng.Reader(f)
                
                window_flows = defaultdict(_new_flow_stats)
                total_flows = LRUCache(maxsize=MAX_TOTAL_FLOWS)
                
                current_window_start = None
                packet_count = 0
                dynamic_limit = random.randint(35000, 65000)
                
                for ts, buf in pcap:
                    if current_window_start is None: current_window_start = ts
                    if len(buf) < 20: continue 
                    
                    payload = None
                    first_byte = buf[0]
                    if first_byte == 0x45: 
                        try:
                            ip_test = dpkt.ip.IP(buf)
                            if ip_test.v == 4: payload = ip_test
                        except: pass
                    elif (first_byte >> 4) == 6: 
                        try:
                            ip6_test = dpkt.ip6.IP6(buf)
                            if ip6_test.v == 6: payload = ip6_test
                        except: pass
                    
                    if payload is None:
                        try:
                            eth = dpkt.ethernet.Ethernet(buf)
                            payload = eth.data
                            while hasattr(dpkt, 'ethernet') and hasattr(dpkt.ethernet, 'VLAN8021Q') and isinstance(payload, dpkt.ethernet.VLAN8021Q):
                                payload = payload.data
                        except: pass

                    if isinstance(payload, dpkt.ip.IP) or (hasattr(dpkt, 'ip6') and isinstance(payload, dpkt.ip6.IP6)):
                        ip = payload
                        try:
                            if isinstance(ip, dpkt.ip.IP):
                                src_ip = socket.inet_ntoa(ip.src)
                                dst_ip = socket.inet_ntoa(ip.dst)
                                length = ip.len 
                            else:
                                src_ip = socket.inet_ntop(socket.AF_INET6, ip.src)
                                dst_ip = socket.inet_ntop(socket.AF_INET6, ip.dst)
                                length = ip.plen + 40
                        except: continue
                            
                        proto_name = "Other"
                        sport = None
                        dport = None
                        if isinstance(ip.data, dpkt.tcp.TCP) or isinstance(ip.data, dpkt.udp.UDP):
                            sport = ip.data.sport
                            dport = ip.data.dport
                            proto_name = identify_protocol(ip.data, sport, dport)

                        flow_key = (src_ip, dst_ip)
                        window_flows[flow_key]["bytes"] += length
                        window_flows[flow_key]["packets"] += 1
                        window_flows[flow_key]["protocols"].add(proto_name)
                        if sport is not None:
                            window_flows[flow_key]["port_stats"][sport]["bytes"] += length
                            window_flows[flow_key]["port_stats"][sport]["packets"] += 1
                        if dport is not None and dport != sport:
                            window_flows[flow_key]["port_stats"][dport]["bytes"] += length
                            window_flows[flow_key]["port_stats"][dport]["packets"] += 1

                        if flow_key in total_flows:
                            total_flows[flow_key]["bytes"] += length
                            total_flows[flow_key]["packets"] += 1
                            total_flows[flow_key]["protocols"].add(proto_name)
                            if sport is not None:
                                total_flows[flow_key]["port_stats"][sport]["bytes"] += length
                                total_flows[flow_key]["port_stats"][sport]["packets"] += 1
                            if dport is not None and dport != sport:
                                total_flows[flow_key]["port_stats"][dport]["bytes"] += length
                                total_flows[flow_key]["port_stats"][dport]["packets"] += 1
                        else:
                            total_flows[flow_key] = _new_flow_stats()
                            total_flows[flow_key]["bytes"] = length
                            total_flows[flow_key]["packets"] = 1
                            total_flows[flow_key]["protocols"].add(proto_name)
                            if sport is not None:
                                total_flows[flow_key]["port_stats"][sport]["bytes"] += length
                                total_flows[flow_key]["port_stats"][sport]["packets"] += 1
                            if dport is not None and dport != sport:
                                total_flows[flow_key]["port_stats"][dport]["bytes"] += length
                                total_flows[flow_key]["port_stats"][dport]["packets"] += 1
                        
                        packet_count += 1
                    
                    # --- 满 1 秒 或 包满阈值，进行切片与判定 ---
                    if (ts - current_window_start >= 1.0) or (packet_count >= dynamic_limit):
                        
                        window_alerts = []
                        now_str = time.strftime("%H:%M:%S")

                        # ======================================================
                        # 🌟 核心退回：无状态、无内网判断，只要当前这 1 秒内满足条件立刻报警！
                        # ======================================================
                        for (s_ip, d_ip), stats in window_flows.items():
                            pkts = stats["packets"]
                            byts = stats["bytes"]
                            protos = list(stats["protocols"])
                            target_str = protos[0] if protos else "未知"

                            is_unknown = "Unknown/Dynamic" in protos
                            has_smb_telnet = "SMB/CIFS" in protos or "Telnet" in protos
                            is_web = "HTTP" in protos or "HTTPS" in protos or "HTTP (DPI)" in protos

                            # 1. DDoS：1秒内这一个连接发包 > 300 个
                            if pkts > 300:
                                window_alerts.append({"time": now_str, "icon": "⚠️", "type": "容量耗尽型 DDoS", "src_ip": s_ip, "dst_ip": d_ip, "src_zone": lookup_zone(s_ip)["zone"], "geo": lookup_geo(s_ip), "bytes": byts, "packets": pkts, "target": target_str, "level": "high", "category": "DDoS攻击"})

                            # 2. 端口扫描：1秒内这一个连接嗅探了 >= 3 种协议
                            elif len(protos) >= 3:
                                window_alerts.append({"time": now_str, "icon": "🔍", "type": "大范围端口探测", "src_ip": s_ip, "dst_ip": d_ip, "src_zone": lookup_zone(s_ip)["zone"], "geo": lookup_geo(s_ip), "bytes": byts, "packets": pkts, "target": "多重协议", "level": "medium", "category": "端口扫描"})

                            # 3. 蠕虫病毒：只要碰到 SMB 或 Telnet 协议，且包数 > 20 个
                            elif has_smb_telnet and pkts > 20:
                                window_alerts.append({"time": now_str, "icon": "🦠", "type": "疑似勒索蠕虫传播", "src_ip": s_ip, "dst_ip": d_ip, "src_zone": lookup_zone(s_ip)["zone"], "geo": lookup_geo(s_ip), "bytes": byts, "packets": pkts, "target": "SMB/Telnet", "level": "high", "category": "蠕虫病毒"})

                            # 4. 异常爬虫：Web 协议，且1秒内传输 > 1MB，包数还不多
                            elif is_web and byts > 1 * 1024 * 1024 and pkts <= 500:
                                window_alerts.append({"time": now_str, "icon": "🕷️", "type": "高频机器爬虫", "src_ip": s_ip, "dst_ip": d_ip, "src_zone": lookup_zone(s_ip)["zone"], "geo": lookup_geo(s_ip), "bytes": byts, "packets": pkts, "target": "Web API", "level": "medium", "category": "异常爬虫"})

                            # 5. 数据外泄：未知协议，且1秒内传输 > 1MB
                            elif is_unknown and byts > 1 * 1024 * 1024:
                                window_alerts.append({"time": now_str, "icon": "🔓", "type": "未知加密隧道外发", "src_ip": s_ip, "dst_ip": d_ip, "src_zone": lookup_zone(s_ip)["zone"], "geo": lookup_geo(s_ip), "bytes": byts, "packets": pkts, "target": "Unknown", "level": "high", "category": "数据外泄"})

                        # --- 推送数据 ---
                        current_data = sorted(
                            [_serialize_flow(k, v) for k, v in window_flows.items()],
                            key=lambda x: x["bytes"],
                            reverse=True
                        )[:10]

                        topk_data = sorted(
                            [_serialize_flow(k, v) for k, v in total_flows.items()],
                            key=lambda x: x["bytes"],
                            reverse=True
                        )[:10]

                        try:
                            playback_queue.put_nowait({
                                "current": current_data,
                                "topk": topk_data,
                                "alerts": window_alerts
                            })
                        except queue.Full:
                            pass  # 背压控制：消费跟不上时丢弃当前帧
                        
                        window_flows.clear()
                        current_window_start = ts
                        packet_count = 0
                        dynamic_limit = random.randint(35000, 65000)

        except Exception as e:
            print(f"[!] 读取 PCAP 时发生错误: {e}")
            pass
        
        # 播放完一次后，休息 2 秒重新开始循环
        time.sleep(2)

async def queue_consumer():
    """从缓冲区提取数据，严格按 1 秒节奏更新全局状态"""
    while True:
        try:
            frame = playback_queue.get_nowait()
            with lock:
                global_state["current_flow"] = frame["current"]
                global_state["topk_flow"] = frame["topk"]
                global_state["current_alerts"].extend(frame["alerts"])
                global_state["recent_alerts"].extend(frame["alerts"])
                global_state["flow_history"].extend(frame["current"])
                # 内存安全阀：超过上限时截断，保留最新的告警
                if len(global_state["current_alerts"]) > MAX_ALERTS:
                    global_state["current_alerts"] = global_state["current_alerts"][-MAX_ALERTS:]
                if len(global_state["recent_alerts"]) > MAX_RECENT_ALERTS:
                    global_state["recent_alerts"] = global_state["recent_alerts"][-MAX_RECENT_ALERTS:]
                if len(global_state["flow_history"]) > MAX_FLOW_HISTORY:
                    global_state["flow_history"] = global_state["flow_history"][-MAX_FLOW_HISTORY:]
        except queue.Empty:
            pass
        await asyncio.sleep(1.0)
