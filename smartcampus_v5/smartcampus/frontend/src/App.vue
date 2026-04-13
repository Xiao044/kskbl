<template>
  <div id="main-container">
    <LoginView v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <div v-else class="app-layout">
      <aside class="sidebar">
        <div class="brand">
          <div class="logo-icon">🛡️</div>
          <div class="brand-text">
            <h2>流量监督</h2>
            <span>智慧校园态势感知系统</span>
          </div>
        </div>

        <nav class="menu">
          <a :class="{'active': currentView === 'Dashboard'}" @click="currentView = 'Dashboard'">
             全局态势看板
          </a>
          <a :class="{'active': currentView === 'Realtime'}" @click="currentView = 'Realtime'">
             瞬时活跃监控
          </a>
          <a :class="{'active': currentView === 'Rank'}" @click="currentView = 'Rank'">
             大流排行追踪
          </a>
          <a :class="{'active': currentView === 'History'}" @click="currentView = 'History'">
             历史溯源检索
          </a>
          <a :class="{'active': currentView === 'Alert'}" @click="currentView = 'Alert'">
             威胁告警雷达
            <span class="badge" v-if="alerts.length">{{ alerts.length }}</span>
          </a>
          
          <div class="menu-divider"></div>
          <a @click="handleLogout" class="logout-btn">
             退出系统
          </a>
        </nav>

        <div class="sidebar-footer">
          <div class="status-item">
            <span class="dot safe"></span> 
            探针状态：已授权
          </div>
        </div>
      </aside>

      <main class="main-wrapper">
        <header class="topbar">
          <h2 class="page-title">{{ pageTitle }}</h2>
          <div class="user-info">
            <span class="time-now">{{ currentTime }}</span>
            <div class="user-chip">管理员 (Admin)</div>
          </div>
        </header>

        <div class="content-body">
          <div class="view-container">
            <keep-alive>
              <component 
                :is="currentView" 
                :flow="currentFlow" 
                :alerts="alerts" 
              />
            </keep-alive>
          </div>

          <div class="ai-sidebar">
            <Chat />
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script>
// 完整导入你的 6 大核心组件 + 新增的 Login 组件
import LoginView from './components/LoginView.vue'
import Dashboard from './components/Dashboard.vue'
import Realtime from './components/Realtime.vue'
import Rank from './components/Rank.vue'
import History from './components/History.vue' // 补全导入
import Alert from './components/Alert.vue'
import Chat from './components/Chat.vue'

export default {
  name: 'App',
  // 完整注册所有组件
  components: { LoginView, Dashboard, Realtime, Rank, History, Alert, Chat },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem('token'),
      currentView: 'Dashboard',
      ws: null,
      currentFlow: [],
      alerts: [],
      currentTime: new Date().toLocaleTimeString()
    }
  },
  computed: {
    pageTitle() {
      // 匹配你原始设定的所有页面标题
      const titles = {
        'Dashboard': '宏观态势总览',
        'Realtime': '瞬时活跃链路切片监控',
        'Rank': '全网流量节点排行榜',
        'History': '历史流记录溯源检索',
        'Alert': '动态威胁感知雷达'
      };
      return titles[this.currentView] || '系统主页';
    }
  },
  mounted() {
    // 初始加载时，如果已登录则启动 WebSocket
    if (this.isLoggedIn) {
      this.initWebSocket();
    }
    // 启动时钟
    setInterval(() => {
      this.currentTime = new Date().toLocaleTimeString();
    }, 1000);
  },
  methods: {
    handleLoginSuccess() {
      this.isLoggedIn = true;
      this.initWebSocket();
    },
    handleLogout() {
      localStorage.removeItem('token');
      this.isLoggedIn = false;
      if (this.ws) this.ws.close();
      // 重置状态
      this.currentFlow = [];
      this.alerts = [];
    },
    initWebSocket() {
      const token = localStorage.getItem('token');
      if (!token) return;

      // 🌟 核心：连接时携带 JWT Token
      this.ws = new WebSocket(`ws://localhost:8000/ws/flow?token=${token}`);
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.flow) {
          this.currentFlow = data.flow;
        }
        if (data.alerts && data.alerts.length > 0) {
          this.alerts.push(...data.alerts);
          // 保持最近 200 条告警，防止前端卡顿
          if (this.alerts.length > 200) this.alerts.splice(0, this.alerts.length - 200);
        }
      };

      this.ws.onclose = (e) => {
        // 如果是 1008 错误，说明 Token 校验失败，强制登出
        if (e.code === 1008) {
          alert("身份认证失效，请重新登录");
          this.handleLogout();
        } else if (this.isLoggedIn) {
          // 正常断开则尝试重连
          setTimeout(() => this.initWebSocket(), 3000);
        }
      };

      this.ws.onerror = () => {
        console.error("WebSocket 连接异常");
      };
    }
  }
}
</script>

<style>
/* 核心布局样式 */
html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: #f8fafc; font-family: 'Inter', system-ui, sans-serif; }
#main-container { height: 100vh; }

.app-layout { display: flex; height: 100%; width: 100%; }

/* 侧边栏 */
.sidebar { width: 260px; background: #0f172a; color: white; display: flex; flex-direction: column; flex-shrink: 0; box-shadow: 4px 0 20px rgba(0,0,0,0.1); }
.brand { padding: 32px 24px; display: flex; align-items: center; gap: 12px; }
.logo-icon { font-size: 28px; }
.brand-text h2 { margin: 0; font-size: 18px; letter-spacing: -0.5px; }
.brand-text span { font-size: 11px; color: #94a3b8; }

.menu { flex: 1; padding: 12px; display: flex; flex-direction: column; gap: 4px; }
.menu a { padding: 12px 16px; color: #94a3b8; text-decoration: none; border-radius: 10px; font-size: 14px; cursor: pointer; transition: all 0.2s; }
.menu a:hover { background: rgba(255,255,255,0.05); color: white; }
.menu a.active { background: #6366f1; color: white; box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3); }

.menu-divider { height: 1px; background: rgba(255,255,255,0.05); margin: 12px 0; }
.logout-btn { color: #f87171 !important; border: 1px solid rgba(248, 113, 113, 0.1); }
.logout-btn:hover { background: rgba(248, 113, 113, 0.1) !important; }

.badge { float: right; background: #ef4444; font-size: 10px; padding: 2px 6px; border-radius: 10px; }

/* 主内容区 */
.main-wrapper { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.topbar { height: 72px; background: white; border-bottom: 1px solid #e2e8f0; display: flex; align-items: center; justify-content: space-between; padding: 0 32px; }
.user-chip { background: #f1f5f9; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: 600; color: #6366f1; }

.content-body { flex: 1; display: flex; gap: 24px; padding: 24px; overflow: hidden; }
.view-container { flex: 1; min-width: 0; }
.ai-sidebar { width: 380px; flex-shrink: 0; }

.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; margin-right: 6px; }
.dot.safe { background: #10b981; box-shadow: 0 0 8px rgba(16,185,129,0.5); }
</style>