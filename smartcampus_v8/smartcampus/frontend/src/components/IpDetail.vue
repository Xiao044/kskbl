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
          <div class="chart-slot chart-slot--trend">
            <svg class="trend-svg" viewBox="0 0 640 260" preserveAspectRatio="none" aria-hidden="true">
              <line
                v-for="line in trendGridLines"
                :key="`grid-${line}`"
                x1="56"
                :y1="line"
                x2="616"
                :y2="line"
                class="trend-grid-line"
              />
              <polyline :points="trendLinePoints" class="trend-line" />
              <polyline :points="trendAreaPoints" class="trend-area" />
              <circle
                v-for="point in trendChartData.points"
                :key="`point-${point.label}`"
                :cx="point.x"
                :cy="point.y"
                class="trend-point"
                r="5"
              />
              <text
                v-for="point in trendChartData.points"
                :key="`label-${point.label}`"
                :x="point.x"
                y="244"
                text-anchor="middle"
                class="trend-axis-label"
              >
                {{ point.label }}
              </text>
            </svg>
            <div class="trend-summary">
              <div
                v-for="point in trendChartData.points"
                :key="`summary-${point.label}`"
                class="trend-summary__item"
              >
                <span class="trend-summary__time">{{ point.label }}</span>
                <strong>{{ formatMetricValue(point.value, metricMode) }}</strong>
              </div>
            </div>
          </div>
          <div v-if="!hasTrendData" class="chart-empty">暂无趋势数据，已切换为占位趋势轮廓。</div>
        </div>
        <div class="chart-card clay-card">
          <div class="card-title-row">
            <h4>协议分布</h4>
            <span class="card-caption">主协议画像</span>
          </div>
          <div class="chart-slot chart-slot--distribution">
            <div class="donut-wrap">
              <div class="donut-chart" :style="{ background: protocolDonutGradient }">
                <div class="donut-chart__inner">
                  <strong>{{ primaryProtocol }}</strong>
                  <span>协议画像</span>
                </div>
              </div>
            </div>
            <div class="distribution-list">
              <div
                v-for="item in protocolChartData"
                :key="`proto-${item.name}`"
                class="distribution-row"
              >
                <div class="distribution-row__meta">
                  <span class="distribution-dot" :style="{ background: item.color }"></span>
                  <span class="distribution-name">{{ item.name }}</span>
                </div>
                <span class="distribution-value">{{ item.percent }}%</span>
              </div>
            </div>
          </div>
        </div>
        <div class="chart-card clay-card">
          <div class="card-title-row">
            <h4>端口分布</h4>
            <span class="card-caption">当前按总活跃度展示</span>
          </div>
          <div class="chart-slot chart-slot--bars">
            <div
              v-for="item in portChartData"
              :key="`port-${item.name}`"
              class="bar-row"
            >
              <div class="bar-row__top">
                <span class="bar-row__name">{{ item.name }}</span>
                <span class="bar-row__value">{{ formatMetricValue(item.value, metricMode) }}</span>
              </div>
              <div class="bar-row__track">
                <div class="bar-row__fill" :style="{ width: `${item.percent}%` }"></div>
              </div>
            </div>
          </div>
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
      metricMode: 'bytes'
    };
  },
  watch: {
    selectedIp: {
      immediate: true,
      handler() {
        this.fetchDetail();
      }
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
    },
    metricUnit() {
      return this.metricMode === 'bytes' ? 'bytes' : 'packets';
    },
    trendChartData() {
      const fallback = [
        { label: '切片1', value: 0 },
        { label: '切片2', value: 0 },
        { label: '切片3', value: 0 },
        { label: '切片4', value: 0 }
      ];
      const source = (this.detail.trend || []).map((item) => ({
        label: item.time || '--',
        value: Number(item[this.metricUnit] || 0)
      }));
      const points = (source.length ? source : fallback).slice(-6);
      const maxValue = Math.max(...points.map((item) => item.value), 1);
      const chartLeft = 56;
      const chartTop = 26;
      const chartWidth = 560;
      const chartHeight = 176;

      return {
        points: points.map((item, index) => {
          const x = points.length === 1
            ? chartLeft + chartWidth / 2
            : chartLeft + (chartWidth / (points.length - 1)) * index;
          const ratio = item.value / maxValue;
          const y = chartTop + chartHeight - ratio * chartHeight;
          return { ...item, x, y };
        })
      };
    },
    trendLinePoints() {
      return this.trendChartData.points.map((point) => `${point.x},${point.y}`).join(' ');
    },
    trendAreaPoints() {
      const points = this.trendChartData.points;
      if (!points.length) return '';
      const start = `${points[0].x},202`;
      const middle = points.map((point) => `${point.x},${point.y}`).join(' ');
      const end = `${points[points.length - 1].x},202`;
      return `${start} ${middle} ${end}`;
    },
    trendGridLines() {
      return [42, 82, 122, 162, 202];
    },
    protocolChartData() {
      const palette = ['#43089f', '#3bd3fd', '#078a52', '#fbbd41', '#fc7981', '#01418d'];
      const source = (this.detail.protocol_dist || [])
        .map((item) => ({
          name: item.name || '未知协议',
          value: Number(item[this.metricUnit] || 0)
        }))
        .filter((item) => item.value > 0);
      const total = source.reduce((sum, item) => sum + item.value, 0);
      const normalized = (source.length ? source : [{ name: '待积累协议画像', value: 1 }]).slice(0, 6);
      const normalizedTotal = normalized.reduce((sum, item) => sum + item.value, 0) || 1;
      return normalized.map((item, index) => ({
        ...item,
        color: palette[index % palette.length],
        percent: Math.round((item.value / normalizedTotal) * 100)
      }));
    },
    protocolDonutGradient() {
      let cursor = 0;
      const segments = this.protocolChartData.map((item) => {
        const start = cursor;
        const end = cursor + item.percent;
        cursor = end;
        return `${item.color} ${start}% ${end}%`;
      });
      return `conic-gradient(${segments.join(', ')})`;
    },
    portChartData() {
      const source = (this.detail.port_dist || [])
        .map((item) => ({
          name: item.name || '端口待补充',
          value: Number(item[this.metricUnit] || 0)
        }))
        .filter((item) => item.value > 0);
      const normalized = (source.length ? source : [{ name: '待积累端口画像', value: 1 }]).slice(0, 6);
      const maxValue = Math.max(...normalized.map((item) => item.value), 1);
      return normalized.map((item) => ({
        ...item,
        percent: Math.max(12, Math.round((item.value / maxValue) * 100))
      }));
    }
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
      } catch (err) {
        this.error = `加载失败: ${err.message || '未知错误'}`;
      } finally {
        this.loading = false;
      }
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
    },
    formatMetricValue(value, mode) {
      if (mode === 'bytes') {
        return this.formatBytes(value);
      }
      return `${this.formatNumber(value)} Pkts`;
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
.chart-slot { flex: 1; width: 100%; min-height: 260px; }
.chart-slot--trend { display: flex; flex-direction: column; gap: 14px; }
.trend-svg { width: 100%; height: 220px; overflow: visible; }
.trend-grid-line { stroke: rgba(218, 212, 200, 0.55); stroke-width: 1; stroke-dasharray: 4 6; }
.trend-line { fill: none; stroke: #43089f; stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
.trend-area { fill: rgba(67, 8, 159, 0.09); stroke: none; }
.trend-point { fill: #43089f; stroke: #ffffff; stroke-width: 2; }
.trend-axis-label { fill: #9f9b93; font-size: 11px; font-weight: 700; }
.trend-summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(96px, 1fr)); gap: 10px; }
.trend-summary__item { padding: 10px 12px; border-radius: 14px; background: rgba(250,249,247,0.82); border: 1px solid rgba(218,212,200,0.35); display: flex; flex-direction: column; gap: 4px; }
.trend-summary__time { font-size: 11px; color: var(--clay-text-muted, #9f9b93); font-weight: 700; }
.trend-summary__item strong { font-size: 13px; color: #171717; }
.chart-slot--distribution { display: flex; flex-direction: column; gap: 18px; justify-content: center; }
.donut-wrap { display: flex; justify-content: center; }
.donut-chart { width: 170px; height: 170px; border-radius: 50%; display: flex; align-items: center; justify-content: center; box-shadow: inset 0 1px 0 rgba(255,255,255,0.45), 0 8px 24px rgba(0,0,0,0.04); }
.donut-chart__inner { width: 92px; height: 92px; border-radius: 50%; background: rgba(255,255,255,0.92); display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; box-shadow: inset 0 1px 0 rgba(255,255,255,0.6); padding: 8px; }
.donut-chart__inner strong { font-size: 14px; color: #171717; line-height: 1.3; word-break: break-word; }
.donut-chart__inner span { font-size: 11px; color: var(--clay-text-muted, #9f9b93); font-weight: 700; }
.distribution-list { display: flex; flex-direction: column; gap: 10px; }
.distribution-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 10px 12px; border-radius: 14px; background: rgba(250,249,247,0.82); border: 1px solid rgba(218,212,200,0.35); }
.distribution-row__meta { display: flex; align-items: center; gap: 8px; min-width: 0; }
.distribution-dot { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
.distribution-name { font-size: 12px; font-weight: 700; color: #171717; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.distribution-value { font-size: 12px; font-weight: 800; color: var(--clay-text-secondary, #55534e); }
.chart-slot--bars { display: flex; flex-direction: column; gap: 14px; justify-content: center; }
.bar-row { display: flex; flex-direction: column; gap: 8px; }
.bar-row__top { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.bar-row__name { font-size: 12px; font-weight: 700; color: #171717; }
.bar-row__value { font-size: 12px; font-weight: 800; color: var(--clay-text-secondary, #55534e); }
.bar-row__track { height: 12px; border-radius: 999px; background: rgba(218,212,200,0.38); overflow: hidden; }
.bar-row__fill { height: 100%; border-radius: 999px; background: linear-gradient(90deg, #fbbd41 0%, #f5d061 100%); box-shadow: inset 0 1px 0 rgba(255,255,255,0.35); }
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
