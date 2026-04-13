<template>
  <div class="dashboard-inner-container">
    
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">全网实时吞吐量</span>
          <div class="icon-wrapper dark"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg></div>
        </div>
        <div class="kpi-body">
          <h2 class="kpi-value">{{ displayMbps }} <span class="unit">Mbps</span></h2>
          <div class="kpi-status"><span class="dot safe"></span> 探针在线</div>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">今日累计拦截威胁</span>
          <div class="icon-wrapper danger"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg></div>
        </div>
        <div class="kpi-body">
          <h2 class="kpi-value text-danger">{{ alerts.length }} <span class="unit">次</span></h2>
          <div class="kpi-status danger-text" v-if="alerts.length > 0">已触发防御机制</div>
          <div class="kpi-status" v-else>环境安全</div>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">独立攻击源 (IP)</span>
          <div class="icon-wrapper warning"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg></div>
        </div>
        <div class="kpi-body">
          <h2 class="kpi-value">{{ uniqueAttackers }} <span class="unit">个</span></h2>
          <div class="kpi-status warning-text" v-if="uniqueAttackers > 0">需重点关注</div>
          <div class="kpi-status" v-else>暂无异常源</div>
        </div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-title">AIOps 智能引擎</span>
          <div class="icon-wrapper purple"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 1 0 10 10H12V2z"></path><path d="M21.18 8.02A10 10 0 0 0 13.98.82v7.2h7.2z"></path></svg></div>
        </div>
        <div class="kpi-body">
          <h2 class="kpi-value text-purple">DeepSeek</h2>
          <div class="kpi-status"><span class="dot safe"></span> 语境注入就绪</div>
        </div>
      </div>
    </div>

    <div class="charts-layout">
      <div class="chart-card flex-7">
        <div class="echarts-inner" ref="globalTrendChart"></div>
      </div>
      
      <div class="chart-card flex-3">
        <div class="echarts-inner" ref="globalProtocolChart"></div>
      </div>
    </div>

  </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  name: 'Dashboard',
  props: { flow: { type: Array, default: () => [] }, alerts: { type: Array, default: () => [] } },
  data() {
    return {
      trendInstance: null, protocolInstance: null,
      trendData: { times: [], mbps: [] },
      displayMbps: '0.00', displayPPS: 0, displayNodes: 0, displayProtocol: 'N/A'
    }
  },
  computed: {
    uniqueAttackers() { return new Set(this.alerts.map(a => a.src_ip)).size; }
  },
  watch: {
    flow: {
      handler(newData) {
        if (newData && newData.length > 0) {
          const totalBytes = newData.reduce((sum, item) => sum + item.bytes, 0);
          this.displayMbps = (totalBytes * 8 / 1024 / 1024).toFixed(2);
          this.updateTrendData();
          this.updateProtocolChart(newData);
        }
      },
      deep: true
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
    initCharts() {
      this.trendInstance = echarts.init(this.$refs.globalTrendChart);
      this.protocolInstance = echarts.init(this.$refs.globalProtocolChart);
      
      // 极简风格趋势图
      this.trendInstance.setOption({
        title: { text: '全网吞吐量宏观波动', textStyle: { color: '#171717', fontSize: 16, fontWeight: 700 }, top: 0, left: 0 },
        tooltip: { trigger: 'axis', backgroundColor: '#171717', borderColor: '#171717', textStyle: { color: '#fff' }, axisPointer: { type: 'line', lineStyle: { color: '#e4e4e7' } }, padding: 12, borderRadius: 8 },
        grid: { left: '0%', right: '0%', bottom: '0%', top: '20%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: [], axisLabel: { color: '#737373', fontSize: 12 }, axisLine: { show: false }, axisTick: { show: false } },
        yAxis: { type: 'value', min: 0, axisLabel: { color: '#737373' }, splitLine: { lineStyle: { color: '#f4f4f5', type: 'dashed' } } },
        series: [{
          name: '吞吐量 (Mbps)', type: 'line', smooth: true, symbol: 'none',
          lineStyle: { color: '#6d28d9', width: 3 }, // 深紫色主线
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(109, 40, 217, 0.2)' },
              { offset: 1, color: 'rgba(109, 40, 217, 0)' }
            ])
          },
          data: []
        }]
      });
      
      // 极简风格饼图
      this.protocolInstance.setOption({
        title: { text: '流量协议画像', textStyle: { color: '#171717', fontSize: 16, fontWeight: 700 }, top: 0, left: 0 },
        tooltip: { trigger: 'item', backgroundColor: '#171717', borderColor: '#171717', textStyle: { color: '#fff' }, padding: 12, borderRadius: 8 },
        series: [{
          name: '协议分布', type: 'pie', radius: ['50%', '75%'], center: ['50%', '55%'],
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: { color: '#52525b', fontWeight: 600, formatter: '{b}\n{d}%' },
          data: []
        }],
        // 使用高级中性色与点缀色搭配
        color: ['#171717', '#6d28d9', '#eab308', '#f97316', '#a1a1aa', '#e4e4e7']
      });
    },
    updateTrendData() {
      const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const mbps = parseFloat(this.displayMbps);
      this.trendData.times.push(now);
      this.trendData.mbps.push(mbps);
      if (this.trendData.times.length > 40) { this.trendData.times.shift(); this.trendData.mbps.shift(); }
      this.trendInstance.setOption({ xAxis: { data: this.trendData.times }, series: [{ data: this.trendData.mbps }] });
    },
    updateProtocolChart(validData) {
      const protoCount = {};
      validData.forEach(item => { item.protocols.forEach(p => { protoCount[p] = (protoCount[p] || 0) + item.bytes; }); });
      const pieData = Object.keys(protoCount).map(key => ({ name: key, value: protoCount[key] }));
      this.protocolInstance.setOption({ series: [{ data: pieData }] });
    },
    resizeCharts() { if (this.trendInstance) this.trendInstance.resize(); if (this.protocolInstance) this.protocolInstance.resize(); }
  }
}
</script>

<style scoped>
.dashboard-inner-container { display: flex; flex-direction: column; gap: 24px; height: 100%; box-sizing: border-box; }

/* 顶部卡片网格 */
.kpi-grid { display: flex; gap: 24px; flex-shrink: 0; }
.kpi-card { flex: 1; background: #ffffff; border-radius: 20px; padding: 24px; display: flex; flex-direction: column; justify-content: space-between; height: 140px; box-sizing: border-box; }

.kpi-header { display: flex; justify-content: space-between; align-items: flex-start; }
.kpi-title { font-size: 14px; color: #737373; font-weight: 600; }
.icon-wrapper { width: 32px; height: 32px; border-radius: 8px; display: flex; justify-content: center; align-items: center; }
.icon-wrapper.dark { background: #f4f4f5; color: #171717; }
.icon-wrapper.danger { background: #fef2f2; color: #dc2626; }
.icon-wrapper.warning { background: #fef3c7; color: #d97706; }
.icon-wrapper.purple { background: #f3e8ff; color: #6d28d9; }

.kpi-body { margin-top: auto; }
.kpi-value { margin: 0 0 8px 0; font-size: 32px; font-weight: 800; color: #171717; font-family: 'Inter', sans-serif; line-height: 1; }
.kpi-value.text-danger { color: #dc2626; }
.kpi-value.text-purple { color: #6d28d9; }
.unit { font-size: 14px; color: #a1a1aa; font-weight: 500; }

.kpi-status { font-size: 12px; color: #737373; display: flex; align-items: center; gap: 6px; font-weight: 500; }
.danger-text { color: #dc2626; }
.warning-text { color: #d97706; }
.dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.dot.safe { background: #16a34a; }

/* 图表布局 */
.charts-layout { flex: 1; display: flex; gap: 24px; min-height: 0; }
.chart-card { background: #ffffff; border-radius: 20px; padding: 24px; box-sizing: border-box; display: flex; flex-direction: column; }
.flex-7 { flex: 7; }
.flex-3 { flex: 3; }
.echarts-inner { width: 100%; height: 100%; flex: 1; }
</style>