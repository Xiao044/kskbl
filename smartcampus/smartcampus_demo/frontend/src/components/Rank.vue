<template>
  <div class="rank">
    <h2>🏆 流量排行 Top K</h2>

    <div class="table">
      <div class="row header">
        <div>排名</div>
        <div>IP</div>
        <div>流量(bytes)</div>
        <div>占比</div>
        <div>趋势</div>
      </div>

      <div
        class="row"
        v-for="(item, index) in sortedFlow"
        :key="item.src_ip"
        :class="{ danger: item.bytes > 800 }"
      >
        <div>#{{ index + 1 }}</div>

        <div>{{ item.src_ip }}</div>

        <div>{{ item.bytes }}</div>

        <div>
          <div class="bar">
            <div
              class="bar-inner"
              :style="{ width: getPercent(item.bytes) + '%' }"
            ></div>
          </div>
        </div>

        <div>
          <span v-if="getTrend(item.src_ip) === 'up'">⬆</span>
          <span v-else-if="getTrend(item.src_ip) === 'down'">⬇</span>
          <span v-else>—</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['flow'],

  data() {
    return {
      prevRankMap: {} // 用于记录上一轮排名
    }
  },

  computed: {
    sortedFlow() {
      if (!this.flow) return []
      return [...this.flow].sort((a, b) => b.bytes - a.bytes)
    },

    maxBytes() {
      if (!this.sortedFlow.length) return 1
      return this.sortedFlow[0].bytes
    }
  },

  watch: {
    sortedFlow: {
      handler(newVal) {
        // 更新排名记录
        const newMap = {}
        newVal.forEach((item, index) => {
          newMap[item.src_ip] = index
        })
        this.prevRankMap = newMap
      },
      deep: true
    }
  },

  methods: {
    getPercent(bytes) {
      return (bytes / this.maxBytes) * 100
    },

    getTrend(ip) {
      // 简单趋势判断（可扩展）
      const prevIndex = this.prevRankMap[ip]
      const currentIndex = this.sortedFlow.findIndex(i => i.src_ip === ip)

      if (prevIndex === undefined) return null

      if (currentIndex < prevIndex) return 'up'
      if (currentIndex > prevIndex) return 'down'
      return null
    }
  }
}
</script>

<style scoped>
.rank {
  padding: 10px;
}

.table {
  background: #0f172a;
  border-radius: 10px;
  overflow: hidden;
}

.row {
  display: grid;
  grid-template-columns: 80px 1fr 1fr 2fr 80px;
  padding: 10px;
  border-bottom: 1px solid #1e293b;
  align-items: center;
}

.row.header {
  background: #020617;
  font-weight: bold;
}

.bar {
  width: 100%;
  height: 10px;
  background: #1e293b;
  border-radius: 5px;
  overflow: hidden;
}

.bar-inner {
  height: 100%;
  background: linear-gradient(90deg, #38bdf8, #22c55e);
}

.danger {
  background: rgba(220, 38, 38, 0.15);
}
</style>