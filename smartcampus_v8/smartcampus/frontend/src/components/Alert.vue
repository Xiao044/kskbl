<template>
  <div class="alert-inner-container">
    <div class="top-section">
      <div class="radar-stage">
        <div class="radar-stage__inner" ref="radarChart"></div>
      </div>

      <div class="right-panel">
        <div class="summary-area">
          <h3 class="section-title">安全防御引擎状态</h3>
          <div class="status-banner">
            <span class="pulse-ring"></span>
            <span class="banner-text">Heuristic IDS 启发式多维巡检中</span>
          </div>

          <div class="stats-grid">
            <div class="stat-box">
              <span class="label">累计拦截 (次)</span>
              <span class="value default">{{ alerts.length }}</span>
            </div>
            <div class="stat-box danger-box">
              <span class="label">高危致命 (次)</span>
              <span class="value danger">{{ highRiskCount }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="bottom-section">
      <div class="table-header">
        <h3 class="section-title">实时安全告警日志 (SecLog)</h3>
      </div>

      <div class="table-scroll-area">
        <table>
          <thead>
            <tr>
              <th>时间</th>
              <th>威胁类型与特征</th>
              <th>攻击源 (IP)</th>
              <th>源区域</th>
              <th>地理溯源</th>
              <th>目标 (IP)</th>
              <th>载荷</th>
              <th>包数</th>
              <th>危险等级</th>
              <th>动作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in aggregatedAlerts" :key="item.aggregateKey">
              <td class="time-text">{{ item.time }}</td>
              <td class="threat-text">
                <span class="emoji">{{ item.icon }}</span> {{ item.type }}
                <span v-if="item.count > 1" class="count-badge" :title="`累计攻击 ${item.count} 次`">x{{ item.count }}</span>
              </td>
              <td class="ip-text">{{ item.src_ip }}</td>
              <td><span class="zone-tag-alert">{{ item.src_zone || '外部网络' }}</span></td>
              <td><span class="geo-tag">{{ formatGeo(item.geo) }}</span></td>
              <td class="ip-dst-text">{{ item.dst_ip || 'N/A' }}</td>
              <td class="bytes-text">{{ item.bytes ? formatBytes(item.bytes) : '--' }}</td>
              <td class="packets-text">{{ item.packets || '--' }}</td>
              <td>
                <span :class="['level-badge', item.level]">
                  {{ item.level === 'high' ? '高危' : (item.level === 'medium' ? '中危' : '低危') }}
                </span>
              </td>
              <td class="action-text"><span class="dot safe"></span> 阻断</td>
            </tr>
            <tr v-if="aggregatedAlerts.length === 0">
              <td colspan="10" class="empty-state">
                <div class="empty-icon">✨</div>
                <p>当前网络环境纯净，暂无威胁告警</p>
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
  name: 'Alert',
  props: { alerts: { type: Array, default: () => [] } },
  data() {
    return {
      echarts: null,
      radarInstance: null
    }
  },
  computed: {
    aggregatedAlerts() {
      const aggregated = new Map();

      this.alerts.forEach((item) => {
        const key = `${item.src_ip || 'unknown'}__${item.type || '未知威胁'}`;
        const count = Number(item.count || 1);
        const bytes = Number(item.bytes || 0);

        if (aggregated.has(key)) {
          const existing = aggregated.get(key);
          existing.count += count;
          existing.bytes = (existing.bytes || 0) + bytes;
          if (String(item.time || '') >= String(existing.time || '')) {
            aggregated.set(key, {
              ...existing,
              ...item,
              count: existing.count,
              bytes: existing.bytes,
              aggregateKey: key
            });
          }
          return;
        }

        aggregated.set(key, {
          ...item,
          count,
          bytes,
          aggregateKey: key
        });
      });

      return Array.from(aggregated.values()).sort((a, b) => String(b.time || '').localeCompare(String(a.time || '')));
    },
    highRiskCount() { return this.alerts.filter(a => a.level === 'high').length; },
    threatStats() {
      const stats = { 'DDoS攻击': 0, '端口扫描': 0, '蠕虫病毒': 0, '异常爬虫': 0, '数据外泄': 0 };
      this.alerts.forEach(item => { if (stats[item.category] !== undefined) stats[item.category]++; });
      return stats;
    }
  },
  watch: {
    alerts: {
      handler() { this.updateRadarChart(); }
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.initRadarChart();
      window.addEventListener('resize', this.resizeChart);
    });
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeChart);
    if (this.radarInstance) this.radarInstance.dispose();
  },
  methods: {
    async initRadarChart() {
      const echartsModule = await import('echarts');
      if (!this.$refs.radarChart) return;

      this.echarts = echartsModule;
      this.radarInstance = echartsModule.init(this.$refs.radarChart);
      this.updateRadarChart();
    },
    formatBytes(bytes) {
      if (!bytes || bytes === 0) return '0 B';
      const k = 1024, sizes = ['B', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    formatGeo(geo) {
      if (!geo) return '--';
      const building = geo.building || '';
      const zone = geo.zone || '';
      if (building && building !== '未知') return building;
      if (zone && zone !== '未知') return zone;
      return '--';
    },
    updateRadarChart() {
      if (!this.radarInstance) return;
      const option = {
        title: {
          text: '六维威胁画像',
          textStyle: { color: '#171717', fontSize: 18, fontWeight: 800 },
          top: 0,
          left: 0
        },
        tooltip: {
          backgroundColor: '#171717',
          textStyle: { color: '#fff' },
          borderWidth: 0,
          padding: 12,
          borderRadius: 8,
          formatter: (params) => {
            const values = params.value || [];
            const labels = ['DDoS', '扫描', '蠕虫', '爬虫', '外泄'];
            return labels.map((label, index) => `${label}: ${values[index] || 0}`).join('<br/>');
          }
        },
        radar: {
          indicator: [
            { name: 'DDoS', max: Math.max(10, this.threatStats['DDoS攻击'] * 1.5) },
            { name: '扫描', max: Math.max(10, this.threatStats['端口扫描'] * 1.5) },
            { name: '蠕虫', max: Math.max(10, this.threatStats['蠕虫病毒'] * 1.5) },
            { name: '爬虫', max: Math.max(10, this.threatStats['异常爬虫'] * 1.5) },
            { name: '外泄', max: Math.max(10, this.threatStats['数据外泄'] * 1.5) }
          ],
          center: ['50%', '58%'],
          radius: '74%',
          splitNumber: 5,
          shape: 'circle',
          axisName: { color: '#52525b', fontWeight: 700, fontSize: 12 },
          splitArea: { areaStyle: { color: ['rgba(255,255,255,0.22)', 'rgba(255,255,255,0.1)'] } },
          axisLine: { lineStyle: { color: 'rgba(163, 163, 163, 0.55)' } },
          splitLine: { lineStyle: { color: 'rgba(163, 163, 163, 0.38)' } }
        },
        series: [{
          type: 'radar',
          data: [{
            value: [this.threatStats['DDoS攻击'], this.threatStats['端口扫描'], this.threatStats['蠕虫病毒'], this.threatStats['异常爬虫'], this.threatStats['数据外泄']]
          }],
          symbol: 'circle',
          symbolSize: 8,
          itemStyle: { color: '#43089f' },
          areaStyle: { color: 'rgba(67, 8, 159, 0.18)' },
          lineStyle: { width: 3, color: '#43089f' }
        }]
      };
      this.radarInstance.setOption(option);
    },
    resizeChart() {
      if (this.radarInstance) this.radarInstance.resize();
    }
  }
}
</script>

<style scoped>
.alert-inner-container { display: flex; flex-direction: column; height: 100%; padding: 24px; box-sizing: border-box; background: var(--glass-bg, rgba(255,255,255,0.55)); backdrop-filter: var(--glass-blur, blur(12px)); -webkit-backdrop-filter: var(--glass-blur, blur(12px)); border-radius: 24px; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.alert-inner-container:hover { transform: translateY(-2px); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)), 0 12px 28px rgba(0,0,0,0.08); }

.top-section { display: flex; height: 360px; gap: 24px; margin-bottom: 24px; flex-shrink: 0; }
.radar-stage { flex: 2; min-width: 0; background: linear-gradient(180deg, rgba(255,255,255,0.52) 0%, rgba(250, 249, 247, 0.7) 100%); border-radius: 20px; padding: 20px; border: 1px solid rgba(218,212,200,0.38); box-sizing: border-box; box-shadow: inset 0 1px 0 rgba(255,255,255,0.35), 0 6px 16px rgba(0,0,0,0.03); transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.radar-stage:hover { transform: translateY(-2px); box-shadow: inset 0 1px 0 rgba(255,255,255,0.35), 0 10px 22px rgba(0,0,0,0.06); }
.radar-stage__inner { width: 100%; height: 100%; }
.right-panel { flex: 1; display: flex; flex-direction: column; justify-content: center; min-width: 0; }

.summary-area { flex: 1; display: flex; flex-direction: column; justify-content: center; padding: 0 4px; }
.section-title { font-size: 18px; font-weight: 600; color: #000000; margin: 0 0 16px 0; letter-spacing: -0.36px; }

.status-banner { display: flex; align-items: center; gap: 12px; background: #f0fdf4; padding: 14px 16px; border-radius: 12px; margin-bottom: 24px; border: 1px solid var(--clay-matcha-light, #84e7a5); }
.pulse-ring { width: 10px; height: 10px; border-radius: 50%; background: var(--clay-matcha, #078a52); box-shadow: 0 0 0 4px rgba(7, 138, 82, 0.2); animation: pulse 2s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(7, 138, 82, 0.4); } 70% { box-shadow: 0 0 0 8px rgba(7, 138, 82, 0); } 100% { box-shadow: 0 0 0 0 rgba(7, 138, 82, 0); } }
.banner-text { color: var(--clay-matcha, #078a52); font-weight: 600; font-size: 13px; }

.stats-grid { display: flex; gap: 16px; }
.stat-box { flex: 1; background: linear-gradient(180deg, rgba(255,255,255,0.48) 0%, rgba(250, 249, 247, 0.72) 100%); padding: 16px; border-radius: 16px; display: flex; flex-direction: column; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: inset 0 1px 0 rgba(255,255,255,0.35), 0 4px 12px rgba(0,0,0,0.03); transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1); }
.stat-box:hover { transform: translateY(-2px); box-shadow: inset 0 1px 0 rgba(255,255,255,0.35), 0 10px 20px rgba(0,0,0,0.06); }
.danger-box { background: linear-gradient(180deg, #fff4f5 0%, #ffecef 100%); border-color: rgba(252, 121, 129, 0.3); }
.label { font-size: 12px; color: var(--clay-text-muted, #9f9b93); margin-bottom: 4px; font-weight: 500; }
.value { font-size: 32px; font-weight: 800; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); }
.value.default { color: #000000; }
.value.danger { color: var(--clay-pomegranate, #fc7981); }

.bottom-section { flex: 1; display: flex; flex-direction: column; overflow: hidden; border-top: 1px solid rgba(218,212,200,0.18); padding-top: 4px; }
.table-scroll-area { flex: 1; overflow-y: auto; }
.table-scroll-area::-webkit-scrollbar { width: 4px; }
.table-scroll-area::-webkit-scrollbar-thumb { background: var(--clay-border, #dad4c8); border-radius: 4px; }

table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 12px 16px; color: var(--clay-text-muted, #9f9b93); font-size: 13px; font-weight: 600; border-bottom: 1px solid var(--clay-border, #dad4c8); position: sticky; top: 0; background: rgba(255,255,255,0.85); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); z-index: 10; }
td { padding: 16px; font-size: 14px; border-bottom: 1px solid var(--clay-border-light, #eee9df); color: #000000; }
tr:hover td { background: var(--clay-bg, #faf9f7); }

.time-text { color: var(--clay-text-muted, #9f9b93); font-family: 'Space Mono', monospace; font-size: 13px; }
.threat-text { font-weight: 600; color: #000000; }
.ip-text { font-family: 'Space Mono', monospace; font-weight: 600; color: var(--clay-ube, #43089f); }
.count-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 28px;
  height: 22px;
  margin-left: 10px;
  padding: 0 10px;
  border-radius: 999px;
  background: linear-gradient(180deg, #d6c6ff 0%, #a78bfa 100%);
  color: #2d1459;
  font-size: 11px;
  font-weight: 800;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.45), 0 2px 0 rgba(92, 57, 170, 0.8);
}

.zone-tag-alert { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; background: var(--clay-pomegranate-bg, #fff0f1); color: var(--clay-pomegranate, #fc7981); border: 1px solid rgba(252, 121, 129, 0.2); }
.geo-tag { display: inline-block; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 600; background: #f0f8ff; color: var(--clay-blueberry, #01418d); border: 1px solid rgba(1, 65, 141, 0.15); }

.ip-dst-text { font-family: 'Space Mono', monospace; color: var(--clay-text-secondary, #55534e); font-size: 13px; }
.bytes-text { font-family: 'Space Mono', monospace; color: #000000; font-weight: 600; font-size: 13px; }
.packets-text { font-family: 'Space Mono', monospace; color: var(--clay-text-secondary, #55534e); font-size: 13px; }

.level-badge { padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; text-align: center; display: inline-block; }
.level-badge.high { background: #fef2f2; color: var(--clay-pomegranate, #fc7981); border: 1px solid rgba(252, 121, 129, 0.3); }
.level-badge.medium { background: #fef3c7; color: var(--clay-lemon, #d08a11); border: 1px solid rgba(251, 189, 65, 0.3); }

.action-text { display: flex; align-items: center; gap: 6px; color: var(--clay-text-muted, #9f9b93); font-size: 13px; }
.dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.dot.safe { background: var(--clay-matcha, #078a52); }

.empty-state { text-align: center; padding: 60px 0 !important; color: var(--clay-text-muted, #9f9b93); }
.empty-icon { font-size: 40px; margin-bottom: 16px; opacity: 0.5; }
</style>
