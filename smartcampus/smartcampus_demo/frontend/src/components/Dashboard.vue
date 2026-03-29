<template>
  <div class="dashboard">
    <h2>📊 数据总览</h2>

    <!-- 折线图 -->
    <div id="chart" class="chart"></div>

    <!-- 新增分析卡片 -->
    <div class="analysis">
      <div class="card">
        <div class="title">警告最多IP</div>
        <div class="value">{{ topAlertIp || '-' }}</div>
      </div>

      <div class="card">
        <div class="title">告警次数</div>
        <div class="value">{{ topAlertCount }}</div>
      </div>

      <div class="card">
        <div class="title">当前流量(bytes)</div>
        <div class="value">{{ topAlertBytes }}</div>
      </div>
    </div>

    <!-- 去向/详情 -->
    <div class="detail" v-if="topAlertIp">
      <h3>📍 流量去向分析</h3>
      <p><strong>源IP：</strong>{{ topAlertIp }}</p>
      <p><strong>当前流量：</strong>{{ topAlertBytes }} bytes</p>
      <p><strong>说明：</strong>该IP在当前窗口内触发异常最多，可能为高频访问源或异常扫描行为。</p>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  props: ['flow'],

  data() {
    return {
      chart: null,
      timeData: [],
      seriesData: [],

      alertCountMap: {} // 统计告警次数
    }
  },

  computed: {
    topAlertIp() {
      let maxIp = null
      let maxCount = 0

      for (let ip in this.alertCountMap) {
        if (this.alertCountMap[ip] > maxCount) {
          maxCount = this.alertCountMap[ip]
          maxIp = ip
        }
      }

      return maxIp
    },

    topAlertCount() {
      return this.topAlertIp ? this.alertCountMap[this.topAlertIp] : 0
    },

    topAlertBytes() {
      if (!this.flow || !this.topAlertIp) return 0
      const item = this.flow.find(i => i.src_ip === this.topAlertIp)
      return item ? item.bytes : 0
    }
  },

  watch: {
    flow: {
      handler(val) {
        this.update(val)
        this.computeAlerts(val)
      },
      deep: true
    }
  },

  methods: {
    // 统计告警IP
    computeAlerts(flow) {
      if (!flow) return

      flow.forEach(item => {
        if (item.bytes > 800) {
          if (!this.alertCountMap[item.src_ip]) {
            this.alertCountMap[item.src_ip] = 0
          }
          this.alertCountMap[item.src_ip]++
        }
      })
    },

    // 更新折线图
    update(flow) {
      if (!this.chart || !flow) return

      const total = flow.reduce((sum, i) => sum + (i.bytes || 0), 0)
      const now = new Date().toLocaleTimeString()

      this.timeData.push(now)
      this.seriesData.push(total)

      if (this.timeData.length > 20) {
        this.timeData.shift()
        this.seriesData.shift()
      }

      this.chart.setOption({
        xAxis: {
          data: this.timeData
        },
        series: [
          {
            data: this.seriesData
          }
        ]
      })
    },

    initChart() {
      const dom = document.getElementById('chart')
      if (!dom) return

      this.chart = echarts.init(dom)

      this.chart.setOption({
        tooltip: { trigger: 'axis' },
        xAxis: {
          type: 'category',
          data: this.timeData
        },
        yAxis: {
          type: 'value'
        },
        series: [
          {
            type: 'line',
            smooth: true,
            data: this.seriesData,
            areaStyle: {}
          }
        ]
      })
    }
  },

  mounted() {
    this.$nextTick(() => {
      this.initChart()
    })
  }
}
</script>

<style scoped>
.dashboard {
  padding: 10px;
}

.chart {
  width: 100%;
  height: 300px;
  background: #020617;
  border-radius: 10px;
  margin-bottom: 20px;
}

.analysis {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.card {
  flex: 1;
  background: #0f172a;
  padding: 15px;
  border-radius: 10px;
  text-align: center;
}

.title {
  font-size: 14px;
  color: #94a3b8;
}

.value {
  font-size: 20px;
  margin-top: 8px;
  color: #38bdf8;
}

.detail {
  background: #0f172a;
  padding: 15px;
  border-radius: 10px;
}
</style>