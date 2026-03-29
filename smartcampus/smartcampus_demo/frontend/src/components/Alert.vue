<template>
  <div class="alert">
    <h2>🚨 异常告警中心</h2>

    <!-- 告警统计 -->
    <div class="stats">
      <div class="card">
        <div class="title">当前告警数</div>
        <div class="value">{{ alerts.length }}</div>
      </div>

      <div class="card">
        <div class="title">最近告警IP</div>
        <div class="value">{{ latestIp }}</div>
      </div>
    </div>

    <!-- 告警列表 -->
    <div class="table">
      <div class="row header">
        <div>时间</div>
        <div>IP</div>
        <div>流量(bytes)</div>
        <div>状态</div>
      </div>

      <div
        class="row"
        v-for="(item, index) in alerts"
        :key="index"
        :class="{ new: index === alerts.length - 1 }"
      >
        <div>{{ item.time }}</div>
        <div>{{ item.src_ip }}</div>
        <div>{{ item.bytes }}</div>
        <div class="danger">⚠ 异常</div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  props: ['realtimeFlow'],

  data() {
    return {
      alerts: [],
      seenKeys: new Set() // 用于去重
    }
  },

  computed: {
    latestIp() {
      if (this.alerts.length === 0) return '-'
      return this.alerts[this.alerts.length - 1].src_ip
    }
  },

  watch: {
    realtimeFlow: {
      handler(val) {
        this.checkAlerts(val)
      },
      deep: true
    }
  },

  methods: {
    checkAlerts(flow) {
      if (!flow) return

      flow.forEach(item => {
        // 阈值判断（可调整）
        if (item.bytes > 800) {
          const key = item.src_ip + '_' + item.bytes

          // 去重，避免重复告警
          if (!this.seenKeys.has(key)) {
            this.seenKeys.add(key)

            this.alerts.push({
              time: new Date().toLocaleTimeString(),
              src_ip: item.src_ip,
              bytes: item.bytes
            })

            // 限制告警数量
            if (this.alerts.length > 50) {
              this.alerts.shift()
            }
          }
        }
      })
    }
  }
}
</script>

<style scoped>
.alert {
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
  color: #ef4444;
}

.table {
  background: #020617;
  border-radius: 10px;
  overflow: hidden;
}

.row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr;
  padding: 10px;
  border-bottom: 1px solid #1e293b;
}

.row.header {
  background: #0f172a;
  font-weight: bold;
}

.danger {
  color: #ef4444;
}

.new {
  background: rgba(239, 68, 68, 0.15);
}
</style>
