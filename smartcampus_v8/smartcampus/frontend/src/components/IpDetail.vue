<template>
  <div class="ip-detail-page">
    <div class="detail-toolbar clay-card">
      <div class="detail-toolbar__left">
        <button class="back-btn" type="button" @click="$emit('back')">返回</button>
        <div>
          <div class="detail-label">IP 独立画像看板</div>
          <h3 class="detail-title">{{ selectedIp || '未选择 IP' }}</h3>
        </div>
      </div>
      <div class="detail-toolbar__right" v-if="selectedIp">
        <button class="ghost-btn" type="button" @click="$emit('analyze-ip', selectedIp)">交给 AI 分析</button>
        <button class="ghost-btn" type="button" @click="$emit('view-history', selectedIp)">查看历史检索</button>
      </div>
    </div>

    <div v-if="loading" class="placeholder clay-card">正在加载 IP 画像...</div>
    <div v-else-if="!selectedIp" class="placeholder clay-card">请从告警、历史记录或 AI 面板中选择一个 IP。</div>
    <div v-else-if="error" class="placeholder clay-card">{{ error }}</div>
    <template v-else>
      <div class="overview-panel clay-card">
        <div class="overview-item">
          <span class="overview-label">画像状态</span>
          <strong :class="['overview-value', hasAnyData ? 'has-data' : 'no-data']">{{ hasAnyData ? '已建立' : '待积累' }}</strong>
          <span class="overview-sub">{{ hasAnyData ? '当前 IP 已形成行为特征' : '当前仅检测到少量上下文' }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">区域画像</span>
          <strong class="overview-value">{{ detail.summary.zone || '未知区域' }}</strong>
          <span class="overview-sub">结合近期流量与告警来源判断</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">画像焦点</span>
          <strong class="overview-value">{{ primaryProtocol }}</strong>
          <span class="overview-sub">{{ portInsightText }}</span>
        </div>
        <div class="overview-item">
          <span class="overview-label">最新态势</span>
          <strong class="overview-value">{{ detail.summary.latest_alert_type || '暂无告警' }}</strong>
          <span class="overview-sub">关联对象 {{ detail.summary.peer_count || 0 }} 个</span>
        </div>
      </div>

      <div class="summary-grid">
        <div class="summary-card clay-card">
          <span class="summary-label">风险等级</span>
          <strong :class="['risk-text', detail.summary.risk_level]">{{ riskText(detail.summary.risk_level) }}</strong>
          <span class="summary-sub">最新告警: {{ detail.summary.latest_alert_type }}</span>
        </div>
        <div class="summary-card clay-card">
          <span class="summary-label">累计告警</span>
          <strong>{{ detail.summary.alert_count }}</strong>
          <span class="summary-sub">高危 {{ detail.summary.high_risk_count }} 条</span>
        </div>
        <div class="summary-card clay-card">
          <span class="summary-label">累计流量</span>
          <strong>{{ formatBytes(detail.summary.total_bytes) }}</strong>
          <span class="summary-sub">{{ formatNumber(detail.summary.total_packets) }} Pkts</span>
        </div>
        <div class="summary-card clay-card">
          <span class="summary-label">关联对象</span>
          <strong>{{ detail.summary.peer_count }}</strong>
          <span class="summary-sub">{{ detail.summary.zone }}</span>
        </div>
        <div class="summary-card clay-card summary-card--secondary">
          <span class="summary-label">主要协议</span>
          <strong>{{ primaryProtocol }}</strong>
          <span class="summary-sub">画像主特征</span>
        </div>
        <div class="summary-card clay-card summary-card--secondary">
          <span class="summary-label">重点端口</span>
          <strong>{{ primaryPort }}</strong>
          <span class="summary-sub">画像主触点</span>
        </div>
      </div>

      <div class="chart-grid">
        <div class="chart-card clay-card">
          <div class="card-title-row">
            <h4>流量趋势</h4>
            <div class="metric-toggle">
              <button :class="{ active: metricMode === 'bytes' }" @click="metricMode = 'bytes'">Bytes</button>
              <button :class="{ active: metricMode === 'packets' }" @click="metricMode = 'packets'">Packets</button>
            </div>
          </div>
          <div ref="trendChart" class="chart-slot"></div>
          <div v-if="!hasTrendData" class="chart-empty">暂无趋势数据，等待更多抓包切片积累</div>
        </div>
        <div class="chart-card clay-card">
          <div class="card-title-row">
            <h4>协议分布</h4>
            <span class="card-caption">主协议画像</span>
          </div>
          <div ref="protocolChart" class="chart-slot"></div>
        </div>
        <div class="chart-card clay-card">
          <div class="card-title-row">
            <h4>端口分布</h4>
            <span class="card-caption">当前按总活跃度展示</span>
          </div>
          <div ref="portChart" class="chart-slot"></div>
        </div>
      </div>

      <div class="detail-grid">
        <div class="list-card clay-card">
          <div class="card-title-row">
            <h4>近期告警</h4>
            <span>{{ detail.alerts.length }} 条</span>
          </div>
          <div v-if="detail.alerts.length" class="list-body">
            <div v-for="(alert, index) in detail.alerts" :key="`alert-${index}`" class="list-item">
              <div class="list-item__top">
                <span class="tag danger">{{ alert.type || '安全告警' }}</span>
                <span class="list-time">{{ alert.time || '--' }}</span>
              </div>
              <div class="list-main">{{ alert.src_ip || '--' }} -> {{ alert.dst_ip || 'N/A' }}</div>
              <div class="list-sub">{{ alert.src_zone || '未知区域' }}</div>
            </div>
          </div>
          <div v-else class="list-empty">当前没有直接命中的安全告警，说明该 IP 在当前窗口内风险较低。</div>
        </div>

        <div class="list-card clay-card">
          <div class="card-title-row">
            <h4>近期流量</h4>
            <span>{{ detail.flows.length }} 条</span>
          </div>
          <div v-if="detail.flows.length" class="list-body">
            <div v-for="(flow, index) in detail.flows" :key="`flow-${index}`" class="list-item">
              <div class="list-item__top">
                <span class="tag">{{ (flow.protocols && flow.protocols[0]) || 'Unknown' }}</span>
                <span class="list-time">{{ flow.time || '--' }}</span>
              </div>
              <div class="list-main">{{ flow.src_ip || '--' }} -> {{ flow.dst_ip || '--' }}</div>
              <div class="list-sub">{{ formatBytes(flow.bytes || 0) }} / {{ formatNumber(flow.packets || 0) }} Pkts</div>
            </div>
          </div>
          <div v-else class="list-empty">当前还没有积累到该 IP 的有效流量切片，可稍后再观察。</div>
        </div>

        <div class="list-card clay-card">
          <div class="card-title-row">
            <h4>关联 IP</h4>
            <span>{{ detail.peer_ips.length }} 个</span>
          </div>
          <div v-if="detail.peer_ips.length" class="peer-list">
            <button
              v-for="peer in detail.peer_ips"
              :key="peer"
              class="peer-chip"
              type="button"
              @click="$emit('view-ip', peer)"
            >
              {{ peer }}
            </button>
          </div>
          <div v-else class="list-empty">暂无可展开的关联对象，当前画像关系链较简单。</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
export default {
  name: 'IpDetail',
  emits: ['back', 'view-ip', 'view-history', 'analyze-ip'],
  props: {
    selectedIp: { type: String, default: '' }
  },
  data() {
    return {
      loading: false,
      error: '',
      detail: {
        summary: {
          risk_level: 'low',
          alert_count: 0,
          high_risk_count: 0,
          total_bytes: 0,
          total_packets: 0,
          peer_count: 0,
          zone: '未知区域',
          latest_alert_type: '暂无告警'
        },
        trend: [],
        protocol_dist: [],
        port_dist: [],
        alerts: [],
        flows: [],
        peer_ips: []
      },
      metricMode: 'bytes',
      echarts: null,
      trendInstance: null,
      protocolInstance: null,
      portInstance: null
    };
  },
  watch: {
    selectedIp: {
      immediate: true,
      handler() {
        this.fetchDetail();
      }
    },
    metricMode() {
      this.renderCharts();
    }
  },
  computed: {
    hasAnyData() {
      return Boolean(
        (this.detail.alerts && this.detail.alerts.length) ||
        (this.detail.flows && this.detail.flows.length) ||
        Number(this.detail.summary.total_bytes || 0) > 0
      );
    },
    hasTrendData() {
      return Array.isArray(this.detail.trend) && this.detail.trend.some((item) => Number(item.bytes || item.packets || 0) > 0);
    },
    primaryProtocol() {
      const item = (this.detail.protocol_dist || []).find((entry) => entry.name && entry.name !== '暂无数据');
      return item ? item.name : '暂无数据';
    },
    primaryPort() {
      const item = (this.detail.port_dist || []).find((entry) => entry.name && entry.name !== '暂无端口');
      return item ? item.name : '暂无端口';
    },
    portInsightText() {
      if (this.primaryPort && this.primaryPort !== '暂无端口') {
        return '可继续沿端口侧做细查';
      }
      return '当前抓包未保留端口明细，先按整体活跃度观察';
    }
  },
  mounted() {
    this.$nextTick(this.initCharts);
    window.addEventListener('resize', this.resizeCharts);
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeCharts);
    if (this.trendInstance) this.trendInstance.dispose();
    if (this.protocolInstance) this.protocolInstance.dispose();
    if (this.portInstance) this.portInstance.dispose();
  },
  methods: {
    defaultDetail() {
      return {
        summary: {
          risk_level: 'low',
          alert_count: 0,
          high_risk_count: 0,
          total_bytes: 0,
          total_packets: 0,
          peer_count: 0,
          zone: '未知区域',
          latest_alert_type: '暂无告警'
        },
        trend: [],
        protocol_dist: [],
        port_dist: [],
        alerts: [],
        flows: [],
        peer_ips: []
      };
    },
    resetDetail() {
      this.detail = this.defaultDetail();
    },
    async initCharts() {
      if (this.echarts || !this.$refs.trendChart || !this.$refs.protocolChart || !this.$refs.portChart) return;
      const echartsModule = await import('echarts');
      this.echarts = echartsModule;
      this.trendInstance = echartsModule.init(this.$refs.trendChart);
      this.protocolInstance = echartsModule.init(this.$refs.protocolChart);
      this.portInstance = echartsModule.init(this.$refs.portChart);
      this.renderCharts();
    },
    async fetchDetail() {
      if (!this.selectedIp) {
        this.resetDetail();
        return;
      }
      this.loading = true;
      this.error = '';
      this.resetDetail();
      try {
        const serverIp = window.location.hostname;
        const token = localStorage.getItem('token');
        const headers = token ? { Authorization: `Bearer ${token}` } : {};
        const res = await fetch(`http://${serverIp}:8000/api/ip-history?ip=${encodeURIComponent(this.selectedIp)}&limit=20`, {
          headers
        });
        if (!res.ok) {
          throw new Error(`画像数据请求失败 (${res.status})`);
        }
        const payload = await res.json();
        this.detail = {
          ...this.defaultDetail(),
          ...payload,
          summary: {
            ...this.defaultDetail().summary,
            ...(payload.summary || {})
          },
          trend: Array.isArray(payload.trend) ? payload.trend : [],
          protocol_dist: Array.isArray(payload.protocol_dist) ? payload.protocol_dist : [],
          port_dist: Array.isArray(payload.port_dist) ? payload.port_dist : [],
          alerts: Array.isArray(payload.alerts) ? payload.alerts : [],
          flows: Array.isArray(payload.flows) ? payload.flows : [],
          peer_ips: Array.isArray(payload.peer_ips) ? payload.peer_ips : []
        };
        this.$nextTick(() => {
          this.initCharts();
          this.renderCharts();
        });
      } catch (err) {
        this.error = `加载失败: ${err.message || '未知错误'}`;
      } finally {
        this.loading = false;
      }
    },
    renderCharts() {
      if (!this.trendInstance || !this.protocolInstance || !this.portInstance) return;

      const trendData = this.detail.trend || [];
      const distKey = this.metricMode === 'bytes' ? 'bytes' : 'packets';
      const unit = this.metricMode === 'bytes' ? 'Bytes' : 'Pkts';

      this.trendInstance.setOption({
        title: { text: this.selectedIp || '', top: 0, right: 0, textStyle: { color: '#9f9b93', fontSize: 12, fontWeight: 700 } },
        tooltip: { trigger: 'axis' },
        grid: { left: '3%', right: '3%', bottom: '3%', top: '12%', containLabel: true },
        xAxis: { type: 'category', data: trendData.map((item) => item.time || '--'), axisLine: { show: false }, axisTick: { show: false } },
        yAxis: { type: 'value', name: unit, splitLine: { lineStyle: { color: '#efeae0', type: 'dashed' } } },
        series: [{
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 10,
          lineStyle: { color: '#43089f', width: 3 },
          itemStyle: { color: '#43089f', borderColor: '#fff', borderWidth: 2 },
          areaStyle: { color: 'rgba(67, 8, 159, 0.12)' },
          data: trendData.map((item) => item[distKey] || 0)
        }]
      });

      this.protocolInstance.setOption({
        title: { text: '协议权重', top: 0, right: 0, textStyle: { color: '#9f9b93', fontSize: 12, fontWeight: 700 } },
        tooltip: { trigger: 'item' },
        series: [{
          type: 'pie',
          radius: ['48%', '74%'],
          itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
          label: { formatter: '{b}\n{d}%' },
          data: (this.detail.protocol_dist || []).map((item) => ({ name: item.name, value: item[distKey] || 0 }))
        }],
        color: ['#43089f', '#3bd3fd', '#078a52', '#fbbd41', '#fc7981', '#01418d']
      });

      this.portInstance.setOption({
        title: { text: '端口热度', top: 0, right: 0, textStyle: { color: '#9f9b93', fontSize: 12, fontWeight: 700 } },
        tooltip: { trigger: 'axis' },
        grid: { left: '3%', right: '3%', bottom: '3%', top: '12%', containLabel: true },
        xAxis: { type: 'value', splitLine: { lineStyle: { color: '#efeae0', type: 'dashed' } } },
        yAxis: { type: 'category', data: (this.detail.port_dist || []).map((item) => item.name).reverse(), axisLine: { show: false }, axisTick: { show: false } },
        series: [{
          type: 'bar',
          barWidth: 16,
          itemStyle: { color: '#fbbd41', borderRadius: [0, 8, 8, 0] },
          data: (this.detail.port_dist || []).map((item) => item[distKey] || 0).reverse()
        }]
      });
    },
    resizeCharts() {
      if (this.trendInstance) this.trendInstance.resize();
      if (this.protocolInstance) this.protocolInstance.resize();
      if (this.portInstance) this.portInstance.resize();
    },
    riskText(level) {
      const map = { high: '高风险', medium: '中风险', low: '低风险' };
      return map[level] || '低风险';
    },
    formatBytes(bytes) {
      const value = Number(bytes || 0);
      if (!value) return '0 B';
      const units = ['B', 'KB', 'MB', 'GB'];
      const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
      return `${(value / Math.pow(1024, index)).toFixed(index === 0 ? 0 : 2)} ${units[index]}`;
    },
    formatNumber(value) {
      return Number(value || 0).toLocaleString();
    }
  }
}
</script>

<style scoped>
.ip-detail-page { display: flex; flex-direction: column; gap: 20px; height: 100%; padding: 10px; box-sizing: border-box; }
.clay-card { background: var(--glass-bg, rgba(255,255,255,0.55)); backdrop-filter: var(--glass-blur, blur(12px)); -webkit-backdrop-filter: var(--glass-blur, blur(12px)); border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); border-radius: 24px; }
.detail-toolbar { padding: 20px 24px; display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.detail-toolbar__left, .detail-toolbar__right { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.detail-label { font-size: 12px; color: var(--clay-text-muted, #9f9b93); font-weight: 800; }
.detail-title { margin: 4px 0 0; font-size: 24px; color: #171717; }
.back-btn, .ghost-btn { border: 1px solid rgba(218,212,200,0.45); background: rgba(255,255,255,0.82); color: #171717; border-radius: 999px; padding: 10px 16px; font-size: 12px; font-weight: 800; cursor: pointer; }
.ghost-btn { background: rgba(243,238,255,0.9); color: var(--clay-ube, #43089f); }
.placeholder { padding: 32px; font-size: 14px; color: var(--clay-text-secondary, #55534e); }
.overview-panel { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; padding: 18px 20px; }
.overview-item { display: flex; flex-direction: column; gap: 6px; padding: 14px 16px; border-radius: 18px; background: rgba(250,249,247,0.74); border: 1px solid rgba(218,212,200,0.32); }
.overview-label { font-size: 11px; color: var(--clay-text-muted, #9f9b93); font-weight: 800; letter-spacing: 0.04em; text-transform: uppercase; }
.overview-value { font-size: 18px; color: #171717; line-height: 1.3; }
.overview-value.has-data { color: var(--clay-matcha, #078a52); }
.overview-value.no-data { color: var(--clay-lemon, #fbbd41); }
.overview-sub { font-size: 12px; color: var(--clay-text-secondary, #55534e); }
.summary-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 16px; }
.summary-card { padding: 20px; display: flex; flex-direction: column; gap: 8px; }
.summary-card--secondary { background: rgba(250,249,247,0.88); }
.summary-label { font-size: 12px; color: var(--clay-text-muted, #9f9b93); font-weight: 800; }
.summary-card strong { font-size: 28px; color: #171717; }
.summary-sub { font-size: 12px; color: var(--clay-text-secondary, #55534e); }
.risk-text.high { color: #fc7981; }
.risk-text.medium { color: #fbbd41; }
.risk-text.low { color: #078a52; }
.chart-grid { display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 16px; min-height: 320px; }
.chart-card, .list-card { padding: 20px; display: flex; flex-direction: column; min-height: 0; }
.chart-slot { flex: 1; min-height: 240px; }
.chart-empty { margin-top: 10px; font-size: 12px; color: var(--clay-text-muted, #9f9b93); font-weight: 700; }
.card-title-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; }
.card-title-row h4 { margin: 0; font-size: 18px; color: #171717; }
.card-caption { font-size: 11px; color: var(--clay-text-muted, #9f9b93); font-weight: 700; }
.metric-toggle { display: inline-flex; gap: 6px; background: rgba(255,255,255,0.72); border-radius: 999px; padding: 4px; }
.metric-toggle button { border: none; background: transparent; color: #55534e; border-radius: 999px; padding: 6px 10px; font-size: 11px; font-weight: 800; cursor: pointer; }
.metric-toggle button.active { background: rgba(243,238,255,0.92); color: var(--clay-ube, #43089f); }
.detail-grid { display: grid; grid-template-columns: 1.2fr 1.2fr 1fr; gap: 16px; min-height: 0; flex: 1; }
.list-body { overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
.list-item { padding: 14px; border-radius: 18px; background: rgba(250,249,247,0.88); border: 1px solid rgba(218,212,200,0.38); }
.list-item__top { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }
.list-main { font-size: 14px; font-weight: 800; color: #171717; word-break: break-all; }
.list-sub, .list-time { font-size: 12px; color: var(--clay-text-secondary, #55534e); }
.tag { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 999px; background: rgba(243,238,255,0.88); color: var(--clay-ube, #43089f); font-size: 11px; font-weight: 800; }
.tag.danger { background: rgba(255,240,241,0.92); color: #fc7981; }
.list-empty { display: flex; align-items: center; justify-content: center; min-height: 160px; padding: 16px; border-radius: 18px; background: rgba(250,249,247,0.72); border: 1px dashed rgba(218,212,200,0.48); color: var(--clay-text-secondary, #55534e); font-size: 13px; line-height: 1.7; text-align: center; }
.peer-list { display: flex; flex-wrap: wrap; gap: 10px; }
.peer-chip { border: 1px solid rgba(193,176,255,0.38); background: rgba(243,238,255,0.88); color: var(--clay-ube, #43089f); border-radius: 999px; padding: 8px 12px; font-size: 12px; font-weight: 800; cursor: pointer; }

@media (max-width: 1280px) {
  .overview-panel, .summary-grid, .chart-grid, .detail-grid { grid-template-columns: 1fr; }
}
</style>
