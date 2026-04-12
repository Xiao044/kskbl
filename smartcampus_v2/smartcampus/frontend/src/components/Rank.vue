<template>
  <div class="rank-container">
    
    <div class="card-box rank-list-box">
      <h3 class="box-title">🏆 全网大流排行榜 Top 10</h3>
      <div class="list-wrapper">
        <div 
          v-for="(item, index) in topk" 
          :key="index" 
          :class="['rank-item', `rank-${index + 1}`]"
        >
          <div class="rank-num">{{ index + 1 }}</div>
          <div class="rank-info">
            <div class="ips">
              <span class="src">{{ item.src_ip }}</span>
              <span class="arrow">→</span>
              <span class="dst">{{ item.dst_ip }}</span>
            </div>
            <div class="tags">
              <span class="tag" v-for="p in item.protocols" :key="p">{{ p }}</span>
            </div>
          </div>
          <div class="rank-stats">
            <div class="bytes">{{ formatBytes(item.bytes) }}</div>
            <div class="packets">{{ item.packets }} Pkts</div>
          </div>
        </div>
        
        <div v-if="topk.length === 0" class="empty-state">
          正在收集全网流量数据...
        </div>
      </div>
    </div>

    <div class="card-box chart-box">
      <h3 class="box-title">累计消耗流量分布</h3>
      <div class="echarts-inner" ref="barChart"></div>
    </div>

  </div>
</template>

<script>
import * as echarts from 'echarts';

export default {
  name: 'Rank',
  data() {
    return {
      topk: [],
      chartInstance: null,
      timer: null
    }
  },
  mounted() {
    this.$nextTick(() => {
      this.initChart();
      this.fetchTopK();
      this.timer = setInterval(this.fetchTopK, 2000); // 每2秒轮询一次排行榜
      window.addEventListener('resize', this.resizeChart);
    });
  },
  beforeUnmount() {
    if (this.timer) clearInterval(this.timer);
    window.removeEventListener('resize', this.resizeChart);
    if (this.chartInstance) this.chartInstance.dispose();
  },
  methods: {
    async fetchTopK() {
      try {
        const res = await fetch('http://localhost:8000/api/topk');
        const data = await res.json();
        this.topk = data.top10;
        this.updateChart();
      } catch (error) {
        console.error("无法获取 TopK 数据", error);
      }
    },
    
    initChart() {
      this.chartInstance = echarts.init(this.$refs.barChart);
      this.chartInstance.setOption({
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: 'rgba(255,255,255,0.9)', textStyle: { color: '#334155' } },
        grid: { left: '3%', right: '8%', bottom: '5%', top: '5%', containLabel: true },
        xAxis: { type: 'value', axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } } },
        yAxis: { type: 'category', data: [], axisLabel: { color: '#64748b', fontFamily: 'Courier New' }, axisLine: { lineStyle: { color: '#cbd5e1' } } },
        series: [{
          name: '累计流量 (Bytes)',
          type: 'bar',
          barWidth: '50%',
          itemStyle: { 
            borderRadius: [0, 4, 4, 0],
            color: new echarts.graphic.LinearGradient(1, 0, 0, 0, [
              { offset: 0, color: '#0ea5e9' },
              { offset: 1, color: '#38bdf8' }
            ])
          },
          data: []
        }]
      });
    },

    updateChart() {
      if (!this.chartInstance || this.topk.length === 0) return;
      
      // ECharts Y轴从下往上画，所以要把 Top 1 放在数组最后
      const reversedData = [...this.topk].reverse();
      const yAxisData = reversedData.map(item => item.src_ip);
      const seriesData = reversedData.map(item => item.bytes);

      this.chartInstance.setOption({
        yAxis: { data: yAxisData },
        series: [{ data: seriesData }]
      });
    },

    resizeChart() {
      if (this.chartInstance) this.chartInstance.resize();
    },

    formatBytes(bytes) {
      if (!bytes || bytes === 0) return '0 B';
      const k = 1024;
      const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
  }
}
</script>

<style scoped>
.rank-container { display: flex; gap: 24px; height: 100%; box-sizing: border-box; }

.card-box { 
  background: #ffffff; 
  border-radius: 16px; 
  padding: 24px; 
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03); 
  border: 1px solid #f1f5f9; 
  display: flex; 
  flex-direction: column;
}

.box-title { margin: 0 0 24px 0; color: #1e293b; font-size: 18px; font-weight: 600; }

/* 左侧列表区 */
.rank-list-box { width: 50%; min-width: 450px; }
.list-wrapper { flex: 1; overflow-y: auto; padding-right: 8px; }
.list-wrapper::-webkit-scrollbar { width: 6px; }
.list-wrapper::-webkit-scrollbar-track { background: transparent; }
.list-wrapper::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 10px; }

.rank-item { 
  display: flex; 
  align-items: center; 
  padding: 16px; 
  background: #f8fafc; 
  border-radius: 12px; 
  margin-bottom: 12px; 
  border: 1px solid #e2e8f0;
  transition: transform 0.2s;
}
.rank-item:hover { transform: translateX(4px); border-color: #cbd5e1; background: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }

/* 奖牌样式 */
.rank-num { 
  width: 36px; height: 36px; 
  border-radius: 50%; 
  background: #e2e8f0; 
  color: #64748b; 
  display: flex; align-items: center; justify-content: center; 
  font-size: 16px; font-weight: bold; 
  margin-right: 16px; 
  flex-shrink: 0;
}

/* 金牌 */
.rank-1 .rank-num { background: linear-gradient(135deg, #fef08a, #eab308); color: #713f12; box-shadow: 0 4px 8px rgba(234, 179, 8, 0.3); }
.rank-1 { border-left: 4px solid #eab308; }

/* 银牌 */
.rank-2 .rank-num { background: linear-gradient(135deg, #f1f5f9, #94a3b8); color: #0f172a; box-shadow: 0 4px 8px rgba(148, 163, 184, 0.3); }
.rank-2 { border-left: 4px solid #94a3b8; }

/* 铜牌 */
.rank-3 .rank-num { background: linear-gradient(135deg, #fed7aa, #f97316); color: #7c2d12; box-shadow: 0 4px 8px rgba(249, 115, 22, 0.3); }
.rank-3 { border-left: 4px solid #f97316; }

.rank-info { flex: 1; overflow: hidden; }
.ips { display: flex; align-items: center; gap: 8px; font-family: 'Courier New', Courier, monospace; font-size: 15px; margin-bottom: 6px; }
.src { color: #1e293b; font-weight: bold; }
.arrow { color: #94a3b8; font-size: 12px; }
.dst { color: #64748b; }

.tag { display: inline-block; background: #e0f2fe; color: #0284c7; padding: 2px 8px; border-radius: 4px; font-size: 11px; margin-right: 6px; font-weight: 500; }

.rank-stats { text-align: right; }
.bytes { font-size: 18px; font-weight: bold; color: #0ea5e9; font-family: 'Inter', sans-serif; }
.packets { font-size: 12px; color: #94a3b8; margin-top: 4px; }

/* 右侧图表区 */
.chart-box { flex: 1; }
.echarts-inner { width: 100%; height: 100%; flex: 1; min-height: 400px; }

.empty-state { padding: 40px; text-align: center; color: #94a3b8; }
</style>