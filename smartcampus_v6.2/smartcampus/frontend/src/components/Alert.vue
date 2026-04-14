<template>
  <div class="alert-inner-container">
    <div class="top-section">
      <div class="chart-area" ref="radarChart"></div>
      
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
              <th>命中协议</th>
              <th>危险等级</th>
              <th>动作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in reversedAlerts" :key="index">
              <td class="time-text">{{ item.time }}</td>
              <td class="threat-text">
                <span class="emoji">{{ item.icon }}</span> {{ item.type }}
              </td>
              <td class="ip-text">{{ item.src_ip }}</td>
              <td><span class="tag-gray">{{ item.target }}</span></td>
              <td>
                <span :class="['level-badge', item.level]">
                  {{ item.level === 'high' ? '高危' : (item.level === 'medium' ? '中危' : '低危') }}
                </span>
              </td>
              <td class="action-text"><span class="dot safe"></span> 阻断</td>
            </tr>
            <tr v-if="alerts.length === 0">
              <td colspan="6" class="empty-state">
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
import * as echarts from 'echarts';

export default {
  name: 'Alert',
  props: { alerts: { type: Array, default: () => [] } },
  data() { return { radarInstance: null } },
  computed: {
    reversedAlerts() { return [...this.alerts].reverse(); },
    highRiskCount() { return this.alerts.filter(a => a.level === 'high').length; },
    threatStats() {
      const stats = { 'DDoS攻击': 0, '端口扫描': 0, '蠕虫病毒': 0, '异常爬虫': 0, '数据外泄': 0 };
      this.alerts.forEach(item => { if (stats[item.category] !== undefined) stats[item.category]++; });
      return stats;
    }
  },
  watch: { alerts: { handler() { this.updateRadarChart(); }, deep: true } },
  mounted() {
    this.$nextTick(() => {
      this.radarInstance = echarts.init(this.$refs.radarChart);
      this.updateRadarChart();
      window.addEventListener('resize', this.resizeChart);
    });
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.resizeChart);
    if (this.radarInstance) this.radarInstance.dispose();
  },
  methods: {
    updateRadarChart() {
      if (!this.radarInstance) return;
      const option = {
        tooltip: { backgroundColor: '#171717', textStyle: { color: '#fff' }, borderWidth: 0, padding: 12, borderRadius: 8 },
        radar: {
          indicator: [ 
            { name: 'DDoS', max: Math.max(10, this.threatStats['DDoS攻击'] * 1.5) }, 
            { name: '扫描', max: Math.max(10, this.threatStats['端口扫描'] * 1.5) }, 
            { name: '蠕虫', max: Math.max(10, this.threatStats['蠕虫病毒'] * 1.5) }, 
            { name: '爬虫', max: Math.max(10, this.threatStats['异常爬虫'] * 1.5) }, 
            { name: '外泄', max: Math.max(10, this.threatStats['数据外泄'] * 1.5) } 
          ],
          center: ['50%', '50%'], radius: '65%', splitNumber: 4, shape: 'circle',
          axisName: { color: '#52525b', fontWeight: 600 },
          splitArea: { areaStyle: { color: ['transparent'] } },
          axisLine: { lineStyle: { color: '#e4e4e7' } },
          splitLine: { lineStyle: { color: '#e4e4e7' } }
        },
        series: [{
          type: 'radar',
          data: [{ 
            value: [this.threatStats['DDoS攻击'], this.threatStats['端口扫描'], this.threatStats['蠕虫病毒'], this.threatStats['异常爬虫'], this.threatStats['数据外泄']] 
          }],
          itemStyle: { color: '#43089f' }, // Ube 深紫
          areaStyle: { color: 'rgba(67, 8, 159, 0.15)' },
          lineStyle: { width: 2 }
        }]
      };
      this.radarInstance.setOption(option);
    },
    resizeChart() { if (this.radarInstance) this.radarInstance.resize(); }
  }
}
</script>

<style scoped>
.alert-inner-container { display: flex; flex-direction: column; height: 100%; padding: 24px; box-sizing: border-box; background: var(--glass-bg, rgba(255,255,255,0.55)); backdrop-filter: var(--glass-blur, blur(12px)); -webkit-backdrop-filter: var(--glass-blur, blur(12px)); border-radius: 24px; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); }

.top-section { display: flex; height: 260px; gap: 32px; margin-bottom: 24px; }
.chart-area { flex: 1.2; background: rgba(250, 249, 247, 0.5); border-radius: 16px; }
.summary-area { flex: 1; display: flex; flex-direction: column; justify-content: center; }

.section-title { font-size: 16px; font-weight: 600; color: #000000; margin: 0 0 16px 0; letter-spacing: -0.32px; }

.status-banner { display: flex; align-items: center; gap: 12px; background: #f0fdf4; padding: 14px 16px; border-radius: 12px; margin-bottom: 24px; border: 1px solid var(--clay-matcha-light, #84e7a5); }
.pulse-ring { width: 10px; height: 10px; border-radius: 50%; background: var(--clay-matcha, #078a52); box-shadow: 0 0 0 4px rgba(7, 138, 82, 0.2); animation: pulse 2s infinite; }
@keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(7, 138, 82, 0.4); } 70% { box-shadow: 0 0 0 8px rgba(7, 138, 82, 0); } 100% { box-shadow: 0 0 0 0 rgba(7, 138, 82, 0); } }
.banner-text { color: var(--clay-matcha, #078a52); font-weight: 600; font-size: 13px; }

.stats-grid { display: flex; gap: 16px; }
.stat-box { flex: 1; background: rgba(250, 249, 247, 0.5); padding: 16px; border-radius: 12px; display: flex; flex-direction: column; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); }
.danger-box { background: #fef2f2; border-color: rgba(252, 121, 129, 0.3); }
.label { font-size: 12px; color: var(--clay-text-muted, #9f9b93); margin-bottom: 4px; font-weight: 500; }
.value { font-size: 32px; font-weight: 800; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); }
.value.default { color: #000000; }
.value.danger { color: var(--clay-pomegranate, #fc7981); }

.bottom-section { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
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
.tag-gray { background: rgba(250, 249, 247, 0.6); padding: 4px 10px; border-radius: 6px; font-size: 12px; color: var(--clay-text-secondary, #55534e); border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); }

.level-badge { padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; text-align: center; display: inline-block; }
.level-badge.high { background: #fef2f2; color: var(--clay-pomegranate, #fc7981); border: 1px solid rgba(252, 121, 129, 0.3); }
.level-badge.medium { background: #fef3c7; color: var(--clay-lemon, #d08a11); border: 1px solid rgba(251, 189, 65, 0.3); }

.action-text { display: flex; align-items: center; gap: 6px; color: var(--clay-text-muted, #9f9b93); font-size: 13px; }
.dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; }
.dot.safe { background: var(--clay-matcha, #078a52); }

.empty-state { text-align: center; padding: 60px 0 !important; color: var(--clay-text-muted, #9f9b93); }
.empty-icon { font-size: 40px; margin-bottom: 16px; opacity: 0.5; }
</style>