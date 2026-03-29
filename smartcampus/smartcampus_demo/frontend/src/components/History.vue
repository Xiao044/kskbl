<template>
  <div class="history">
    <h2>📜 历史流量记录</h2>

    <!-- 折线图 -->
    <div id="historyChart" class="chart"></div>

    <!-- 历史表格 -->
    <div class="table">
      <div class="row header">
        <div>时间</div>
        <div>总流量</div>
        <div>IP数量</div>
      </div>

      <div class="row" v-for="(item, index) in history" :key="index">
        <div>{{ item.time }}</div>
        <div>{{ item.total }}</div>
        <div>{{ item.count }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  props: ['flow'],

  data() {
    return {
      history: [],
      chart: null,
      timeData: [],
      totalData: []
    }
  },

  watch: {
    flow: {
      handler(val) {
        this.addRecord(val)
      },
      deep: true
    }
  },

  methods: {
    addRecord(flow) {
      if (!flow || flow.length === 0) return

      const total = flow.reduce((sum, i) => sum + (i.bytes || 0), 0)
      const time = new Date().toLocaleTimeString()

      const record = {
        time,
        total,
        count: flow.length
      }

      this.history.push(record)
      this.timeData.push(time)
      this.totalData.push(total)

      // 限制历史长度（避免内存无限增长）
      if (this.history.length > 50) {
        this.history.shift()
        this.timeData.shift()
        this.totalData.shift()
      }

      this.updateChart()
    },

    initChart() {
      const dom = document.getElementById('historyChart')
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
            name: '总流量',
            type: 'line',
            smooth: true,
            data: this.totalData,
            areaStyle: {}
          }
        ]
      })
    },

    updateChart() {
      if (!this.chart) return

      this.chart.setOption({
        xAxis: {
          data: this.timeData
        },
        series: [
          {
            data: this.totalData
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
.history {
  padding: 10px;
}

.chart {
  width: 100%;
  height: 300px;
  background: #020617;
  border-radius: 10px;
  margin-bottom: 20px;
}

.table {
  background: #0f172a;
  border-radius: 10px;
  overflow: hidden;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  padding: 10px;
  border-bottom: 1px solid #1e293b;
}

.row.header {
  font-weight: bold;
  background: #020617;
}
</style>
