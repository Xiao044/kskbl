<template>
  <div class="realtime">
    <h2>⚡ 实时流量监控</h2>

    <div class="stats">
      <div class="card">
        <div class="title">在线IP数</div>
        <div class="value">{{ flow.length }}</div>
      </div>

      <div class="card">
        <div class="title">总流量</div>
        <div class="value">{{ totalBytes }}</div>
      </div>

      <div class="card">
        <div class="title">最大流量IP</div>
        <div class="value">{{ maxIp }}</div>
      </div>
    </div>

    <div class="table">
      <div class="row header">
        <div>源IP</div>
        <div>流量(bytes)</div>
        <div>状态</div>
      </div>

      <div
        class="row"
        v-for="item in sortedFlow"
        :key="item.src_ip"
        :class="{ danger: item.bytes > 800 }"
      >
        <div>{{ item.src_ip }}</div>
        <div>{{ item.bytes }}</div>
        <div>
          <span v-if="item.bytes > 800" class="warn">⚠ 异常</span>
          <span v-else class="ok">正常</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['flow'],

  computed: {
    // 排序（高流量在前）
    sortedFlow() {
      if (!this.flow) return []
      return [...this.flow].sort((a, b) => b.bytes - a.bytes)
    },

    // 总流量
    totalBytes() {
      if (!this.flow) return 0
      return this.flow.reduce((sum, i) => sum + (i.bytes || 0), 0)
    },

    // 最大流量 IP
    maxIp() {
      if (!this.flow || this.flow.length === 0) return '-'
      const max = this.sortedFlow[0]
      return max ? max.src_ip : '-'
    }
  }
}
</script>

<style scoped>
.realtime {
  padding: 10px;
}

.stats {
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
  font-size: 22px;
  margin-top: 8px;
  color: #38bdf8;
}

.table {
  background: #020617;
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
  background: #0f172a;
  font-weight: bold;
}

.row.danger {
  background: rgba(220, 38, 38, 0.15);
}

.warn {
  color: #ef4444;
}

.ok {
  color: #22c55e;
}
</style>