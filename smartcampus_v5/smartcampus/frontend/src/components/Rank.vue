<template>
  <div class="rank-inner-container">
    <div class="top-row">
      <div class="chart-box pie-area">
        <h3 class="box-title">Top-10 节点吞吐占比</h3>
        <div class="echarts-container" ref="pieChart"></div>
      </div>
      <div class="chart-box bar-area">
        <h3 class="box-title">实时吞吐强度对比 (Mbps)</h3>
        <div class="echarts-container" ref="barChart"></div>
      </div>
    </div>

    <div class="bottom-row">
      <div class="table-card">
        <div class="table-header">
          <h3 class="box-title">全网流量大户溯源清单 (Top-10)</h3>
          <button class="refresh-btn" @click="fetchTopK" :disabled="loading">
            {{ loading ? '同步中...' : '手动刷新' }}
          </button>
        </div>
        
        <div class="table-wrapper">
          <table v-if="topkList.length">
            <thead>
              <tr>
                <th width="60">排名</th>
                <th>源地址 (Source)</th>
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
                <td class="ip-text">{{ item.src_ip }}</td>
                <td class="ip-text">{{ item.dst_ip }}</td>
                <td>
                  <span class="proto-tag" v-for="p in item.protocols" :key="p">{{ p }}</span>
                </td>
                <td>
                  <div class="progress-container">
                    <div class="progress-bar" :style="{ width: getProgressWidth(item.bytes) + '%' }"></div>
                  </div>
                </td>
                <td class="data-text">{{ formatBytes(item.bytes) }}</td>
                <td class="data-text">{{ item.packets.toLocaleString() }}</td>
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
import * as echarts from 'echarts';

export default {
  name: 'Rank',
  data() {
    return {
      topkList: [],
      loading: false,
      pieInstance: null,
      barInstance: null,
      timer: null
    };
  },
  mounted() {
    this.initCharts();
    this.fetchTopK();
    // 每 5 秒自动同步一次 Top-K 数据
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
        const res = await fetch('http://localhost:8000/api/topk', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (res.status === 401) {
          this.$emit('logout'); 
          return;
        }
        
        const data = await res.json();
        this.topkList = data.top10 || [];
        this.updateCharts();
      } catch (err) {
        console.error("排行数据同步失败", err);
      } finally {
        this.loading = false;
      }
    },
    initCharts() {
      this.pieInstance = echarts.init(this.$refs.pieChart);
      this.barInstance = echarts.init(this.$refs.barChart);
      
      const commonOption = {
        textStyle: { fontFamily: 'Inter' },
        animationDuration: 1000
      };
      
      this.pieInstance.setOption({
        ...commonOption,
        tooltip: { trigger: 'item', backgroundColor: '#171717', textStyle: { color: '#fff' } },
        series: [{
          type: 'pie', radius: ['40%', '70%'], avoidLabelOverlap: false,
          itemStyle: { borderRadius: 8, borderColor: '#fff', borderWidth: 2 },
          label: { show: false },
          data: []
        }],
        color: ['#6366f1', '#8b5cf6', '#a855f7', '#d946ef', '#ec4899', '#f43f5e', '#f97316', '#eab308', '#22c55e', '#06b6d4']
      });

      this.barInstance.setOption({
        ...commonOption,
        tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' }, backgroundColor: '#171717', textStyle: { color: '#fff' } },
        grid: { left: '3%', right: '4%', bottom: '3%', top: '5%', containLabel: true },
        xAxis: { type: 'value', splitLine: { lineStyle: { type: 'dashed' } } },
        yAxis: { type: 'category', data: [], axisLine: { show: false }, axisTick: { show: false } },
        series: [{
          type: 'bar', data: [], itemStyle: { borderRadius: [0, 4, 4, 0], color: '#6366f1' },
          barWidth: '60%'
        }]
      });
    },
    updateCharts() {
      if (!this.topkList.length) return;

      const pieData = this.topkList.map(item => ({ name: item.src_ip, value: item.bytes }));
      this.pieInstance.setOption({ series: [{ data: pieData }] });

      const barY = this.topkList.slice(0, 5).reverse().map(item => item.src_ip);
      const barX = this.topkList.slice(0, 5).reverse().map(item => (item.bytes * 8 / 1024 / 1024).toFixed(2));
      this.barInstance.setOption({
        yAxis: { data: barY },
        series: [{ data: barX }]
      });
    },
    getProgressWidth(bytes) {
      if (!this.topkList.length) return 0;
      const max = this.topkList[0].bytes;
      return (bytes / max * 100).toFixed(2);
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
}
</script>

<style scoped>
.rank-inner-container { display: flex; flex-direction: column; gap: 24px; height: 100%; box-sizing: border-box; }

.top-row { display: flex; gap: 24px; height: 320px; }
.chart-box { flex: 1; background: #ffffff; border-radius: 20px; padding: 24px; display: flex; flex-direction: column; }
.box-title { font-size: 16px; font-weight: 700; color: #1e293b; margin: 0 0 16px 0; }
.echarts-container { flex: 1; width: 100%; }

.bottom-row { flex: 1; min-height: 0; }
.table-card { background: #ffffff; border-radius: 20px; padding: 24px; height: 100%; display: flex; flex-direction: column; box-sizing: border-box; }

.table-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.refresh-btn { padding: 8px 16px; background: #f1f5f9; border: none; border-radius: 8px; font-size: 13px; font-weight: 600; color: #64748b; cursor: pointer; transition: all 0.2s; }
.refresh-btn:hover { background: #e2e8f0; color: #1e293b; }

.table-wrapper { flex: 1; overflow-y: auto; }
table { width: 100%; border-collapse: collapse; }
th { text-align: left; padding: 12px 16px; font-size: 13px; color: #64748b; font-weight: 600; border-bottom: 1px solid #f1f5f9; position: sticky; top: 0; background: #fff; z-index: 1; }
td { padding: 16px; border-bottom: 1px solid #f8fafc; font-size: 14px; vertical-align: middle; }

.rank-num { width: 24px; height: 24px; display: flex; align-items: center; justify-content: center; background: #f1f5f9; border-radius: 6px; font-size: 12px; font-weight: 700; color: #64748b; }
.rank-num.top-three { background: #6366f1; color: #fff; }

.ip-text { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: #1e293b; }
.proto-tag { display: inline-block; padding: 2px 8px; background: #eff6ff; color: #3b82f6; border-radius: 4px; font-size: 11px; font-weight: 600; margin-right: 4px; }

.progress-container { width: 100%; height: 8px; background: #f1f5f9; border-radius: 4px; overflow: hidden; }
.progress-bar { height: 100%; background: linear-gradient(90deg, #6366f1, #a855f7); transition: width 0.5s ease; }

.data-text { font-family: 'JetBrains Mono', monospace; color: #64748b; font-size: 13px; }

.empty-state { padding: 60px; text-align: center; color: #94a3b8; }
.empty-icon { font-size: 48px; margin-bottom: 16px; }
</style>