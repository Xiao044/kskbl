<template>
  <div class="rank-inner-container">
    <div class="top-row">
      <div class="chart-box pie-area">
        <div class="chart-header">
          <h3 class="box-title">Top-10 节点流量占比</h3>
          <div class="ui-metric-toggle">
            <button :class="{ active: metricMode === 'bytes' }" @click="setMetricMode('bytes')">Bytes</button>
            <button :class="{ active: metricMode === 'packets' }" @click="setMetricMode('packets')">Packets</button>
          </div>
        </div>
        <div class="echarts-container" ref="pieChart"></div>
      </div>
      <div class="chart-box bar-area">
        <div class="chart-header">
          <h3 class="box-title">实时流量强度对比</h3>
          <div class="ui-metric-toggle">
            <button :class="{ active: metricMode === 'bytes' }" @click="setMetricMode('bytes')">Bytes</button>
            <button :class="{ active: metricMode === 'packets' }" @click="setMetricMode('packets')">Packets</button>
          </div>
        </div>
        <div class="echarts-container" ref="barChart"></div>
      </div>
    </div>

    <div class="bottom-row">
      <div class="table-card">
        <div class="table-header">
          <h3 class="box-title">全网流量大户溯源清单 (Top-10)</h3>
          <button class="refresh-btn ui-action-btn" @click="fetchTopK" :disabled="loading">
            {{ loading ? '同步中...' : '手动刷新' }}
          </button>
        </div>
        
        <div class="table-wrapper ui-table-scroll">
          <table v-if="topkList.length" class="ui-data-table">
            <thead>
              <tr>
                <th width="60">排名</th>
                <th>源地址 (Source)</th>
                <th>源区域</th>
                <th>目的地址 (Destination)</th>
                <th>协议特征</th>
                <th width="200">吞吐进度</th>
                <th>累计流量</th>
                <th>包数 (Pkts)</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(item, index) in topkList" :key="index">
                <td><span :class="['rank-num', index < 3 ? 'top-three' : '']">{{ index + 1 }}</span></td>
                <td class="ip-text">
                  <button class="ip-link ui-ip-link" type="button" @click="$emit('view-ip', item.src_ip)">{{ item.src_ip }}</button>
                </td>
                <td><span class="zone-tag-rank ui-pill-tag ui-pill-tag--blue">{{ item.src_zone || '--' }}</span></td>
                <td class="ip-text">
                  <button class="ip-link ui-ip-link" type="button" @click="$emit('view-ip', item.dst_ip)">{{ item.dst_ip }}</button>
                </td>
                <td>
                  <span class="proto-tag" v-for="p in item.protocols" :key="p">{{ p }}</span>
                </td>
                <td>
                  <div class="progress-container">
                    <div class="progress-bar" :style="{ width: getProgressWidth(item) + '%' }"></div>
                  </div>
                </td>
                <td class="data-text">{{ formatBytes(item.bytes || 0) }}</td>
                <td class="data-text">{{ Number(item.packets || 0).toLocaleString() }}</td>
              </tr>
            </tbody>
          </table>
          
          <div v-else class="empty-state">
            <div class="empty-icon">📊</div>
            <p>暂无排行数据，正在等待探针分析...</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Rank',
  emits: ['view-ip', 'logout'],
  data() {
    return {
      echarts: null,
      topkList: [],
      loading: false,
      pieInstance: null,
      barInstance: null,
      timer: null,
      metricMode: 'bytes'
    };
  },
  watch: {
    metricMode() {
      this.updateCharts();
    }
  },
  mounted() {
    this.initCharts();
    this.fetchTopK();
    this.timer = setInterval(this.fetchTopK, 5000);
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    clearInterval(this.timer);
    window.removeEventListener('resize', this.handleResize);
    if (this.pieInstance) this.pieInstance.dispose();
    if (this.barInstance) this.barInstance.dispose();
  },
  methods: {
    async fetchTopK() {
      const token = localStorage.getItem('token');
      if (!token) return;
      
      this.loading = true;
      try {
        const serverIp = window.location.hostname;
        const res = await fetch(`http://${serverIp}:8000/api/topk`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (res.status === 401) {
          this.$emit('logout');
          return;
        }
        
        const data = await res.json();
        this.topkList = data.top10 || [];
        this.updateCharts();
      } catch (err) {
        console.error('排行数据同步失败', err);
      } finally {
        this.loading = false;
      }
    },
    async initCharts() {
      const echartsModule = await import('echarts');
      if (!this.$refs.pieChart || !this.$refs.barChart) return;

      this.echarts = echartsModule;
      this.pieInstance = echartsModule.init(this.$refs.pieChart);
      this.barInstance = echartsModule.init(this.$refs.barChart);
      
      const commonOption = {
        textStyle: { fontFamily: 'Inter' },
        animationDuration: 1000
      };
      
      this.pieInstance.setOption({
        ...commonOption,
        tooltip: {
          trigger: 'item',
          backgroundColor: '#171717',
          textStyle: { color: '#fff' },
          formatter: (params) => `${params.name}<br/>${this.metricLabel()}: ${this.formatMetricValue(params.value || 0)}<br/>占比: ${params.percent || 0}%`
        },
        series: [{
          type: 'pie',
          radius: ['40%', '70%'],
          avoidLabelOverlap: false,
          itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
          label: { show: false },
          data: []
        }],
        color: ['#078a52', '#3bd3fd', '#fbbd41', '#43089f', '#fc7981', '#01418d', '#84e7a5', '#c1b0ff', '#f8cc65', '#0089ad']
      });

      this.barInstance.setOption({
        ...commonOption,
        tooltip: {
          trigger: 'axis',
          triggerOn: 'mousemove|click',
          confine: true,
          axisPointer: { type: 'shadow' },
          backgroundColor: '#171717',
          textStyle: { color: '#fff' },
          formatter: (params) => {
            const point = Array.isArray(params) ? params[0] : params;
            return `${point.name}<br/>纵坐标值: ${this.formatMetricValue(Number(point.data || 0))}`;
          }
        },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '5%', containLabel: true },
        xAxis: {
          type: 'value',
          axisLabel: { formatter: (value) => this.formatAxisValue(value) },
          splitLine: { lineStyle: { type: 'dashed' } }
        },
        yAxis: { type: 'category', data: [], axisLine: { show: false }, axisTick: { show: false } },
        series: [{
          type: 'bar',
          data: [],
          label: {
            show: false,
            position: 'right',
            color: '#171717',
            fontWeight: 700,
            formatter: ({ value }) => this.formatMetricValue(Number(value || 0))
          },
          emphasis: { focus: 'series', label: { show: true } },
          itemStyle: { borderRadius: [0, 6, 6, 0], color: '#43089f' },
          barWidth: '60%'
        }]
      });

      if (this.topkList.length) {
        this.updateCharts();
      }
    },
    updateCharts() {
      if (!this.pieInstance || !this.barInstance) return;
      if (!this.topkList.length) {
        this.pieInstance.setOption({ series: [{ data: [] }] });
        this.barInstance.setOption({
          yAxis: { data: [] },
          series: [{ data: [] }]
        });
        return;
      }

      const pieData = this.topkList.map((item) => ({ name: item.src_ip, value: this.getMetricValue(item) }));
      this.pieInstance.setOption({ series: [{ data: pieData }] });

      const barY = this.topkList.slice(0, 5).reverse().map((item) => item.src_ip);
      const barX = this.topkList.slice(0, 5).reverse().map((item) => this.getMetricValue(item));
      this.barInstance.setOption({
        yAxis: { data: barY },
        series: [{ data: barX }]
      });
    },
    setMetricMode(mode) {
      if (this.metricMode === mode) return;
      this.metricMode = mode;
    },
    metricLabel() {
      return this.metricMode === 'bytes' ? '累计字节数' : '累计包数';
    },
    getMetricValue(item) {
      return this.metricMode === 'bytes' ? Number(item.bytes || 0) : Number(item.packets || 0);
    },
    getProgressWidth(item) {
      if (!this.topkList.length) return 0;
      const max = Math.max(...this.topkList.map((entry) => this.getMetricValue(entry)), 0);
      if (!max) return 0;
      return (this.getMetricValue(item) / max * 100).toFixed(2);
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
      if (bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    handleResize() {
      this.pieInstance?.resize();
      this.barInstance?.resize();
    }
  }
};
</script>

<style scoped>
.rank-inner-container { display: flex; flex-direction: column; gap: 24px; height: 100%; box-sizing: border-box; }
.top-row { display: flex; gap: 24px; height: 320px; }
.chart-box { flex: 1; background: var(--glass-bg, rgba(255,255,255,0.55)); backdrop-filter: var(--glass-blur, blur(12px)); -webkit-backdrop-filter: var(--glass-blur, blur(12px)); border-radius: 24px; padding: 24px; display: flex; flex-direction: column; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); }
.box-title { font-size: 16px; font-weight: 600; color: #000000; margin: 0; letter-spacing: -0.32px; }
.chart-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 16px; }
.echarts-container { flex: 1; width: 100%; }
.bottom-row { flex: 1; min-height: 0; }
.table-card { background: var(--glass-bg, rgba(255,255,255,0.55)); backdrop-filter: var(--glass-blur, blur(12px)); -webkit-backdrop-filter: var(--glass-blur, blur(12px)); border-radius: 24px; padding: 24px; height: 100%; display: flex; flex-direction: column; box-sizing: border-box; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); }
.table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.refresh-btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; background: #ffffff; color: var(--clay-text-muted, #9f9b93); }
.table-wrapper { flex: 1; overflow-y: auto; }
.ui-data-table th { padding: 12px 16px; font-size: 13px; color: var(--clay-text-muted, #9f9b93); font-weight: 600; border-bottom: 1px solid var(--clay-border, #dad4c8); background: rgba(255,255,255,0.85); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); z-index: 1; }
.ui-data-table td { padding: 16px; border-bottom: 1px solid var(--clay-border-light, #eee9df); font-size: 14px; }
.rank-num { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; background: var(--clay-bg, #faf9f7); border-radius: 6px; font-size: 12px; font-weight: 700; color: var(--clay-text-secondary, #55534e); border: 1px solid var(--clay-border, #dad4c8); }
.rank-num.top-three { background: var(--clay-ube-light, #c1b0ff); color: var(--clay-ube, #43089f); border-color: var(--clay-ube-light, #c1b0ff); }
.ip-text { font-family: 'Space Mono', monospace; font-weight: 600; color: #000000; }
.proto-tag { display: inline-block; padding: 2px 8px; background: #f0f8ff; color: var(--clay-blueberry, #01418d); border-radius: 999px; font-size: 11px; font-weight: 600; margin-right: 4px; border: 1px solid var(--clay-border-light, #eee9df); }
.progress-container { width: 100%; height: 8px; background: var(--clay-border-light, #eee9df); border-radius: 4px; overflow: hidden; }
.progress-bar { height: 100%; background: linear-gradient(90deg, var(--clay-ube, #43089f), var(--clay-ube-light, #c1b0ff)); transition: width 0.5s ease; }
.data-text { font-family: 'Space Mono', monospace; color: var(--clay-text-secondary, #55534e); font-size: 13px; }
.empty-state { padding: 60px; text-align: center; color: var(--clay-text-muted, #9f9b93); }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
</style>
