amère: 03-29 16:54:23
<template>
  <div class="app">

    <!-- 左侧菜单 -->
    <div class="sidebar">
      <h2 class="logo">Net Monitor</h2>

      <div
        v-for="item in menu"
        :key="item.key"
        :class="['menu-item', { active: current === item.key }]"
        @click="switchPage(item.key)"
      >
        {{ item.label }}
      </div>
    </div>

    <!-- 右侧内容 -->
    <div class="content">

      <!-- 顶部栏 -->
      <div class="topbar">
        <div class="title">{{ currentTitle }}</div>
        <div class="time">{{ nowTime }}</div>
      </div>

      <!-- 页面 -->
      <div class="page">
        <keep-alive>
          <component
            :is="currentComponent"
            :flow="flow"
            :history="history"
            :realtimeFlow="flow"
          />
        </keep-alive>
      </div>

    </div>

  </div>
</template>

<script>
import Dashboard from './components/Dashboard.vue'
import Realtime from './components/Realtime.vue'
import History from './components/History.vue'
import Rank from './components/Rank.vue'
import Alert from './components/Alert.vue'

export default {
  components: {
    Dashboard,
    Realtime,
    History,
    Rank,
    Alert
  },

  data() {
    return {
      current: 'dashboard',
      nowTime: '',
      flow: [],
      history: [],
      ws: null,
      menu: [
        { key: 'dashboard', label: '数据总览' },
        { key: 'realtime', label: '实时流量' },
        { key: 'history', label: '历史记录' },
        { key: 'rank', label: '流量排行' },
        { key: 'alert', label: '异常告警' }
      ]
    }
  },

  computed: {
    currentComponent() {
      return this.current
    },
    currentTitle() {
      const map = {
        dashboard: '数据总览',
        realtime: '实时流量监控',
        history: '历史记录',
        rank: '流量排行',
        alert: '异常告警'
      }
      return map[this.current]
    }
  },

  methods: {
    switchPage(key) {
      this.current = key
    },

    connectWS() {
      this.ws = new WebSocket("ws://localhost:8000/ws/flow")

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data)

        this.flow = data

        // 历史记录
        data.forEach(i => {
          this.history.unshift({
            ...i,
            time: new Date().toLocaleTimeString()
          })
        })

        this.history = this.history.slice(0, 50)
      }

      this.ws.onclose = () => {
        setTimeout(() => {
          this.connectWS()
        }, 2000)
      }
    },

    updateTime() {
      this.nowTime = new Date().toLocaleString()
    }
  },

  mounted() {
    this.connectWS()

    this.updateTime()
    setInterval(this.updateTime, 1000)
  }
}
</script>

<style scoped>
.app {
  display: flex;
  height: 100vh;
  background: #0f172a;
  color: #fff;
}

.sidebar {
  width: 220px;
  background: #1e293b;
  padding: 15px;
}

.logo {
  color: #38bdf8;
  margin-bottom: 20px;
}

.menu-item {
  padding: 12px;
  margin-bottom: 8px;
  cursor: pointer;
  border-radius: 6px;
}

.menu-item:hover {
  background: #334155;
}

.menu-item.active {
  background: #08ebdf;
  color: #000;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.topbar {
  height: 60px;
  background: #020617;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}

.page {
  flex: 1;
  padding: 20px;
  overflow: auto;
}
</style>
