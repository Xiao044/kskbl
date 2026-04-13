<template>
  <div class="realtime-inner-container">
    
    <div class="charts-row">
      <div class="content-card flex-1">
        <div class="echarts-inner" ref="trendChart"></div>
      </div>
      <div class="content-card flex-1">
        <div class="echarts-inner" ref="protocolChart"></div>
      </div>
    </div>

    <div class="content-card table-card">
      <div class="card-header flex-between">
        <h3 class="section-title">秒级活跃链路监控</h3>
        <div class="live-pill"><span class="pulse-dot"></span> LIVE</div>
      </div>
      
      <div class="table-scroll-area">
        <table>
          <thead>
            <tr>
              <th>源 IP (发起方)</th>
              <th>去向 (目的 IP)</th>
              <th>瞬时吞吐量</th>
              <th>数据包量 (PPS)</th>
              <th>识别应用/协议</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in flow" :key="index">
              <td class="ip-src">{{ item.src_ip }}</td>
              <td class="ip-dst">
                <span :class="['status-dot', isInternalIP(item.dst_ip) ? 'safe' : 'warn']"></span>
                {{ item.dst_ip }}
              </td>
              <td class="bytes-text">{{ formatBytes(item.bytes) }}</td>
              <td class="packets-text">{{ item.packets }} <span class="unit">pps</span></td>
              <td>
                <span class="tag-pill" v-for="p in item.protocols" :key="p">{{ p }}</span>
              </td>
            </tr>
            <tr v-if="flow.length === 0">
              <td colspan="5" class="empty-state">
                <div class="empty-icon">📡</div>
                <p>当前时段无活跃的网路数据流</p>
              </td>
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
  props: { flow: { type: Array, default: () => [] } },
  data() { return { trendInstance: null, protocolInstance: null } },
  watch: {
    flow: {
      handler(newData) {
        if (newData && newData.length > 0) {
          this.updateTrendChart(newData);
          this.updateProtocolChart(newData);
        }
      }, deep: true
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
  methods: {
    isInternalIP(ip) { return ip && (ip.startsWith('10.') || ip.startsWith('192.168.') || ip.startsWith('172.')); },
    initCharts() {
      this.trendInstance = echarts.init(this.$refs.trendChart);
      this.protocolInstance = echarts.init(this.$refs.protocolChart);
      
      // 瞬时吞吐量 - 柱状图
      this.trendInstance.setOption({
        title: { text: '大流吞吐量瞬时切片', textStyle: { color: '#171717', fontSize: 16, fontWeight: 700 }, top: 0 },
        tooltip: { trigger: 'axis', backgroundColor: '#171717', borderColor: '#171717', textStyle: { color: '#fff' }, padding: 12, borderRadius: 8 },
        grid: { left: '0%', right: '0%', bottom: '0%', top: '20%', containLabel: true },
        xAxis: [{ type: 'category', data: [], axisLabel: { color: '#737373', fontSize: 11 }, axisLine: { show: false }, axisTick: { show: false } }],
        yAxis: [{ type: 'value', axisLabel: { color: '#a1a1aa' }, splitLine: { lineStyle: { color: '#f4f4f5', type: 'dashed' } } }],
        series: [{ 
          name: '瞬时流量', type: 'bar', barWidth: '35%',
          itemStyle: { 
            borderRadius: [4, 4, 0, 0],
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              {offset: 0, color: '#171717'}, 
              {offset: 1, color: '#6d28d9'}
            ]) 
          }, 
          data: [] 
        }]
      });

      // 协议分布 - 极简环形图
      this.protocolInstance.setOption({
        title: { text: '瞬时应用协议分布', textStyle: { color: '#171717', fontSize: 16, fontWeight: 700 }, top: 0 },
        tooltip: { trigger: 'item', backgroundColor: '#171717', borderColor: '#171717', textStyle: { color: '#fff' }, padding: 12, borderRadius: 8 },
        series: [{ 
          type: 'pie', radius: ['45%', '75%'], center: ['50%', '55%'],
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 }, 
          label: { color: '#52525b', fontWeight: 600 }, 
          data: [] 
        }],
        color: ['#171717', '#6d28d9', '#eab308', '#f97316', '#a1a1aa', '#e4e4e7']
      });
    },
    updateTrendChart(data) {
      this.trendInstance.setOption({
        xAxis: [{ data: data.map(item => item.src_ip) }],
        series: [{ data: data.map(item => item.bytes) }]
      });
    },
    updateProtocolChart(data) {
      const protoCount = {};
      data.forEach(item => { item.protocols.forEach(p => { protoCount[p] = (protoCount[p] || 0) + item.packets; }); });
      this.protocolInstance.setOption({ series: [{ data: Object.keys(protoCount).map(key => ({ name: key, value: protoCount[key] })) }] });
    },
    resizeCharts() { if (this.trendInstance) this.trendInstance.resize(); if (this.protocolInstance) this.protocolInstance.resize(); },
    formatBytes(bytes) {
      if (!bytes || bytes === 0) return '0 B';
      const k = 1024, sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
  }
}
</script>

<style scoped>
.realtime-inner-container { display: flex; flex-direction: column; gap: 24px; height: 100%; box-sizing: border-box; }

.content-card { background: #ffffff; border-radius: 20px; padding: 24px; display: flex; flex-direction: column; }
.card-header { margin-bottom: 20px; }
.flex-between { display: flex; justify-content: space-between; align-items: center; }
.section-title { margin: 0; color: #171717; font-size: 18px; font-weight: 700; }

/* 顶部图表区 */
.charts-row { display: flex; gap: 24px; height: 320px; flex-shrink: 0; }
.flex-1 { flex: 1; }
.echarts-inner { width: 100%; height: 100%; flex: 1; }

/* 底部表格区 */
.table-card { flex: 1; overflow: hidden; }

/* Live 呼吸灯徽章 */
.live-pill { display: flex; align-items: center; gap: 8px; background: #fef2f2; color: #dc2626; padding: 6px 14px; border-radius: 999px; font-size: 12px; font-weight: 700; font-family: 'Inter', sans-serif; }
.pulse-dot { width: 6px; height: 6px; border-radius: 50%; background: #dc2626; animation: pulse 1.5s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0.4); } 70% { box-shadow: 0 0 0 6px rgba(220, 38, 38, 0); } 100% { box-shadow: 0 0 0 0 rgba(220, 38, 38, 0); } }

/* 表格主体 */
.table-scroll-area { flex: 1; overflow-y: auto; }
.table-scroll-area::-webkit-scrollbar { width: 4px; }
.table-scroll-area::-webkit-scrollbar-thumb { background: #d4d4d8; border-radius: 4px; }

table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 14px 16px; color: #737373; font-size: 13px; font-weight: 600; border-bottom: 2px solid #e5e7eb; position: sticky; top: 0; background: #ffffff; z-index: 10; }
td { padding: 16px; font-size: 14px; border-bottom: 1px solid #f4f4f5; color: #27272a; }
tr:hover td { background: #fafafa; }

.ip-src { color: #6d28d9; font-family: 'Courier New', monospace; font-weight: 700; }
.ip-dst { display: flex; align-items: center; gap: 8px; font-family: 'Courier New', monospace; color: #52525b; }

.status-dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.safe { background-color: #16a34a; }
.warn { background-color: #d97706; }

.bytes-text { font-weight: 700; color: #171717; }
.packets-text { color: #52525b; }
.unit { font-size: 12px; color: #a1a1aa; }

.tag-pill { display: inline-block; background: #f4f4f5; color: #52525b; padding: 4px 12px; border-radius: 999px; font-size: 12px; margin-right: 8px; font-weight: 600; }

.empty-state { text-align: center; padding: 60px 0 !important; color: #a1a1aa; }
.empty-icon { font-size: 40px; margin-bottom: 16px; opacity: 0.3; filter: grayscale(1); }
</style>