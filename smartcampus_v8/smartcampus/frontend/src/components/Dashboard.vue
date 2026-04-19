<template>
  <div class="dashboard-inner-container">
    <div class="kpi-grid">
      <div class="kpi-card clay-card kpi-matcha">
        <div class="kpi-header">
          <span class="kpi-title">全网实时吞吐量</span>
          <div class="icon-wrapper dark"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg></div>
        </div>
        <div class="kpi-body">
          <h2 class="kpi-value">{{ displayMbps }} <span class="unit">Mbps</span></h2>
          <div class="kpi-status"><span class="dot safe"></span> 探针在线</div>
        </div>
      </div>

      <div class="kpi-card clay-card kpi-pomegranate">
        <div class="kpi-header">
          <span class="kpi-title">今日累计拦截威胁</span>
          <div class="icon-wrapper danger"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg></div>
        </div>
        <div class="kpi-body">
          <h2 class="kpi-value text-danger">{{ aggregatedThreatCount }} <span class="unit">次</span></h2>
          <div class="kpi-status danger-text" v-if="aggregatedThreatCount > 0">已触发防御机制</div>
          <div class="kpi-status" v-else>环境安全</div>
        </div>
      </div>

      <div class="kpi-card clay-card kpi-lemon">
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

      <div class="kpi-card clay-card kpi-ube">
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

    <div class="map-trend-row">
      <div class="map-col">
        <MapTraceability :alerts="alerts" @view-ip="$emit('view-ip', $event)" />
      </div>
      <div class="trend-col">
        <div class="chart-card clay-card trend-card">
          <div class="chart-header">
            <h3 class="chart-title">全网吞吐量宏观波动</h3>
            <div class="metric-toggle">
              <button :class="{ active: metricMode === 'bytes' }" @click="setMetricMode('bytes')">Bytes</button>
              <button :class="{ active: metricMode === 'packets' }" @click="setMetricMode('packets')">Packets</button>
            </div>
          </div>
          <div class="echarts-inner" ref="globalTrendChart"></div>
        </div>
      </div>
    </div>

    <div class="charts-layout">
      <div class="chart-card clay-card flex-3">
        <div class="chart-header">
          <h3 class="chart-title">流量协议画像</h3>
          <div class="metric-toggle">
            <button :class="{ active: metricMode === 'bytes' }" @click="setMetricMode('bytes')">Bytes</button>
            <button :class="{ active: metricMode === 'packets' }" @click="setMetricMode('packets')">Packets</button>
          </div>
        </div>
        <div class="echarts-inner" ref="globalProtocolChart"></div>
      </div>

      <div class="chart-card clay-card flex-4">
        <div class="chart-header">
          <h3 class="chart-title">区域流量透视</h3>
          <div class="metric-toggle">
            <button :class="{ active: metricMode === 'bytes' }" @click="setMetricMode('bytes')">Bytes</button>
            <button :class="{ active: metricMode === 'packets' }" @click="setMetricMode('packets')">Packets</button>
          </div>
        </div>
        <div class="echarts-inner" ref="zoneChart"></div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineAsyncComponent } from 'vue';

export default {
  name: 'Dashboard',
  emits: ['view-ip'],
  components: {
    MapTraceability: defineAsyncComponent(() => import('./MapTraceability.vue'))
  },
  props: {
    flow: { type: Array, default: () => [] },
    alerts: { type: Array, default: () => [] }
  },
  data() {
    return {
      echarts: null,
      trendInstance: null,
      protocolInstance: null,
      zoneInstance: null,
      trendData: { times: [], bytes: [], packets: [] },
      displayMbps: '0.00',
      displayPPS: 0,
      displayNodes: 0,
      displayProtocol: 'N/A',
      zoneTimer: null,
      metricMode: 'bytes'
    };
  },
  computed: {
    aggregatedAlerts() {
      const aggregated = new Map();

      this.alerts.forEach((item) => {
        const key = `${item.src_ip || 'unknown'}__${item.type || '未知威胁'}`;
        const count = Number(item.count || 1);

        if (aggregated.has(key)) {
          const existing = aggregated.get(key);
          existing.count += count;
          if (String(item.time || '') >= String(existing.time || '')) {
            aggregated.set(key, {
              ...existing,
              ...item,
              count: existing.count,
              aggregateKey: key
            });
          }
          return;
        }

        aggregated.set(key, {
          ...item,
          count,
          aggregateKey: key
        });
      });

      return Array.from(aggregated.values());
    },
    aggregatedThreatCount() {
      return this.aggregatedAlerts.reduce((sum, item) => sum + Number(item.count || 1), 0);
    },
    uniqueAttackers() {
      return new Set(this.aggregatedAlerts.map((item) => item.src_ip).filter(Boolean)).size;
    }
  },
  watch: {
    flow: {
      handler(newData) {
        const validData = Array.isArray(newData) ? newData : [];
        if (validData.length > 0) {
          const totalBytes = validData.reduce((sum, item) => sum + Number(item.bytes || 0), 0);
          this.displayMbps = (totalBytes * 8 / 1024 / 1024).toFixed(2);
          this.displayPPS = validData.reduce((sum, item) => sum + Number(item.packets || 0), 0);
        } else {
          this.displayMbps = '0.00';
          this.displayPPS = 0;
        }
        this.updateTrendData(validData);
        this.updateProtocolChart(validData);
      },
      deep: true,
      immediate: true
    },
    metricMode() {
      this.refreshAllCharts();
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.initCharts().then(() => {
        this.refreshAllCharts();
        this.fetchZoneStats();
        this.zoneTimer = setInterval(this.fetchZoneStats, 5000);
        window.addEventListener('resize', this.resizeCharts);
      });
    });
  },
  beforeUnmount() {
    clearInterval(this.zoneTimer);
    window.removeEventListener('resize', this.resizeCharts);
    if (this.trendInstance) this.trendInstance.dispose();
    if (this.protocolInstance) this.protocolInstance.dispose();
    if (this.zoneInstance) this.zoneInstance.dispose();
  },
  methods: {
    async initCharts() {
      const echartsModule = await import('echarts');
      if (!this.$refs.globalTrendChart || !this.$refs.globalProtocolChart || !this.$refs.zoneChart) return;

      this.echarts = echartsModule;
      this.trendInstance = echartsModule.init(this.$refs.globalTrendChart);
      this.protocolInstance = echartsModule.init(this.$refs.globalProtocolChart);
      this.zoneInstance = echartsModule.init(this.$refs.zoneChart);

      this.trendInstance.setOption({
        tooltip: {
          trigger: 'axis',
          triggerOn: 'mousemove|click',
          confine: true,
          backgroundColor: '#171717',
          borderColor: '#171717',
          textStyle: { color: '#fff' },
          axisPointer: { type: 'line', lineStyle: { color: '#e4e4e7' } },
          padding: 12,
          borderRadius: 8,
          formatter: (params) => {
            const point = Array.isArray(params) ? params[0] : params;
            return `${point.axisValue}<br/>纵坐标值: ${this.formatMetricValue(Number(point.data || 0))}`;
          }
        },
        grid: { left: '0%', right: '0%', bottom: '0%', top: '8%', containLabel: true },
        xAxis: { type: 'category', boundaryGap: false, data: [], axisLabel: { color: '#737373', fontSize: 12 }, axisLine: { show: false }, axisTick: { show: false } },
        yAxis: {
          type: 'value',
          min: 0,
          axisLabel: { color: '#737373', formatter: (value) => this.formatAxisValue(value) },
          splitLine: { lineStyle: { color: '#f4f4f5', type: 'dashed' } }
        },
        series: [{
          name: '流量走势',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 14,
          showSymbol: true,
          hoverAnimation: true,
          lineStyle: { color: '#43089f', width: 3 },
          itemStyle: { color: '#43089f', borderColor: '#ffffff', borderWidth: 2 },
          label: {
            show: false,
            color: '#43089f',
            fontWeight: 700,
            backgroundColor: 'rgba(255,255,255,0.92)',
            borderRadius: 8,
            padding: [4, 8],
            formatter: ({ value }) => this.formatMetricValue(Number(value || 0))
          },
          emphasis: { focus: 'series', scale: 1.35, label: { show: true } },
          areaStyle: {
            color: new echartsModule.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(67, 8, 159, 0.2)' },
              { offset: 1, color: 'rgba(67, 8, 159, 0)' }
            ])
          },
          data: []
        }]
      });

      this.protocolInstance.setOption({
        tooltip: {
          trigger: 'item',
          backgroundColor: '#171717',
          borderColor: '#171717',
          textStyle: { color: '#fff' },
          padding: 12,
          borderRadius: 8,
          formatter: (params) => `${params.name}<br/>${this.metricMode === 'bytes' ? '字节数' : '包数'}: ${this.formatMetricValue(params.value || 0)}<br/>占比: ${params.percent || 0}%`
        },
        series: [{
          name: '协议分布',
          type: 'pie',
          radius: ['50%', '75%'],
          center: ['50%', '55%'],
          itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
          label: { color: '#52525b', fontWeight: 600, formatter: '{b}\n{d}%' },
          data: []
        }],
        color: ['#078a52', '#3bd3fd', '#fbbd41', '#43089f', '#fc7981', '#01418d']
      });

      this.zoneInstance.setOption({
        tooltip: {
          trigger: 'axis',
          triggerOn: 'mousemove|click',
          confine: true,
          backgroundColor: '#171717',
          borderColor: '#171717',
          textStyle: { color: '#fff' },
          axisPointer: { type: 'shadow' },
          padding: 12,
          borderRadius: 8,
          formatter: (params) => {
            const point = Array.isArray(params) ? params[0] : params;
            return `${point.name}<br/>纵坐标值: ${this.formatMetricValue(Number(point.data || 0))}`;
          }
        },
        grid: { left: '0%', right: '0%', bottom: '0%', top: '8%', containLabel: true },
        xAxis: { type: 'category', data: [], axisLabel: { color: '#737373', fontSize: 11 }, axisLine: { show: false }, axisTick: { show: false } },
        yAxis: {
          type: 'value',
          axisLabel: { color: '#737373', formatter: (value) => this.formatAxisValue(value) },
          splitLine: { lineStyle: { color: '#f4f4f5', type: 'dashed' } }
        },
        series: [{
          name: '区域流量',
          type: 'bar',
          barWidth: '45%',
          label: {
            show: false,
            position: 'top',
            color: '#171717',
            fontWeight: 700,
            formatter: ({ value }) => this.formatMetricValue(Number(value || 0))
          },
          emphasis: { focus: 'series', label: { show: true } },
          itemStyle: {
            borderRadius: [6, 6, 0, 0],
            color(params) {
              const colors = ['#078a52', '#3bd3fd', '#fbbd41', '#43089f', '#fc7981', '#01418d'];
              return colors[params.dataIndex % colors.length];
            }
          },
          data: []
        }]
      });
    },
    setMetricMode(mode) {
      if (this.metricMode === mode) return;
      this.metricMode = mode;
    },
    refreshAllCharts() {
      this.updateTrendData(this.flow);
      this.updateProtocolChart(this.flow);
      this.fetchZoneStats();
    },
    async fetchZoneStats() {
      if (!this.zoneInstance) return;
      try {
        const serverIp = window.location.hostname;
        const res = await fetch(`http://${serverIp}:8000/api/zone-stats`);
        const data = await res.json();
        if (data.zones && data.zones.length > 0) {
          const names = data.zones.map((z) => z.zone);
          const values = data.zones.map((z) => this.metricMode === 'bytes' ? Number(z.bytes || 0) : Number(z.packets || 0));
          this.zoneInstance.setOption({
            xAxis: { data: names },
            series: [{ data: values }]
          });
        } else {
          this.zoneInstance.setOption({
            xAxis: { data: [] },
            series: [{ data: [] }]
          });
        }
      } catch (err) {
      }
    },
    updateTrendData(validData = []) {
      if (!this.trendInstance) return;
      const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
      const totalBytes = (validData || []).reduce((sum, item) => sum + Number(item.bytes || 0), 0);
      const totalPackets = (validData || []).reduce((sum, item) => sum + Number(item.packets || 0), 0);
      const lastTime = this.trendData.times[this.trendData.times.length - 1];

      if (lastTime !== now) {
        this.trendData.times.push(now);
        this.trendData.bytes.push(totalBytes);
        this.trendData.packets.push(totalPackets);
      } else {
        const lastIndex = this.trendData.times.length - 1;
        this.trendData.bytes.splice(lastIndex, 1, totalBytes);
        this.trendData.packets.splice(lastIndex, 1, totalPackets);
      }

      if (this.trendData.times.length > 40) {
        this.trendData.times.shift();
        this.trendData.bytes.shift();
        this.trendData.packets.shift();
      }

      this.trendInstance.setOption({
        xAxis: { data: this.trendData.times },
        series: [{ data: this.metricMode === 'bytes' ? this.trendData.bytes : this.trendData.packets }]
      });
    },
    updateProtocolChart(validData) {
      if (!this.protocolInstance) return;
      const protoCount = {};
      (validData || []).forEach((item) => {
        (item.protocols || []).forEach((p) => {
          protoCount[p] = (protoCount[p] || 0) + (this.metricMode === 'bytes' ? Number(item.bytes || 0) : Number(item.packets || 0));
        });
      });
      const pieData = Object.keys(protoCount).map((key) => ({ name: key, value: protoCount[key] }));
      this.protocolInstance.setOption({ series: [{ data: pieData }] });
    },
    formatPackets(value) {
      return `${Number(value || 0).toLocaleString()} Pkts`;
    },
    formatMetricValue(value) {
      return this.metricMode === 'bytes' ? this.formatBytes(value) : this.formatPackets(value);
    },
    formatAxisValue(value) {
      const numericValue = Number(value || 0);
      if (this.metricMode === 'bytes') {
        return this.formatBytes(numericValue);
      }
      if (numericValue >= 1000) {
        return `${(numericValue / 1000).toFixed(1)}k`;
      }
      return `${numericValue}`;
    },
    formatBytes(bytes) {
      if (!bytes || bytes <= 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
    },
    resizeCharts() {
      if (this.trendInstance) this.trendInstance.resize();
      if (this.protocolInstance) this.protocolInstance.resize();
      if (this.zoneInstance) this.zoneInstance.resize();
    }
  }
};
</script>

<style scoped>
.dashboard-inner-container { display: flex; flex-direction: column; gap: 24px; height: 100%; box-sizing: border-box; }
.kpi-grid { display: flex; gap: 24px; flex-shrink: 0; }
.kpi-card { flex: 1; background: var(--glass-bg, rgba(255,255,255,0.55)); backdrop-filter: var(--glass-blur, blur(12px)); -webkit-backdrop-filter: var(--glass-blur, blur(12px)); border-radius: 24px; padding: 24px; display: flex; flex-direction: column; justify-content: space-between; height: 140px; box-sizing: border-box; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); position: relative; overflow: hidden; }
.clay-card { transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.clay-card:hover { transform: translateY(-2px); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)), 0 12px 28px rgba(0,0,0,0.08); }
.kpi-matcha { background: var(--clay-matcha-bg, #edfcf2) !important; border-color: rgba(7, 138, 82, 0.15) !important; }
.kpi-pomegranate { background: var(--clay-pomegranate-bg, #fff0f1) !important; border-color: rgba(252, 121, 129, 0.15) !important; }
.kpi-lemon { background: var(--clay-lemon-bg, #fef9ed) !important; border-color: rgba(251, 189, 65, 0.15) !important; }
.kpi-ube { background: var(--clay-ube-bg, #f3eeff) !important; border-color: rgba(67, 8, 159, 0.12) !important; }
.kpi-header { display: flex; justify-content: space-between; align-items: flex-start; }
.kpi-title { font-size: 14px; color: var(--clay-text-muted, #9f9b93); font-weight: 600; }
.icon-wrapper { width: 32px; height: 32px; border-radius: 8px; display: flex; justify-content: center; align-items: center; }
.icon-wrapper.dark { background: #f4f4f5; color: #000000; }
.icon-wrapper.danger { background: #fef2f2; color: var(--clay-pomegranate, #fc7981); }
.icon-wrapper.warning { background: #fef3c7; color: var(--clay-lemon, #fbbd41); }
.icon-wrapper.purple { background: #f3e8ff; color: var(--clay-ube, #43089f); }
.kpi-body { margin-top: auto; }
.kpi-value { margin: 0 0 8px 0; font-size: 32px; font-weight: 800; color: #000000; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); line-height: 1; }
.kpi-value.text-danger { color: var(--clay-pomegranate, #fc7981); }
.kpi-value.text-purple { color: var(--clay-ube, #43089f); }
.unit { font-size: 14px; color: var(--clay-text-muted, #9f9b93); font-weight: 500; }
.kpi-status { font-size: 12px; color: var(--clay-text-muted, #9f9b93); display: flex; align-items: center; gap: 6px; font-weight: 500; }
.danger-text { color: var(--clay-pomegranate, #fc7981); }
.warning-text { color: var(--clay-lemon, #d08a11); }
.dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.dot.safe { background: var(--clay-matcha, #078a52); }
.charts-layout { flex: 1; display: flex; gap: 24px; min-height: 0; }
.chart-card { background: var(--glass-bg, rgba(255,255,255,0.55)); backdrop-filter: var(--glass-blur, blur(12px)); -webkit-backdrop-filter: var(--glass-blur, blur(12px)); border-radius: 24px; padding: 24px; box-sizing: border-box; display: flex; flex-direction: column; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); }
.chart-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.chart-title { margin: 0; color: #171717; font-size: 16px; font-weight: 700; }
.metric-toggle { display: inline-flex; gap: 6px; background: rgba(255,255,255,0.72); border-radius: 999px; padding: 4px; }
.metric-toggle button { border: none; background: transparent; color: #55534e; border-radius: 999px; padding: 6px 10px; font-size: 11px; font-weight: 800; cursor: pointer; }
.metric-toggle button.active { background: rgba(243,238,255,0.92); color: var(--clay-ube, #43089f); }
.flex-3 { flex: 3; }
.flex-4 { flex: 4; }
.echarts-inner { width: 100%; height: 100%; flex: 1; }
.map-trend-row { display: flex; gap: 24px; flex-shrink: 0; height: 440px; }
.map-col { flex: 5; min-width: 0; }
.trend-col { flex: 5; min-width: 0; }
.trend-card { height: 100%; }
</style>
