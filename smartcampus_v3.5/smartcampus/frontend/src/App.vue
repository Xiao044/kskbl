<template>
  <LoginView v-if="!isLoggedIn" @login-success="onLoginSuccess" />
  <div v-else class="app">

    <div class="sidebar">
      <h2 class="logo">Net Monitor</h2>

      <div class="menu-list">
        <div
          v-for="item in menu"
          :key="item.key"
          :class="['menu-item', { active: current === item.key }]"
          @click="switchPage(item.key)"
        >
          <span class="menu-text">{{ item.label }}</span>
        </div>
      </div>
    </div>

    <div class="content">

      <div class="topbar">
        <div class="title">{{ currentTitle }}</div>
        <div class="time">{{ nowTime }}</div>
      </div>

      <div class="page">
        <keep-alive>
          <component
            :is="currentComponent"
            :flow="flow"
            :history="history"
            :alerts="globalAlerts"
          />
        </keep-alive>
      </div>

    </div>

  </div>
</template>

<script>
import LoginView from './components/LoginView.vue'
import Dashboard from './components/Dashboard.vue'
import Realtime from './components/Realtime.vue'
import History from './components/History.vue'
import Rank from './components/Rank.vue'
import Alert from './components/Alert.vue'
import Chat from './components/Chat.vue'

export default {
  name: 'App',
  components: {
    LoginView,
    dashboard: Dashboard,
    realtime: Realtime,
    history: History,
    rank: Rank,
    alert: Alert,
    chat: Chat
  },

  data() {
    return {
      isLoggedIn: false,
      current: 'alert',
      nowTime: '',
      flow: [],
      history: [],
      globalAlerts: [],
      ws: null,
      menu: [
        { key: 'dashboard', label: '📊 数据总览' },
        { key: 'realtime', label: '⚡ 实时流量' },
        { key: 'history', label: '📂 历史记录' },
        { key: 'rank', label: '🏆 流量排行' },
        { key: 'alert', label: '🚨 异常告警' },
        { key: 'chat', label: '💬 工作群聊' }
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
        history: '历史流记录检索',
        rank: '全网大流排行 Top-K',
        alert: '多维态势感知告警 (后端引擎直连)',
        chat: '团队协同与网络运维 AI 助手'
      }
      return map[this.current]
    }
  },

  watch: {
    isLoggedIn(val) {
      if (val) {
        this.connectWS()
        this.updateTime()
        setInterval(this.updateTime, 1000)
      }
    }
  },

  methods: {
    onLoginSuccess() {
      this.isLoggedIn = true
    },

    switchPage(key) {
      this.current = key
    },

    connectWS() {
      this.ws = new WebSocket("ws://localhost:8000/ws/flow")

      this.ws.onmessage = (event) => {
        const payload = JSON.parse(event.data);

        if (payload.flow && Array.isArray(payload.flow)) {
          this.flow = payload.flow;

          payload.flow.forEach(item => {
            this.history.unshift({
              ...item,
              time: new Date().toLocaleTimeString()
            });
          });

          if (this.history.length > 100) {
            this.history = this.history.slice(0, 100);
          }
        } else {
          this.flow = [];
        }

        if (payload.alerts && Array.isArray(payload.alerts) && payload.alerts.length > 0) {
          this.globalAlerts.push(...payload.alerts);
          if (this.globalAlerts.length > 100) {
            this.globalAlerts = this.globalAlerts.slice(-100);
          }
        }
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

  beforeUnmount() {
    if (this.ws) {
      this.ws.close()
    }
  }
}
</script>

<style scoped>
/* 全局：柔和、明亮的背景 */
.app {
  display: flex;
  height: 100vh;
  background: #f4f7f6;
  color: #334155;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
}

/* 左侧边栏：纯白底色，精致阴影 */
.sidebar {
  width: 240px;
  background: #ffffff;
  padding: 24px 16px;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.02);
  z-index: 10;
  display: flex;
  flex-direction: column;
}

/* Logo：使用柔和的青绿色 */
.logo {
  color: #059669;
  margin-bottom: 40px;
  font-size: 20px;
  font-weight: 800;
  padding-left: 12px;
  letter-spacing: 0.5px;
}

/* 菜单列表区域 */
.menu-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 单个菜单项：圆角胶囊状 */
.menu-item {
  padding: 12px 16px;
  cursor: pointer;
  border-radius: 20px;
  transition: all 0.2s ease;
  font-size: 15px;
  font-weight: 500;
  color: #64748b;
  display: flex;
  align-items: center;
}

/* 悬浮状态 */
.menu-item:hover {
  background: #f8fafc;
  color: #334155;
}

/* 选中状态：淡绿色背景，深绿色文字 */
.menu-item.active {
  background: #ecfdf5;
  color: #059669;
  font-weight: 600;
}

/* 右侧内容区 */
.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 顶部栏：纯白，极细底边框 */
.topbar {
  height: 64px;
  background: #ffffff;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 30px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.01);
  z-index: 5;
}

.title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.time {
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
}

/* 页面容器 */
.page {
  flex: 1;
  padding: 24px 30px;
  overflow: auto;
  background: transparent;
}
</style>
