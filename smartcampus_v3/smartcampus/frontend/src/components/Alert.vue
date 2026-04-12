<template>
  <div class="alert-container">
    <div class="charts-row">
      <div class="chart-box" ref="radarChart"></div>
      
      <div class="alert-summary">
        <h3 class="box-title">动态威胁感知引擎状态</h3>
        
        <div class="engine-status">
          <div class="status-indicator scanning"></div>
          <span class="status-text">启发式多维特征匹配中... (Heuristic IDS)</span>
        </div>
        
        <div class="alert-stats">
          <div class="stat-item">
            <span class="stat-label">累计拦截记录</span>
            <span class="num blue">{{ alerts.length }}</span>
          </div>
          <div class="stat-item danger">
            <span class="stat-label">高危致命告警</span>
            <span class="num red">{{ highRiskCount }}</span>
          </div>
        </div>
      </div>
    </div>

    <div class="table-box">
      <div class="table-header">
        <h3 class="box-title">实时安全告警日志 (SecLog)</h3>
        <span class="badge" v-if="alerts.length > 0">{{ alerts.length }} 条记录</span>
      </div>
      
      <div class="table-wrapper">
        <table>
          <thead>
            <tr>
              <th>告警时间</th>
              <th>威胁类型与特征描述</th>
              <th>源 IP (攻击方)</th>
              <th>命中业务/协议</th>
              <th>危险等级</th>
              <th>防御动作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(item, index) in reversedAlerts" :key="index">
              <td class="time-col">{{ item.time }}</td>
              <td class="threat-col">
                <span class="icon">{{ item.icon }}</span> {{ item.type }}
              </td>
              <td class="ip-col">{{ item.src_ip }}</td>
              <td><span class="proto-tag">{{ item.target }}</span></td>
              <td>
                <span :class="['risk-badge', item.level]">{{ item.level === 'high' ? '高危' : (item.level === 'medium' ? '中危' : '低危') }}</span>
              </td>
              <td class="status-col">
                <span class="dot safe"></span> 流量封堵 / 阻断
              </td>
            </tr>
            <tr v-if="alerts.length === 0">
              <td colspan="6" class="empty-text">
                <div class="empty-icon">🛡️</div>
                当前网络环境安全，各项安全规则巡检未见异常
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
  props: {
    flow: Array,
    alerts: { // 🌟 现在直接从属性接收后端的判断结果
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      radarInstance: null
    }
  },
  computed: {
    reversedAlerts() {
      return [...this.alerts].reverse();
    },
    highRiskCount() {
      return this.alerts.filter(a => a.level === 'high').length;
    },
    // 动态统计各个类别的报警数量以渲染雷达图
    threatStats() {
      const stats = { 'DDoS攻击': 0, '端口扫描': 0, '蠕虫病毒': 0, '异常爬虫': 0, '数据外泄': 0 };
      this.alerts.forEach(item => {
        if (stats[item.category] !== undefined) {
          stats[item.category]++;
        }
      });
      return stats;
    }
  },
  watch: {
    // 当后端的告警数据发生变化时，重绘画布
    alerts: {
      handler() {
        this.updateRadarChart();
      },
      deep: true
    }
  },
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
        title: { text: '五维安全威胁画像', textStyle: { color: '#1e293b', fontSize: 16, fontWeight: 600 }, top: 0 },
        tooltip: { backgroundColor: 'rgba(255, 255, 255, 0.95)', borderColor: '#e2e8f0', textStyle: { color: '#334155' } },
        radar: {
          indicator: [
            { name: 'DDoS攻击', max: Math.max(10, this.threatStats['DDoS攻击'] * 1.5) },
            { name: '端口扫描', max: Math.max(10, this.threatStats['端口扫描'] * 1.5) },
            { name: '蠕虫病毒', max: Math.max(10, this.threatStats['蠕虫病毒'] * 1.5) },
            { name: '异常爬虫', max: Math.max(10, this.threatStats['异常爬虫'] * 1.5) },
            { name: '数据外泄', max: Math.max(10, this.threatStats['数据外泄'] * 1.5) }
          ],
          center: ['50%', '55%'], radius: '65%', splitNumber: 4, shape: 'polygon',
          axisName: { color: '#64748b', fontWeight: 500 },
          splitArea: { areaStyle: { color: ['rgba(239, 68, 68, 0.02)', 'rgba(239, 68, 68, 0.05)', '#ffffff', '#f8fafc'] } },
          axisLine: { lineStyle: { color: '#e2e8f0' } }, splitLine: { lineStyle: { color: '#e2e8f0' } }
        },
        series: [{
          name: '威胁特征触发次数', type: 'radar',
          data: [{
            value: [ this.threatStats['DDoS攻击'], this.threatStats['端口扫描'], this.threatStats['蠕虫病毒'], this.threatStats['异常爬虫'], this.threatStats['数据外泄'] ],
            name: '后端引擎拦截统计'
          }],
          itemStyle: { color: '#ef4444' }, areaStyle: { color: 'rgba(239, 68, 68, 0.15)' }, lineStyle: { width: 2 }
        }]
      };
      this.radarInstance.setOption(option);
    },
    resizeChart() { if (this.radarInstance) this.radarInstance.resize(); }
  }
}
</script>

<style scoped>
.alert-container { display: flex; flex-direction: column; gap: 24px; height: 100%; box-sizing: border-box; }

.charts-row { display: flex; height: 320px; min-height: 320px; gap: 24px; }
.chart-box { 
  flex: 1.5; 
  background: #ffffff; 
  border-radius: 16px; 
  padding: 24px; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); 
  border: 1px solid #f1f5f9; 
  box-sizing: border-box;
}

.alert-summary { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  background: #ffffff; 
  border-radius: 16px; 
  padding: 24px; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); 
  border: 1px solid #f1f5f9; 
  box-sizing: border-box;
}

.box-title { margin: 0 0 20px 0; color: #1e293b; font-size: 16px; font-weight: 600; }

/* 引擎状态指示器 */
.engine-status { display: flex; align-items: center; gap: 12px; margin-bottom: 30px; background: #ecfdf5; padding: 12px 16px; border-radius: 12px; border: 1px solid #d1fae5; }
.status-indicator { width: 10px; height: 10px; border-radius: 50%; background: #10b981; box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.2); }
.scanning { animation: pulse 2s infinite; }
.status-text { color: #059669; font-weight: 600; font-size: 13px; }

@keyframes pulse { 
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); } 
  70% { box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); } 
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } 
}

/* 统计方块 */
.alert-stats { display: flex; gap: 16px; flex: 1; }
.stat-item { background: #f8fafc; padding: 20px; border-radius: 12px; flex: 1; display: flex; flex-direction: column; justify-content: center; align-items: center; border: 1px solid #e2e8f0; transition: transform 0.2s; }
.stat-item:hover { transform: translateY(-2px); }
.stat-label { color: #64748b; font-size: 14px; margin-bottom: 8px; font-weight: 500; }
.num { font-size: 36px; font-weight: bold; }
.num.blue { color: #0ea5e9; }

.stat-item.danger { background: #fef2f2; border-color: #fee2e2; }
.stat-item.danger .stat-label { color: #991b1b; }
.num.red { color: #ef4444; }

/* 表格区域 */
.table-box { 
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  background: #ffffff; 
  border-radius: 16px; 
  padding: 24px; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); 
  border: 1px solid #f1f5f9; 
  overflow: hidden; 
  box-sizing: border-box;
}
.table-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.table-header .box-title { margin: 0; }
.badge { background: #fee2e2; color: #ef4444; padding: 4px 10px; border-radius: 20px; font-size: 12px; font-weight: bold; }

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

.time-col { color: #94a3b8; font-family: 'Courier New', Courier, monospace; }
.threat-col { color: #1e293b; font-weight: 600; display: flex; align-items: center; gap: 8px; }
.icon { font-size: 18px; }
.ip-col { color: #0ea5e9; font-family: 'Courier New', Courier, monospace; font-weight: 600; }

.proto-tag { display: inline-block; background: #f1f5f9; color: #475569; padding: 4px 8px; border-radius: 6px; font-size: 12px; border: 1px solid #e2e8f0; }

.risk-badge { padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: bold; }
.risk-badge.high { background: #fef2f2; color: #ef4444; border: 1px solid #fca5a5; }
.risk-badge.medium { background: #fffbeb; color: #d97706; border: 1px solid #fcd34d; }

.status-col { color: #64748b; display: flex; align-items: center; gap: 6px; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
.dot.safe { background-color: #10b981; }

.empty-text { text-align: center; color: #94a3b8; padding: 60px !important; }
.empty-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.5; filter: grayscale(100%); }
</style>