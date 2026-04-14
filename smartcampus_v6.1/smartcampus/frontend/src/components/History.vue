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

        <button class="btn-export" @click="clearHistory">
          <span class="icon">🗑️</span> 清空记录
        </button>
      </div>
    </div>

    <div class="table-card">
      <div class="table-header">
        <h3 class="title">动态流记录审计 (本地缓存模式)</h3>
        <span class="count">当前已捕获 {{ filteredLogs.length }} 条记录 (最大缓存 1000 条)</span>
      </div>

      <div class="table-wrapper">
        <table v-if="filteredLogs.length > 0">
          <thead>
            <tr>
              <th>捕获时间</th>
              <th>流量链路 (Source ➔ Destination)</th>
              <th>主要协议</th>
              <th>载荷大小 (KB)</th>
              <th>状态标识</th>
              <th>包数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(log, index) in paginatedLogs" :key="index">
              <td class="time-col">{{ log.time }}</td>
              <td class="path-col">
                <span class="ip">{{ log.src_ip }}</span>
                <span class="arrow">➔</span>
                <span class="ip">{{ log.dst_ip }}</span>
              </td>
              <td><span class="proto-tag">{{ log.proto }}</span></td>
              <td class="data-col">{{ log.size }}</td>
              <td>
                <span :class="['status-dot', log.level]"></span>
                <span :class="['status-text', log.level]">{{ log.status }}</span>
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
  // 接收 App.vue 传过来的实时数据
  props: {
    flow: { type: Array, default: () => [] },
    alerts: { type: Array, default: () => [] }
  },
  data() {
    return {
      searchQuery: '',
      filterProto: 'all',
      filterLevel: 'all',
      currentPage: 1,
      pageSize: 12,
      historyLogs: [] // 真正用来存数据的本地数组
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
          proto: item.protocols[0] || 'Unknown',
          size: (item.bytes / 1024).toFixed(2),
          packets: item.packets,
          level: 'normal',
          status: '常规放行'
        }));

        // 把新数据插到数组最前面
        this.historyLogs.unshift(...topFlows);
        this.limitHistorySize();
      },
      deep: true
    },
    // 监听告警数据，累加到历史记录中，并标记为红色危险
    alerts: {
      handler(newAlerts) {
        if (!newAlerts || newAlerts.length === 0) return;
        
        const alertLogs = newAlerts.map(item => ({
          time: item.time,
          src_ip: item.src_ip,
          dst_ip: item.target || 'N/A',
          proto: item.category || 'Threat',
          size: '---',
          packets: '---',
          level: item.level === 'high' ? 'danger' : 'warning',
          status: item.type
        }));

        this.historyLogs.unshift(...alertLogs);
        this.limitHistorySize();
      },
      deep: true
    }
  },
  computed: {
    filteredLogs() {
      return this.historyLogs.filter(log => {
        const matchSearch = log.src_ip.includes(this.searchQuery) || log.dst_ip.includes(this.searchQuery);
        const matchProto = this.filterProto === 'all' || log.proto.includes(this.filterProto);
        const matchLevel = this.filterLevel === 'all' || log.level === this.filterLevel;
        return matchSearch && matchProto && matchLevel;
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
    handleSearch() {
      this.currentPage = 1;
    },
    clearHistory() {
      this.historyLogs = [];
      this.currentPage = 1;
    },
    limitHistorySize() {
      // 限制最大缓存 1000 条，防止浏览器内存溢出崩溃
      if (this.historyLogs.length > 1000) {
        this.historyLogs = this.historyLogs.slice(0, 1000);
      }
    }
  }
}
</script>

<style scoped>
.history-container { display: flex; flex-direction: column; gap: 20px; height: 100%; padding: 10px; box-sizing: border-box; }

.filter-card { background: #ffffff; padding: 20px; border-radius: 24px; display: flex; justify-content: space-between; align-items: center; border: 1px solid var(--clay-border, #dad4c8); box-shadow: var(--clay-shadow, rgba(0,0,0,0.1) 0px 1px 1px, rgba(0,0,0,0.04) 0px -1px 1px inset, rgba(0,0,0,0.05) 0px -0.5px 1px); flex-shrink: 0; }
.input-with-icon { position: relative; width: 300px; }
.search-icon { position: absolute; left: 12px; top: 10px; color: var(--clay-text-muted, #9f9b93); }
input { width: 100%; padding: 10px 10px 10px 35px; border: 1px solid var(--clay-border, #dad4c8); border-radius: 12px; outline: none; box-sizing: border-box; background: #ffffff; color: #000000; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); }
input:focus { border-color: var(--clay-ube, #43089f); box-shadow: rgb(20, 110, 245) solid 2px; }

.filter-group { display: flex; gap: 12px; }
select { padding: 8px 16px; border-radius: 12px; border: 1px solid var(--clay-border, #dad4c8); background: #ffffff; color: #000000; outline: none; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); }

/* Clay 标志性 Hover 按钮 */
.btn-export { padding: 8px 20px; background: #ffffff; color: var(--clay-pomegranate, #fc7981); border: 1px solid var(--clay-border, #dad4c8); border-radius: 12px; font-weight: 600; cursor: pointer; transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); }
.btn-export:hover { transform: rotateZ(-8deg) translateY(-2px); box-shadow: rgb(0,0,0) -7px 7px; background-color: var(--clay-lemon, #fbbd41); color: #ffffff; border-color: var(--clay-lemon, #fbbd41); }

.table-card { background: #ffffff; border-radius: 24px; flex: 1; display: flex; flex-direction: column; overflow: hidden; border: 1px solid var(--clay-border, #dad4c8); box-shadow: var(--clay-shadow, rgba(0,0,0,0.1) 0px 1px 1px, rgba(0,0,0,0.04) 0px -1px 1px inset, rgba(0,0,0,0.05) 0px -0.5px 1px); min-height: 0; }
.table-header { padding: 20px; border-bottom: 1px dashed var(--clay-border, #dad4c8); display: flex; justify-content: space-between; align-items: center; flex-shrink: 0; }
.title { margin: 0; font-size: 18px; color: #000000; font-weight: 600; letter-spacing: -0.36px; }
.count { font-size: 13px; color: var(--clay-text-muted, #9f9b93); font-weight: 600; }

.table-wrapper { flex: 1; overflow-y: auto; }
table { width: 100%; border-collapse: collapse; }
th { background: var(--clay-bg, #faf9f7); text-align: left; padding: 15px 20px; font-size: 13px; color: var(--clay-text-muted, #9f9b93); font-weight: 600; border-bottom: 1px solid var(--clay-border, #dad4c8); position: sticky; top: 0; z-index: 10; }
td { padding: 15px 20px; border-bottom: 1px solid var(--clay-border-light, #eee9df); font-size: 14px; color: #000000; }

.time-col { color: var(--clay-text-muted, #9f9b93); font-family: 'Space Mono', monospace; font-size: 13px; }
.path-col { display: flex; align-items: center; gap: 10px; font-weight: 600; }
.ip { font-family: 'Space Mono', monospace; }
.arrow { color: var(--clay-border, #dad4c8); }
.proto-tag { padding: 4px 10px; background: #f0f8ff; color: var(--clay-blueberry, #01418d); border-radius: 999px; font-size: 12px; font-weight: 700; border: 1px solid var(--clay-border-light, #eee9df); }
.data-col { font-family: 'Space Mono', monospace; color: var(--clay-text-secondary, #55534e); font-size: 13px; }

.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
.normal { background: var(--clay-matcha, #078a52); color: var(--clay-matcha, #078a52); }
.warning { background: var(--clay-lemon, #fbbd41); color: var(--clay-lemon, #fbbd41); }
.danger { background: var(--clay-pomegranate, #fc7981); color: var(--clay-pomegranate, #fc7981); }

.empty-placeholder { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: var(--clay-text-muted, #9f9b93); }
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; }

.pagination { padding: 15px; display: flex; justify-content: center; align-items: center; gap: 20px; border-top: 1px dashed var(--clay-border, #dad4c8); flex-shrink: 0; }
.pagination button { padding: 6px 15px; border-radius: 12px; border: 1px solid var(--clay-border, #dad4c8); background: #ffffff; cursor: pointer; color: #000000; font-weight: 600; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); }
.pagination button:hover:not(:disabled) { transform: rotateZ(-8deg) translateY(-2px); box-shadow: rgb(0,0,0) -7px 7px; background-color: var(--clay-ube-light, #c1b0ff); color: var(--clay-ube, #43089f); border-color: var(--clay-ube-light, #c1b0ff); }
.pagination button:disabled { opacity: 0.5; cursor: not-allowed; background: #ffffff; color: var(--clay-text-muted, #9f9b93); }
.page-info { font-size: 13px; color: var(--clay-text-muted, #9f9b93); font-weight: 600; }
</style>