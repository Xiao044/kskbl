<template>
  <div class="history-container">
    <div class="card-box">
      <div class="toolbar">
        <h3 class="box-title">历史流记录检索 (SecLog)</h3>
        <div class="search-box">
          <span class="icon">🔍</span>
          <input type="text" v-model="searchQuery" placeholder="搜索 IP 或 协议..." />
        </div>
      </div>

      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>捕获时间</th>
              <th>源 IP 地址</th>
              <th>流量去向 (目的 IP)</th>
              <th>吞吐量 (Bytes)</th>
              <th>数据包量</th>
              <th>识别协议 (DPI)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in filteredHistory" :key="index">
              <td class="time-col">{{ item.time }}</td>
              <td class="ip-col">{{ item.src_ip }}</td>
              <td class="dst-col">{{ item.dst_ip }}</td>
              <td class="bytes-col">{{ formatBytes(item.bytes) }}</td>
              <td>{{ item.packets }}</td>
              <td>
                <span class="tag" v-for="p in item.protocols" :key="p">{{ p }}</span>
              </td>
            </tr>
            <tr v-if="filteredHistory.length === 0">
              <td colspan="6" class="empty-text">
                <div class="empty-icon">📭</div>
                暂无匹配的历史记录
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'History',
  props: {
    history: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      searchQuery: ''
    }
  },
  computed: {
    filteredHistory() {
      if (!this.searchQuery) return this.history;
      const lowerQ = this.searchQuery.toLowerCase();
      return this.history.filter(item => {
        return (
          item.src_ip.includes(lowerQ) ||
          item.dst_ip.includes(lowerQ) ||
          item.protocols.some(p => p.toLowerCase().includes(lowerQ))
        );
      });
    }
  },
  methods: {
    formatBytes(bytes) {
      if (!bytes || bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
  }
}
</script>

<style scoped>
.history-container { display: flex; flex-direction: column; height: 100%; box-sizing: border-box; }

.card-box { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  background: #ffffff; 
  border-radius: 16px; 
  padding: 24px; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); 
  border: 1px solid #f1f5f9; 
  overflow: hidden; 
}

.toolbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.box-title { margin: 0; color: #1e293b; font-size: 18px; font-weight: 600; }

.search-box { 
  display: flex; 
  align-items: center; 
  background: #f8fafc; 
  border: 1px solid #e2e8f0; 
  border-radius: 20px; 
  padding: 8px 16px; 
  width: 300px;
  transition: all 0.3s;
}
.search-box:focus-within { border-color: #0ea5e9; box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.1); background: #ffffff; }
.search-box .icon { color: #94a3b8; font-size: 14px; }
.search-box input { border: none; background: transparent; outline: none; margin-left: 10px; width: 100%; color: #334155; font-size: 14px; }

/* 表格区域 */
.table-wrapper { flex: 1; overflow-y: auto; padding-right: 8px; }
.table-wrapper::-webkit-scrollbar { width: 6px; }
.table-wrapper::-webkit-scrollbar-track { background: transparent; }
.table-wrapper::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }

table { width: 100%; border-collapse: separate; border-spacing: 0; }
th, td { padding: 16px; text-align: left; font-size: 14px; }
th { 
  color: #64748b; 
  font-weight: 600; 
  position: sticky; 
  top: 0; 
  background: #f8fafc; 
  border-bottom: 2px solid #e2e8f0; 
  border-top: 1px solid #e2e8f0; 
  z-index: 10;
}
th:first-child { border-top-left-radius: 8px; border-bottom-left-radius: 8px; border-left: 1px solid #e2e8f0; }
th:last-child { border-top-right-radius: 8px; border-bottom-right-radius: 8px; border-right: 1px solid #e2e8f0; }

td { border-bottom: 1px solid #f1f5f9; color: #334155; }
tr:hover td { background-color: #f8fafc; }

.time-col { color: #94a3b8; font-family: 'Courier New', Courier, monospace; }
.ip-col { color: #0ea5e9; font-weight: 600; font-family: 'Courier New', Courier, monospace; }
.dst-col { color: #64748b; font-family: 'Courier New', Courier, monospace; }
.bytes-col { font-weight: 600; color: #1e293b; }

.tag { 
  display: inline-block; 
  background: #ecfdf5; 
  color: #059669; 
  padding: 4px 10px; 
  border-radius: 6px; 
  font-size: 12px; 
  margin-right: 6px; 
  border: 1px solid #d1fae5; 
  font-weight: 500;
}

.empty-text { text-align: center; color: #94a3b8; padding: 60px !important; }
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; filter: grayscale(1); }
</style>