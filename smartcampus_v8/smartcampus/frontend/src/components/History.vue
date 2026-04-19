<template>
  <div class="history-container">
    <div class="filter-card">
      <div class="search-group">
        <div class="input-with-icon">
          <span class="search-icon">🔍</span>
          <input 
            v-model="searchQuery" 
            type="text" 
            placeholder="搜索源/目的 IP..." 
            @input="handleSearch"
          />
        </div>
      </div>
      
      <div class="filter-group">
        <span v-if="historyZoneSeed" class="zone-filter-chip" :title="`当前按区域筛选: ${historyZoneSeed}`">
          区域: {{ historyZoneSeed }}
        </span>
        <select v-model="filterProto">
          <option value="all">所有协议</option>
          <option value="HTTP">HTTP/HTTPS</option>
          <option value="SSH">SSH</option>
          <option value="DNS">DNS</option>
          <option value="Unknown">未知</option>
        </select>

        <select v-model="filterLevel">
          <option value="all">所有状态</option>
          <option value="normal">正常流量</option>
          <option value="warning">可疑流量</option>
          <option value="danger">安全告警</option>
        </select>

        <button class="btn-export ui-action-btn ui-action-btn--danger" @click="clearHistory">
          <span class="icon">🗑️</span> 清空记录
        </button>
      </div>
    </div>

    <div class="table-card">
      <div class="table-header">
        <h3 class="title">动态流记录审计 (本地缓存模式)</h3>
        <span class="count">当前已捕获 {{ filteredLogs.length }} 条记录 (最大缓存 1000 条)</span>
      </div>

      <div class="table-wrapper ui-table-scroll">
        <table v-if="filteredLogs.length > 0" class="ui-data-table">
          <thead>
            <tr>
              <th>捕获时间</th>
              <th>流量链路 (Source ➔ Destination)</th>
              <th>源区域</th>
              <th>主要协议</th>
              <th>载荷大小 (KB)</th>
              <th>状态标识</th>
              <th>包数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in paginatedLogs" :key="log.aggregateKey">
              <td class="time-col">{{ log.time }}</td>
              <td>
                <div class="path-col">
                  <button class="ip ip-link ui-ip-link" type="button" @click="$emit('view-ip', log.src_ip)">{{ log.src_ip }}</button>
                  <span v-if="log.count > 1" class="count-badge" :title="`累计攻击 ${log.count} 次`">x{{ log.count }}</span>
                  <span class="arrow">➔</span>
                  <button class="ip ip-link ui-ip-link" type="button" @click="$emit('view-ip', log.dst_ip)">{{ log.dst_ip }}</button>
                </div>
              </td>
              <td><span class="zone-tag-hist ui-pill-tag ui-pill-tag--blue">{{ log.src_zone || '--' }}</span></td>
              <td><span class="proto-tag">{{ log.proto }}</span></td>
              <td class="data-col">{{ log.size }}</td>
              <td>
                <span :class="['status-badge', 'ui-status-badge', `ui-status-badge--${log.level}` , log.level]">
                  <span class="status-dot ui-status-badge__dot"></span>
                  <span class="status-label">{{ log.status }}</span>
                </span>
              </td>
              <td class="data-col">{{ log.packets }}</td>
            </tr>
          </tbody>
        </table>

        <div v-else class="empty-placeholder">
          <div class="empty-icon">📡</div>
          <p>正在监听网络接口，暂无匹配的历史记录...</p>
        </div>
      </div>

      <div class="pagination">
        <button @click="currentPage--" :disabled="currentPage <= 1">上一页</button>
        <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
        <button @click="currentPage++" :disabled="currentPage >= totalPages">下一页</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'History',
  emits: ['view-ip'],
  // 接收 App.vue 传过来的实时数据
  props: {
    flow: { type: Array, default: () => [] },
    alerts: { type: Array, default: () => [] },
    historySearchSeed: { type: String, default: '' },
    historyFocusToken: { type: Number, default: 0 },
    historyZoneSeed: { type: String, default: '' }
  },
  data() {
    return {
      searchQuery: '',
      filterProto: 'all',
      filterLevel: 'all',
      currentPage: 1,
      pageSize: 12,
      historyLogs: [], // 真正用来存数据的本地数组
      lastAlertUid: 0
    }
  },
  watch: {
    // 监听正常流量，累加到历史记录中
    flow: {
      handler(newFlow) {
        if (!newFlow || newFlow.length === 0) return;
        
        const now = new Date().toLocaleTimeString('zh-CN', { hour12: false });
        
        // 我们只取当前 1 秒内流量最大的前 3 个链路存入历史，防止数据量爆炸
        const topFlows = newFlow.slice(0, 3).map(item => ({
          time: now,
          src_ip: item.src_ip,
          dst_ip: item.dst_ip,
          src_zone: item.src_zone || '外部网络',
          proto: item.protocols[0] || 'Unknown',
          size: (item.bytes / 1024).toFixed(2),
          packets: item.packets,
          level: 'normal',
          status: '常规放行'
        }));

        // 把新数据插到数组最前面
        this.historyLogs.unshift(...topFlows);
        this.limitHistorySize();
      }
    },
    // 监听告警数据，累加到历史记录中，并标记为红色危险
    alerts: {
      handler(newAlerts) {
        if (!newAlerts || newAlerts.length === 0) return;

        const freshAlerts = newAlerts.filter(item => (item._uid || 0) > this.lastAlertUid);
        if (freshAlerts.length === 0) return;

        this.lastAlertUid = freshAlerts[freshAlerts.length - 1]._uid || this.lastAlertUid;

        const alertLogs = freshAlerts.map(item => ({
          time: item.time,
          src_ip: item.src_ip,
          dst_ip: item.dst_ip || 'N/A',
          src_zone: item.src_zone || '外部网络',
          proto: item.category || 'Threat',
          size: item.bytes ? (item.bytes / 1024).toFixed(2) : '---',
          packets: item.packets || '---',
          level: item.level === 'high' ? 'danger' : 'warning',
          status: item.type,
          count: Number(item.count || 1)
        }));

        this.historyLogs.unshift(...alertLogs);
        this.limitHistorySize();
      }
    },
    historyFocusToken: {
      handler() {
        this.applyHistorySearchSeed();
      }
    }
  },
  computed: {
    aggregatedAlerts() {
      const alertMap = new Map();
      const normalLogs = [];

      this.historyLogs.forEach((log, index) => {
        if (log.level === 'normal') {
          normalLogs.push({
            ...log,
            count: Number(log.count || 1),
            aggregateKey: `${log.src_ip}__${log.dst_ip}__${log.time}__${index}`
          });
          return;
        }

        const key = `${log.src_ip}__${log.status}`;
        const existing = alertMap.get(key);
        const count = Number(log.count || 1);
        const bytes = log.size === '---' ? 0 : Number(log.size || 0);
        const packets = log.packets === '---' ? 0 : Number(log.packets || 0);

        if (existing) {
          existing.count += count;
          existing.sizeValue += bytes;
          existing.packetValue += packets;
          if (String(log.time) >= String(existing.time)) {
            existing.time = log.time;
            existing.dst_ip = log.dst_ip;
            existing.src_zone = log.src_zone;
            existing.proto = log.proto;
            existing.status = log.status;
            existing.level = log.level;
          }
          existing.size = existing.sizeValue > 0 ? existing.sizeValue.toFixed(2) : '---';
          existing.packets = existing.packetValue > 0 ? existing.packetValue : '---';
          return;
        }

        alertMap.set(key, {
          ...log,
          count,
          sizeValue: bytes,
          packetValue: packets,
          size: bytes > 0 ? bytes.toFixed(2) : '---',
          packets: packets > 0 ? packets : '---',
          aggregateKey: key
        });
      });

      return [...normalLogs, ...Array.from(alertMap.values())]
        .sort((a, b) => String(b.time).localeCompare(String(a.time)));
    },
    filteredLogs() {
      return this.aggregatedAlerts.filter(log => {
        const matchSearch = log.src_ip.includes(this.searchQuery) || log.dst_ip.includes(this.searchQuery);
        const matchProto = this.filterProto === 'all' || log.proto.includes(this.filterProto);
        const matchLevel = this.filterLevel === 'all' || log.level === this.filterLevel;
        const matchZone = !this.historyZoneSeed || (log.src_zone || '').includes(this.historyZoneSeed);
        return matchSearch && matchProto && matchLevel && matchZone;
      });
    },
    totalPages() {
      return Math.ceil(this.filteredLogs.length / this.pageSize) || 1;
    },
    paginatedLogs() {
      const start = (this.currentPage - 1) * this.pageSize;
      return this.filteredLogs.slice(start, start + this.pageSize);
    }
  },
  methods: {
    applyHistorySearchSeed() {
      const nextValue = String(this.historySearchSeed || '').trim();
      this.searchQuery = nextValue;
      this.currentPage = 1;
    },
    handleSearch() {
      this.currentPage = 1;
    },
    clearHistory() {
      this.historyLogs = [];
      this.currentPage = 1;
      this.lastAlertUid = this.alerts.length
        ? Math.max(...this.alerts.map(item => item._uid || 0))
        : 0;
    },
    limitHistorySize() {
      // 限制最大缓存 1000 条，防止浏览器内存溢出崩溃
      if (this.historyLogs.length > 1000) {
        this.historyLogs = this.historyLogs.slice(0, 1000);
      }
    }
  },
  mounted() {
    this.applyHistorySearchSeed();
  }
}
</script>

<style scoped>
.history-container { display: flex; flex-direction: column; gap: 20px; height: 100%; padding: 10px; box-sizing: border-box; }

.filter-card { background: var(--glass-bg, rgba(255,255,255,0.55)); backdrop-filter: var(--glass-blur, blur(12px)); -webkit-backdrop-filter: var(--glass-blur, blur(12px)); padding: 20px; border-radius: 24px; display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); flex-shrink: 0; transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.filter-card:hover { transform: translateY(-2px); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)), 0 12px 28px rgba(0,0,0,0.08); }
.input-with-icon { position: relative; width: 300px; }
.search-icon { position: absolute; left: 12px; top: 10px; color: var(--clay-text-muted, #9f9b93); }
input { width: 100%; padding: 10px 10px 10px 35px; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); border-radius: 12px; outline: none; box-sizing: border-box; background: rgba(255,255,255,0.6); color: #000000; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); transition: all 0.25s ease; }
input:focus { border-color: rgba(67, 8, 159, 0.3); box-shadow: 0 0 0 3px rgba(193, 176, 255, 0.28); }

.filter-group { display: flex; gap: 12px; }
.zone-filter-chip { display: inline-flex; align-items: center; padding: 8px 14px; border-radius: 999px; background: rgba(243, 238, 255, 0.88); border: 1px solid rgba(193, 176, 255, 0.42); color: var(--clay-ube, #43089f); font-size: 12px; font-weight: 800; white-space: nowrap; }
select { padding: 8px 16px; border-radius: 12px; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); background: rgba(255,255,255,0.6); color: #000000; outline: none; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); transition: all 0.25s ease; }
select:focus { border-color: rgba(67, 8, 159, 0.3); box-shadow: 0 0 0 3px rgba(193, 176, 255, 0.22); }

/* Clay 标志性 Hover 按钮 */
.table-card { background: var(--glass-bg, rgba(255,255,255,0.55)); backdrop-filter: var(--glass-blur, blur(12px)); -webkit-backdrop-filter: var(--glass-blur, blur(12px)); border-radius: 24px; flex: 1; display: flex; flex-direction: column; overflow: hidden; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); min-height: 0; transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.table-card:hover { transform: translateY(-2px); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)), 0 12px 28px rgba(0,0,0,0.08); }
.table-header { padding: 20px; border-bottom: 1px dashed var(--clay-border, #dad4c8); display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.title { margin: 0; font-size: 18px; color: #000000; font-weight: 600; letter-spacing: -0.36px; }
.count { font-size: 13px; color: var(--clay-text-muted, #9f9b93); font-weight: 600; }

.table-wrapper {}
.ui-data-table th { background: rgba(250, 249, 247, 0.8); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); padding: 15px 20px; font-size: 13px; color: var(--clay-text-muted, #9f9b93); font-weight: 600; border-bottom: 1px solid var(--clay-border, #dad4c8); }
.ui-data-table td { padding: 15px 20px; border-bottom: 1px solid var(--clay-border-light, #eee9df); font-size: 14px; color: #000000; }
.time-col { color: var(--clay-text-muted, #9f9b93); font-family: 'Space Mono', monospace; font-size: 13px; }
.path-col { display: flex; align-items: center; gap: 10px; font-weight: 600; min-width: 0; }
.ip { font-family: 'Space Mono', monospace; }
.arrow { color: var(--clay-border, #dad4c8); }
.proto-tag { padding: 4px 10px; background: #f0f8ff; color: var(--clay-blueberry, #01418d); border-radius: 999px; font-size: 12px; font-weight: 700; border: 1px solid var(--clay-border-light, #eee9df); }
.data-col { font-family: 'Space Mono', monospace; color: var(--clay-text-secondary, #55534e); font-size: 13px; }
.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 22px;
  padding: 0 10px;
  border-radius: 999px;
  background: linear-gradient(180deg, #ff7f8f 0%, #fc7981 100%);
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.02em;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.35), 0 2px 0 rgba(180, 46, 63, 0.9);
}

.status-label {
  position: relative;
  z-index: 1;
}
.empty-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--clay-text-muted, #9f9b93); }
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }

.pagination { padding: 15px; display: flex; justify-content: center; align-items: center; gap: 20px; border-top: 1px dashed var(--clay-border, #dad4c8); flex-shrink: 0; background: rgba(255,255,255,0.18); }
.pagination button { padding: 6px 15px; border-radius: 12px; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); background: rgba(255,255,255,0.6); cursor: pointer; color: #000000; font-weight: 600; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); }
.pagination button:hover:not(:disabled) { transform: rotateZ(-8deg) translateY(-2px); box-shadow: rgb(0,0,0) -7px 7px; background-color: var(--clay-ube-light, #c1b0ff); color: var(--clay-ube, #43089f); border-color: var(--clay-ube-light, #c1b0ff); }
.pagination button:disabled { opacity: 0.5; cursor: not-allowed; background: #ffffff; color: var(--clay-text-muted, #9f9b93); }
.page-info { font-size: 13px; color: var(--clay-text-muted, #9f9b93); font-weight: 600; }
</style>
