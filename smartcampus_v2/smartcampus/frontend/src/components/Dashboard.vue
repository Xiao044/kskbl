<template>
  <div class="dashboard-container">
    <div class="stat-cards">
      <div class="card card-throughput">
        <div class="card-title">全网实时吞吐量</div>
        <div class="card-value throughput">
          {{ displayMbps }} <span class="unit">Mbps</span>
        </div>
      </div>
      <div class="card card-pps">
        <div class="card-title">全网实时包速率</div>
        <div class="card-value pps">
          {{ displayPPS }} <span class="unit">PPS</span>
        </div>
      </div>
      <div class="card card-active">
        <div class="card-title">监控活跃大流节点</div>
        <div class="card-value active-ips">
          {{ displayNodes }} <span class="unit">个</span>
        </div>
      </div>
      <div class="card card-proto">
        <div class="card-title">当前主要协议</div>
        <div class="card-value protocol">
          {{ displayProtocol }}
        </div>
      </div>
    </div>

    <div class="main-chart-row">
      <div class="chart-box full-width">
        <div class="echarts-inner" ref="globalTrendChart"></div>
      </div>
    </div>

    <div class="bottom-row">
      <div class="chart-box half-width">
        <div class="echarts-inner" ref="globalProtocolChart"></div>
      </div>
      
      <div class="info-box half-width">
        <h3>全网安全态势感知概览</h3>
        <ul class="status-list">
          <li>
            <span class="status-label">系统运行状态</span>
            <span class="status-value safe"><span class="dot"></span>正常抓包解析中</span>
          </li>
          <li>
            <span class="status-label">当前链路带宽</span>
            <span class="status-value">10 Gbps (持续监测)</span>
          </li>
          <li>
            <span class="status-label">异常流量预警</span>
            <span class="status-value warning">动态安全规则巡检中</span>
          </li>
          <li>
            <span class="status-label">数据接入点</span>
            <span class="status-value">核心交换机/出口网关</span>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  name: 'Dashboard',
  props: {
    flow: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      trendInstance: null,
      protocolInstance: null,
      trendData: {
        times: [],
        mbps: []
      },
      // 🌟 核心修复：引入“影子变量”，用来缓存最后的有效数值，防止卡片跳 0
      displayMbps: '0.00',
      displayPPS: 0,
      displayNodes: 0,
      displayProtocol: 'N/A'
    }
  },
  watch: {
    flow: {
      handler(newData) {
        // 🌟 核心防御逻辑：只有当后端传来的数据不为空时，才更新卡片！
        if (newData && newData.length > 0) {
          
          // 1. 计算并缓存卡片数据
          const totalBytes = newData.reduce((sum, item) => sum + item.bytes, 0);
          this.displayMbps = (totalBytes * 8 / 1024 / 1024).toFixed(2);
          
          this.displayPPS = newData.reduce((sum, item) => sum + item.packets, 0);
          this.displayNodes = newData.length;
          
          const count = {};
          newData.forEach(item => {
            item.protocols.forEach(p => {
              count[p] = (count[p] || 0) + 1;
            });
          });
          const sorted = Object.keys(count).sort((a, b) => count[b] - count[a]);
          this.displayProtocol = sorted[0] || 'Unknown';

          // 2. 只有拿到有效数据，才触发图表画图，保证 1秒1动
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
      
      this.trendInstance.setOption({
        title: { text: '宏观网络吞吐量实时波动 (Mbps)', textStyle: { color: '#1e293b', fontSize: 16, fontWeight: 600 } },
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross', lineStyle: { color: '#94a3b8' } }, backgroundColor: 'rgba(255,255,255,0.9)', borderColor: '#e2e8f0', textStyle: { color: '#334155' } },
        grid: { left: '3%', right: '3%', bottom: '5%', top: '15%', containLabel: true },
        animationDurationUpdate: 500,
        xAxis: { type: 'category', boundaryGap: false, data: [], axisLabel: { color: '#64748b' }, axisLine: { lineStyle: { color: '#cbd5e1' } } },
        yAxis: { 
          type: 'value', 
          min: 0, 
          axisLabel: { color: '#64748b' }, 
          splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } } 
        },
        series: [{
          name: '吞吐量',
          type: 'line',
          smooth: true,
          symbol: 'none',
          lineStyle: { color: '#0ea5e9', width: 3 },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(14, 165, 233, 0.3)' },
              { offset: 1, color: 'rgba(14, 165, 233, 0)' }
            ])
          },
          data: []
        }]
      });
    },

    updateTrendData() {
      const now = new Date().toLocaleTimeString();
      // 使用缓存的、永远不会异常跌0的值来画折线图
      const mbps = parseFloat(this.displayMbps);

      this.trendData.times.push(now);
      this.trendData.mbps.push(mbps);

      if (this.trendData.times.length > 60) {
        this.trendData.times.shift();
        this.trendData.mbps.shift();
      }

      this.trendInstance.setOption({
        xAxis: { data: this.trendData.times },
        series: [{ data: this.trendData.mbps }]
      });
    },

    updateProtocolChart(validData) {
      const protoCount = {};
      validData.forEach(item => {
        item.protocols.forEach(p => { 
          protoCount[p] = (protoCount[p] || 0) + item.bytes;
        });
      });
      const pieData = Object.keys(protoCount).map(key => ({ name: key, value: protoCount[key] }));

      this.protocolInstance.setOption({
        title: { text: '全网协议流量占比', textStyle: { color: '#1e293b', fontSize: 16, fontWeight: 600 } },
        tooltip: { trigger: 'item', backgroundColor: 'rgba(255,255,255,0.9)', borderColor: '#e2e8f0', textStyle: { color: '#334155' } },
        animationDurationUpdate: 800,
        series: [{
          name: '协议分布',
          type: 'pie',
          radius: ['45%', '70%'],
          center: ['50%', '55%'],
          roseType: 'area',
          itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
          label: { color: '#475569', fontWeight: 500 },
          data: pieData
        }],
        color: ['#0ea5e9', '#10b981', '#8b5cf6', '#f59e0b', '#f43f5e', '#64748b']
      });
    },

    resizeCharts() {
      if (this.trendInstance) this.trendInstance.resize();
      if (this.protocolInstance) this.protocolInstance.resize();
    }
  }
}
</script>

<style scoped>
/* 样式部分完全保持之前的明亮现代风格 */
.dashboard-container { display: flex; flex-direction: column; gap: 24px; height: 100%; box-sizing: border-box; }

.stat-cards { display: flex; gap: 24px; }
.card { 
  flex: 1; 
  position: relative; 
  background: #ffffff; 
  border-radius: 16px; 
  padding: 24px; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); 
  border: 1px solid #f1f5f9; 
  box-sizing: border-box;
}

.card-throughput { border-top: 4px solid #0ea5e9; }
.card-pps { border-top: 4px solid #8b5cf6; }
.card-active { border-top: 4px solid #10b981; }
.card-proto { border-top: 4px solid #f43f5e; }

.card-title { color: #64748b; font-size: 14px; font-weight: 500; margin-bottom: 12px; }
.card-value { font-size: 32px; font-weight: bold; font-family: 'Inter', -apple-system, sans-serif; color: #1e293b; }
.unit { font-size: 14px; color: #94a3b8; font-weight: normal; margin-left: 4px; }

.throughput { color: #0ea5e9; }
.pps { color: #8b5cf6; }
.active-ips { color: #10b981; }
.protocol { color: #f43f5e; font-size: 28px; }

.main-chart-row { 
  height: 500px; 
  min-height: 500px; 
  display: flex; 
  width: 100%; 
}

.bottom-row { 
  height: 320px; 
  min-height: 320px;
  display: flex; 
  gap: 24px; 
  width: 100%;
}

.chart-box { 
  background: #ffffff; 
  border-radius: 16px; 
  padding: 20px; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); 
  border: 1px solid #f1f5f9; 
  box-sizing: border-box;
  display: flex; 
  flex-direction: column; 
}

.full-width { width: 100%; }
.half-width { flex: 1; }

.echarts-inner {
  width: 100%;
  height: 100%;
  flex: 1;
}

.info-box { 
  background: #ffffff; 
  border-radius: 16px; 
  padding: 24px; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); 
  border: 1px solid #f1f5f9; 
  box-sizing: border-box;
}
.info-box h3 { margin: 0 0 20px 0; color: #1e293b; font-size: 16px; font-weight: 600; }
.status-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 16px; }
.status-list li { display: flex; justify-content: space-between; align-items: center; padding-bottom: 16px; border-bottom: 1px dashed #e2e8f0; }
.status-list li:last-child { border-bottom: none; padding-bottom: 0; }
.status-label { color: #64748b; font-size: 14px; font-weight: 500; }
.status-value { font-size: 14px; font-weight: 600; color: #334155; display: flex; align-items: center; gap: 6px; }

.dot { width: 8px; height: 8px; border-radius: 50%; background: #10b981; display: inline-block; }
.status-value.safe { color: #059669; }
.status-value.warning { color: #d97706; }
</style>