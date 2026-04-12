<template>
  <div class="realtime-container">
    <div class="charts-row">
      <div class="card-box chart-card">
        <div class="echarts-inner" ref="trendChart"></div>
      </div>
      <div class="card-box chart-card">
        <div class="echarts-inner" ref="protocolChart"></div>
      </div>
    </div>

    <div class="card-box table-card">
      <div class="table-header">
        <h3 class="box-title">秒级活跃链路监控</h3>
        <div class="live-badge"><span class="pulse-dot"></span> LIVE</div>
      </div>
      
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>源 IP 地址</th>
              <th>流量去向 (目的 IP)</th>
              <th>瞬时吞吐量</th>
              <th>数据包量</th>
              <th>识别应用/协议</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in flow" :key="index">
              <td class="ip-col">{{ item.src_ip }}</td>
              <td class="dst-col">
                <span :class="['status-dot', isInternalIP(item.dst_ip) ? 'dot-safe' : 'dot-warn']"></span>
                {{ item.dst_ip }}
              </td>
              <td class="bytes-col">{{ formatBytes(item.bytes) }}</td>
              <td class="packets-col">{{ item.packets }} <span class="unit">pps</span></td>
              <td>
                <span class="tag" v-for="p in item.protocols" :key="p">{{ p }}</span>
              </td>
            </tr>
            <tr v-if="flow.length === 0">
              <td colspan="5" class="empty-text">当前时段无活跃流量</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  name: 'Realtime',
  props: {
    flow: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      trendInstance: null,
      protocolInstance: null
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.initCharts();
      window.addEventListener('resize', this.resizeCharts);
    });
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeCharts);
    if (this.trendInstance) this.trendInstance.dispose();
    if (this.protocolInstance) this.protocolInstance.dispose();
  },
  watch: {
    flow: {
      handler(newData) {
        if (newData && newData.length > 0) {
          this.updateTrendChart(newData);
          this.updateProtocolChart(newData);
        }
      },
      deep: true
    }
  },
  methods: {
    isInternalIP(ip) {
      if (!ip) return false;
      return ip.startsWith('10.') || ip.startsWith('192.168.') || ip.startsWith('172.');
    },
    
    initCharts() {
      this.trendInstance = echarts.init(this.$refs.trendChart);
      this.protocolInstance = echarts.init(this.$refs.protocolChart);
      
      // 预先设置基础配置 (亮色主题)
      this.trendInstance.setOption({
        title: { text: '大流吞吐量瞬时切片 (Top 10)', textStyle: { color: '#1e293b', fontSize: 16, fontWeight: 600 } },
        tooltip: { trigger: 'axis', backgroundColor: 'rgba(255,255,255,0.9)', borderColor: '#e2e8f0', textStyle: { color: '#334155' } },
        grid: { left: '3%', right: '4%', bottom: '5%', top: '15%', containLabel: true },
        xAxis: [{ type: 'category', data: [], axisLabel: { color: '#64748b' }, axisLine: { lineStyle: { color: '#cbd5e1' } } }],
        yAxis: [{ type: 'value', name: 'Bytes', axisLabel: { color: '#64748b' }, splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } } }],
        series: [{ 
          name: '流量', type: 'bar', barWidth: '40%',
          itemStyle: { 
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {offset: 0, color: '#0ea5e9'}, 
              {offset: 1, color: '#38bdf8'}
            ]) 
          }, 
          data: [] 
        }]
      });

      this.protocolInstance.setOption({
        title: { text: '瞬时应用协议分布', textStyle: { color: '#1e293b', fontSize: 16, fontWeight: 600 } },
        tooltip: { trigger: 'item', backgroundColor: 'rgba(255,255,255,0.9)', borderColor: '#e2e8f0', textStyle: { color: '#334155' } },
        series: [{ 
          type: 'pie', radius: ['45%', '70%'], avoidLabelOverlap: false, 
          itemStyle: { borderRadius: 8, borderColor: '#ffffff', borderWidth: 2 }, 
          label: { color: '#475569', fontWeight: 500 }, 
          data: [] 
        }],
        color: ['#0ea5e9', '#10b981', '#8b5cf6', '#f59e0b', '#f43f5e', '#64748b']
      });
    },

    updateTrendChart(data) {
      const ips = data.map(item => item.src_ip);
      const bytes = data.map(item => item.bytes);
      this.trendInstance.setOption({
        xAxis: [{ data: ips }],
        series: [{ data: bytes }]
      });
    },

    updateProtocolChart(data) {
      const protoCount = {};
      data.forEach(item => {
        item.protocols.forEach(p => { protoCount[p] = (protoCount[p] || 0) + item.packets; });
      });
      const pieData = Object.keys(protoCount).map(key => ({ name: key, value: protoCount[key] }));
      this.protocolInstance.setOption({
        series: [{ data: pieData }]
      });
    },

    resizeCharts() {
      if (this.trendInstance) this.trendInstance.resize();
      if (this.protocolInstance) this.protocolInstance.resize();
    },

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
.realtime-container { display: flex; flex-direction: column; gap: 24px; height: 100%; box-sizing: border-box; }

/* 基础卡片样式 */
.card-box {
  background: #ffffff;
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  border: 1px solid #f1f5f9;
  box-sizing: border-box;
}

/* 图表行 */
.charts-row { 
  display: flex; 
  height: 380px; /* 给予固定的高度 */
  min-height: 380px;
  gap: 24px; 
}
.chart-card { 
  flex: 1; 
  display: flex; 
  flex-direction: column; /* 让内部元素继承高度 */
  padding: 20px;
}
.echarts-inner {
  width: 100%;
  height: 100%;
  flex: 1;
}

/* 表格区 */
.table-card { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  overflow: hidden; 
}

.table-header { display: flex; align-items: center; gap: 12px; margin-bottom: 20px; }
.box-title { margin: 0; color: #1e293b; font-size: 16px; font-weight: 600; }
.live-badge { display: flex; align-items: center; gap: 6px; background: #fee2e2; color: #ef4444; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; font-family: 'Inter', sans-serif; }
.pulse-dot { width: 6px; height: 6px; border-radius: 50%; background: #ef4444; animation: pulse 1.5s infinite; }

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(239, 68, 68, 0); }
  100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
}

.table-wrapper { flex: 1; overflow-y: auto; padding-right: 8px; }
.table-wrapper::-webkit-scrollbar { width: 6px; }
.table-wrapper::-webkit-scrollbar-track { background: transparent; }
.table-wrapper::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }

table { width: 100%; border-collapse: separate; border-spacing: 0; }
th, td { padding: 14px 16px; text-align: left; font-size: 14px; }
th { color: #64748b; font-weight: 600; position: sticky; top: 0; background: #f8fafc; border-bottom: 2px solid #e2e8f0; border-top: 1px solid #e2e8f0; z-index: 10; }
th:first-child { border-top-left-radius: 8px; border-bottom-left-radius: 8px; border-left: 1px solid #e2e8f0; }
th:last-child { border-top-right-radius: 8px; border-bottom-right-radius: 8px; border-right: 1px solid #e2e8f0; }

td { border-bottom: 1px solid #f1f5f9; color: #334155; }
tr:hover td { background-color: #f8fafc; }

.ip-col { color: #0ea5e9; font-family: 'Courier New', Courier, monospace; font-weight: bold; }
.dst-col { display: flex; align-items: center; gap: 8px; font-family: 'Courier New', Courier, monospace; color: #64748b; }

.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot-safe { background-color: #10b981; }
.dot-warn { background-color: #f59e0b; }

.bytes-col { font-weight: 600; color: #1e293b; }
.packets-col { color: #64748b; }
.unit { font-size: 12px; color: #94a3b8; }

.tag { display: inline-block; background: #ecfdf5; color: #059669; padding: 4px 10px; border-radius: 6px; font-size: 12px; margin-right: 6px; border: 1px solid #d1fae5; font-weight: 500; }

.empty-text { text-align: center; color: #94a3b8; padding: 40px !important; }
</style>