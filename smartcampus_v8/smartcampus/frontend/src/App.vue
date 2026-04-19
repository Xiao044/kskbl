<template>
  <div id="main-container">
    <LoginView v-if="!isLoggedIn" @login-success="handleLoginSuccess" />

    <div
      v-else
      class="app-layout"
      :class="{
        'is-sidebar-animating': isSidebarAnimating,
        'is-chat-animating': isChatAnimating
      }"
    >
      <aside class="sidebar" :class="{ 'is-collapsed': isCollapsed }">
        <div class="sidebar__toggle" @click="toggleSidebar" :title="isCollapsed ? '展开菜单' : '收起菜单'">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></svg>
        </div>

        <div class="brand">
          <img src="./clay_logo.png" alt="Logo" class="logo-icon" />
          <div class="brand-text">
            <h2>流量监督</h2>
            <span>智慧校园态势感知系统</span>
          </div>
        </div>

        <nav class="menu">
          <a :class="{'active': currentView === 'Dashboard'}" @click="switchView('Dashboard')">
            <span class="menu-icon">📊</span>
            <span class="menu-label">全局态势看板</span>
          </a>
          <a :class="{'active': currentView === 'Realtime'}" @click="switchView('Realtime')">
            <span class="menu-icon">⚡</span>
            <span class="menu-label">瞬时活跃监控</span>
          </a>
          <a :class="{'active': currentView === 'Rank'}" @click="switchView('Rank')">
            <span class="menu-icon">🏆</span>
            <span class="menu-label">大流排行追踪</span>
          </a>
          <a :class="{'active': currentView === 'History'}" @click="switchView('History')">
            <span class="menu-icon">🕐</span>
            <span class="menu-label">历史溯源检索</span>
          </a>
          <a :class="{'active': currentView === 'Alert'}" @click="switchView('Alert')">
            <span class="menu-icon">🛡️</span>
            <span class="menu-label">威胁告警雷达</span>
            <span class="badge" v-if="alerts.length">{{ alerts.length }}</span>
          </a>
          <a :class="{'active': currentView === 'IpDetail'}" @click="switchView('IpDetail')">
            <span class="menu-icon">🧭</span>
            <span class="menu-label">独立 IP 画像</span>
          </a>
        </nav>

        <!-- Mascot is teleported to body via ChatMascotHandle, but instance lives here -->
        <ChatMascotHandle
          :is-collapsed="isCollapsed"
          :is-chat-focused="chatFocused"
          :is-interactive-enabled="!isSidebarAnimating && !isChatAnimating && !isCollapsed"
          @open-chat="openChatDrawer"
        />
      </aside>

      <main class="main-wrapper">
        <header class="topbar">
          <h2 class="page-title">{{ pageTitle }}</h2>
          <div class="user-info">
            <span class="time-now">{{ currentTime }}</span>
            <!-- Account dropdown trigger -->
            <div class="account-trigger" @click="showUserMenu = !showUserMenu" v-click-outside="() => showUserMenu = false">
              <div class="user-chip" :class="{ 'is-active': showUserMenu }">
                <span class="user-avatar">A</span>
                管理员
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="chevron" :class="{ 'is-flipped': showUserMenu }"><polyline points="6 9 12 15 18 9"></polyline></svg>
              </div>
              <!-- Clay dropdown menu -->
              <transition name="dropdown">
                <div v-if="showUserMenu" class="user-dropdown">
                  <a class="dropdown-item" @click.stop="showUserMenu = false">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                    修改密码
                  </a>
                  <div class="dropdown-divider"></div>
                  <a class="dropdown-item dropdown-item--danger" @click.stop="handleLogout">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"></path><polyline points="16 17 21 12 16 7"></polyline><line x1="21" y1="12" x2="9" y2="12"></line></svg>
                    退出登录
                  </a>
                </div>
              </transition>
            </div>
          </div>
        </header>

        <div class="content-body">
          <div class="view-container">
            <component
              :is="currentView"
              :flow="currentFlow"
              :alerts="alerts"
              :selected-ip="selectedIp"
              :history-search-seed="historySearchSeed"
              :history-focus-token="historyFocusToken"
              :history-zone-seed="historyZoneSeed"
              @view-ip="openIpDetail"
              @back="closeIpDetail"
              @view-history="openHistoryForIp"
            />
          </div>
        </div>
      </main>

      <!-- Floating AI Chat Drawer -->
      <transition name="drawer-backdrop">
        <div v-if="isChatOpen" class="chat-drawer-backdrop" @click="isChatOpen = false"></div>
      </transition>
      <div class="chat-drawer" :class="{ 'is-open': isChatOpen }">
        <!-- Clay capsule pull handle -->
        <div class="drawer-handle" @click="toggleChatDrawer" :title="isChatOpen ? '收起面板' : '展开 AI 面板'">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
        </div>
        <div class="chat-drawer__panel">
          <Chat
            @chat-focus="onChatFocus"
            @chat-blur="onChatBlur"
            @message-sent="onMessageSent"
            @view-ip="openIpDetail"
            @focus-ip-history="openHistoryForIp"
            @focus-zone-history="openHistoryForZone"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineAsyncComponent } from 'vue'
// 完整导入你的 6 大核心组件 + 新增的 Login 组件
import LoginView from './components/LoginView.vue'
import ChatMascotHandle from './components/ChatMascotHandle.vue'

const Dashboard = defineAsyncComponent(() => import('./components/Dashboard.vue'))
const Realtime = defineAsyncComponent(() => import('./components/Realtime.vue'))
const Rank = defineAsyncComponent(() => import('./components/Rank.vue'))
const History = defineAsyncComponent(() => import('./components/History.vue'))
const Alert = defineAsyncComponent(() => import('./components/Alert.vue'))
const Chat = defineAsyncComponent(() => import('./components/Chat.vue'))
const IpDetail = defineAsyncComponent(() => import('./components/IpDetail.vue'))

export default {
  name: 'App',
  components: { LoginView, Dashboard, Realtime, Rank, History, Alert, Chat, IpDetail, ChatMascotHandle },
  data() {
    return {
      isLoggedIn: !!localStorage.getItem('token'),
      isCollapsed: false,
      isChatOpen: false,
      chatFocused: false,
      showUserMenu: false,
      currentView: 'Dashboard',
      ws: null,
      currentFlow: [],
      alerts: [],
      isSidebarAnimating: false,
      isChatAnimating: false,
      sidebarAnimationTimer: null,
      chatAnimationTimer: null,
      pendingFlowFrame: null,
      pendingFlowData: null,
      pendingAlertsBatch: [],
      historySearchSeed: '',
      historyZoneSeed: '',
      historyFocusToken: 0,
      selectedIp: '',
      previousView: 'Dashboard',
      currentTime: new Date().toLocaleTimeString(),
      clockTimer: null,
      nextAlertId: 1
    }
  },
  computed: {
    pageTitle() {
      const titles = {
        'Dashboard': '宏观态势总览',
        'Realtime': '瞬时活跃链路切片监控',
        'Rank': '全网流量节点排行榜',
        'History': '历史流记录溯源检索',
        'Alert': '动态威胁感知雷达',
        'IpDetail': '独立 IP 画像看板'
      };
      return titles[this.currentView] || '系统主页';
    }
  },
  watch: {
    isCollapsed() {
      this.startUiAnimation('sidebar');
    },
    isChatOpen() {
      this.startUiAnimation('chat');
    }
  },
  mounted() {
    if (this.isLoggedIn) {
      this.initWebSocket();
    }
    this.clockTimer = setInterval(() => {
      this.currentTime = new Date().toLocaleTimeString();
    }, 1000);
    // ESC: close drawer OR close dropdown
    this._escHandler = (e) => {
      if (e.key === 'Escape') {
        if (this.isChatOpen) this.isChatOpen = false;
        if (this.showUserMenu) this.showUserMenu = false;
      }
    };
    window.addEventListener('keydown', this._escHandler);
  },
  beforeUnmount() {
    if (this.clockTimer) clearInterval(this.clockTimer);
    if (this.sidebarAnimationTimer) clearTimeout(this.sidebarAnimationTimer);
    if (this.chatAnimationTimer) clearTimeout(this.chatAnimationTimer);
    if (this.pendingFlowFrame) cancelAnimationFrame(this.pendingFlowFrame);
    window.removeEventListener('keydown', this._escHandler);
  },
  methods: {
    switchView(viewName) {
      if (!viewName) return;
      if (viewName !== 'IpDetail') {
        this.previousView = viewName;
      }
      this.currentView = viewName;
    },
    startUiAnimation(target) {
      const timerKey = target === 'sidebar' ? 'sidebarAnimationTimer' : 'chatAnimationTimer';
      const flagKey = target === 'sidebar' ? 'isSidebarAnimating' : 'isChatAnimating';
      const duration = target === 'sidebar' ? 320 : 380;

      this[flagKey] = true;
      if (this[timerKey]) clearTimeout(this[timerKey]);
      this[timerKey] = setTimeout(() => {
        this[flagKey] = false;
        this[timerKey] = null;
      }, duration);
    },
    toggleSidebar() {
      this.isCollapsed = !this.isCollapsed;
    },
    toggleChatDrawer() {
      this.isChatOpen = !this.isChatOpen;
    },
    openChatDrawer() {
      if (!this.isChatOpen) {
        this.isChatOpen = true;
      }
    },
    onChatFocus() { this.chatFocused = true; },
    onChatBlur() { this.chatFocused = false; },
    onMessageSent() { this.chatFocused = false; },
    openIpDetail(ip) {
      if (!ip || typeof ip !== 'string') return;
      const normalizedIp = ip.trim();
      if (!normalizedIp || normalizedIp === 'N/A') return;

      if (this.currentView !== 'IpDetail') {
        this.previousView = this.currentView;
      }
      this.selectedIp = normalizedIp;
      this.currentView = 'IpDetail';
      this.isChatOpen = false;
      this.chatFocused = false;
    },
    closeIpDetail() {
      this.currentView = this.previousView && this.previousView !== 'IpDetail'
        ? this.previousView
        : 'Dashboard';
    },
    openHistoryForIp(ip) {
      if (!ip || typeof ip !== 'string') return;
      this.historySearchSeed = ip.trim();
      this.historyZoneSeed = '';
      this.historyFocusToken += 1;
      this.switchView('History');
      this.isChatOpen = false;
      this.chatFocused = false;
    },
    openHistoryForZone(zone) {
      if (!zone || typeof zone !== 'string') return;
      this.historySearchSeed = '';
      this.historyZoneSeed = zone.trim();
      this.historyFocusToken += 1;
      this.switchView('History');
      this.isChatOpen = false;
      this.chatFocused = false;
    },
    scheduleDataFlush() {
      if (this.pendingFlowFrame) return;

      this.pendingFlowFrame = requestAnimationFrame(() => {
        if (this.pendingFlowData) {
          this.currentFlow = this.pendingFlowData;
        }

        if (this.pendingAlertsBatch.length) {
          const incomingAlerts = this.pendingAlertsBatch.map((alert) => ({
            ...alert,
            _uid: this.nextAlertId++
          }));
          this.alerts = [...this.alerts, ...incomingAlerts].slice(-200);
        }

        this.pendingFlowData = null;
        this.pendingAlertsBatch = [];
        this.pendingFlowFrame = null;
      });
    },
    handleLoginSuccess() {
      this.isLoggedIn = true;
      this.initWebSocket();
    },
    handleLogout() {
      this.showUserMenu = false;
      localStorage.removeItem('token');
      this.isLoggedIn = false;
      if (this.ws) this.ws.close();
      this.currentFlow = [];
      this.alerts = [];
      this.selectedIp = '';
      this.previousView = 'Dashboard';
      this.currentView = 'Dashboard';
      this.pendingFlowData = null;
      this.pendingAlertsBatch = [];
      if (this.pendingFlowFrame) {
        cancelAnimationFrame(this.pendingFlowFrame);
        this.pendingFlowFrame = null;
      }
      this.nextAlertId = 1;
    },
    initWebSocket() {
      const token = localStorage.getItem('token');
      if (!token) return;

      const serverIp = window.location.hostname;
      this.ws = new WebSocket(`ws://${serverIp}:8000/ws/flow?token=${token}`);

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.flow) {
          this.pendingFlowData = data.flow;
        }
        if (data.alerts && data.alerts.length > 0) {
          this.pendingAlertsBatch.push(...data.alerts);
        }
        this.scheduleDataFlush();
      };

      this.ws.onclose = (e) => {
        if (e.code === 1008) {
          alert("身份认证失效，请重新登录");
          this.handleLogout();
        } else if (this.isLoggedIn) {
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
/* ===== Clay Design System — Global Variables ===== */
:root {
  --clay-bg: #faf9f7;
  --clay-text: #000000;
  --clay-text-muted: #9f9b93;
  --clay-text-secondary: #55534e;
  --clay-border: #dad4c8;
  --clay-border-light: #eee9df;
  --clay-shadow: rgba(0,0,0,0.1) 0px 1px 1px, rgba(0,0,0,0.04) 0px -1px 1px inset, rgba(0,0,0,0.05) 0px -0.5px 1px;
  --clay-shadow-hover: rgb(0,0,0) -7px 7px;
  --clay-matcha: #078a52;
  --clay-matcha-light: #84e7a5;
  --clay-matcha-bg: #edfcf2;
  --clay-slushie: #3bd3fd;
  --clay-slushie-bg: #eaf8ff;
  --clay-lemon: #fbbd41;
  --clay-lemon-bg: #fef9ed;
  --clay-ube: #43089f;
  --clay-ube-light: #c1b0ff;
  --clay-ube-bg: #f3eeff;
  --clay-pomegranate: #fc7981;
  --clay-pomegranate-bg: #fff0f1;
  --clay-blueberry: #01418d;
  --clay-blueberry-bg: #eef4ff;
  --clay-sidebar-w: 260px;
  --clay-sidebar-collapsed-w: 64px;
  --clay-font: 'Roobert', 'Arial', sans-serif;
  --clay-mono: 'Space Mono', monospace;
  /* Glass */
  --glass-bg: rgba(255, 255, 255, 0.55);
  --glass-bg-heavy: rgba(255, 255, 255, 0.72);
  --glass-blur: blur(12px);
  --glass-border: rgba(218, 212, 200, 0.4);
  --glass-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
}

html, body { margin: 0; padding: 0; width: 100vw; height: 100vh; overflow: hidden; background: var(--clay-bg); font-family: var(--clay-font); color: var(--clay-text); }
#main-container { height: 100vh; }

.app-layout { display: flex; height: 100%; width: 100%; padding: 16px; box-sizing: border-box; gap: 16px; background: var(--clay-bg); background-image: radial-gradient(ellipse at 5% 15%, rgba(67, 8, 159, 0.045) 0%, transparent 50%), radial-gradient(ellipse at 85% 80%, rgba(7, 138, 82, 0.04) 0%, transparent 50%), radial-gradient(ellipse at 50% 50%, rgba(59, 211, 253, 0.03) 0%, transparent 50%); }

/* ===== Sidebar — 折叠 + Clay 色彩增强 ===== */
.sidebar {
  width: var(--clay-sidebar-w);
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  color: var(--clay-text);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  border-right: none;
  border-radius: 20px;
  border: 1px solid var(--glass-border);
  box-shadow: var(--glass-shadow);
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  position: relative;
  contain: layout paint style;
  will-change: width;
}

/* 折叠状态 */
.sidebar.is-collapsed { width: var(--clay-sidebar-collapsed-w); }

/* 折叠切换按钮 */
.sidebar__toggle {
  display: flex; align-items: center; justify-content: center;
  height: 40px; margin: 12px 12px 0 12px;
  border-radius: 10px; cursor: pointer;
  background: rgba(250, 249, 247, 0.5); border: 1px solid var(--glass-border);
  color: var(--clay-text-secondary);
  transition: background-color 0.2s ease, color 0.2s ease, border-color 0.2s ease, transform 0.2s ease;
}
.sidebar__toggle:hover { background: var(--clay-ube-bg); color: var(--clay-ube); border-color: var(--clay-ube-light); }
.sidebar.is-collapsed .sidebar__toggle { margin: 12px 8px 0 8px; }

/* 品牌区 */
.brand {
  padding: 24px; display: flex; align-items: center; gap: 12px;
  border-bottom: 1px dashed var(--glass-border);
  white-space: nowrap; overflow: hidden;
  transition: padding 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.sidebar.is-collapsed .brand { padding: 20px 8px; justify-content: center; }
.logo-icon { width: 36px; height: 36px; flex-shrink: 0; object-fit: contain; border-radius: 10px; transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1), height 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
.sidebar.is-collapsed .logo-icon { width: 28px; height: 28px; }
.brand-text { overflow: hidden; transition: opacity 0.3s 0.1s, transform 0.3s 0.1s; }
.brand-text h2 { margin: 0; font-size: 18px; letter-spacing: -0.5px; font-weight: 600; color: var(--clay-text); }
.brand-text span { font-size: 11px; color: var(--clay-text-muted); }
.sidebar.is-collapsed .brand-text { opacity: 0; transform: translateX(-10px); pointer-events: none; transition: opacity 0.15s, transform 0.15s; }

/* 菜单 */
.menu { flex: 1; padding: 12px; display: flex; flex-direction: column; gap: 4px; overflow: hidden; }
.menu a {
  padding: 12px 16px; color: var(--clay-text-secondary); text-decoration: none;
  border-radius: 12px; font-size: 14px; font-weight: 500; cursor: pointer;
  transition: background-color 0.2s ease, color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
  display: flex; align-items: center; gap: 10px;
  white-space: nowrap; overflow: hidden; position: relative;
}
.menu a:hover { background: rgba(250, 249, 247, 0.5); color: var(--clay-text); }
/* Active 项：Ube 背景盒子阴影与 Clay 倾斜跳出感 */
.menu a.active {
  background: var(--clay-ube-light); color: var(--clay-ube); font-weight: 600;
  box-shadow: var(--clay-shadow), 0 2px 8px rgba(67, 8, 159, 0.15);
  transform: rotateZ(-1.5deg);
}
.menu a.active:hover { transform: rotateZ(-1.5deg) scale(1.02); }

/* 菜单图标（折叠时保留） */
.menu-icon { font-size: 18px; flex-shrink: 0; width: 24px; text-align: center; }
/* 菜单文字标签（折叠时隐藏） */
.menu-label {
  overflow: hidden;
  transition: opacity 0.3s 0.1s, transform 0.3s 0.1s;
}
.sidebar.is-collapsed .menu-label { opacity: 0; transform: translateX(-8px); width: 0; transition: opacity 0.1s, transform 0.1s; }

/* 折叠时菜单项居中图标 */
.sidebar.is-collapsed .menu a { padding: 12px 0; justify-content: center; }
.sidebar.is-collapsed .badge { display: none; }

.badge { position: absolute; right: 12px; background: var(--clay-pomegranate); font-size: 10px; padding: 2px 6px; border-radius: 10px; color: #ffffff; font-weight: 600; }

/* ===== 主内容区 — Clay 暖调 ===== */
.main-wrapper { flex: 1; display: flex; flex-direction: column; min-width: 0; gap: 16px; transition: margin-left 0s; contain: layout paint; }
.topbar { height: 72px; background: var(--glass-bg); backdrop-filter: var(--glass-blur); -webkit-backdrop-filter: var(--glass-blur); border-bottom: 1px solid var(--glass-border); border-radius: 20px; box-shadow: var(--glass-shadow); display: flex; align-items: center; justify-content: space-between; padding: 0 32px; position: relative; z-index: 50; }
.page-title { font-weight: 600; font-size: 18px; letter-spacing: -0.36px; }
.time-now { color: var(--clay-text-muted); font-size: 13px; margin-right: 16px; font-family: var(--clay-mono); }

/* ===== Account Dropdown — Clay style ===== */
.user-info { display: flex; align-items: center; gap: 12px; }
.account-trigger { position: relative; }

.user-chip {
  display: flex; align-items: center; gap: 8px;
  background: rgba(218, 212, 200, 0.25); padding: 6px 14px; border-radius: 20px;
  font-size: 13px; font-weight: 600; color: var(--clay-ube);
  border: 1px solid var(--glass-border); cursor: pointer;
  transition: background-color 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.user-chip:hover, .user-chip.is-active {
  background: var(--clay-ube-bg); border-color: var(--clay-ube-light);
  transform: translateY(-1px);
  box-shadow: var(--clay-shadow), 0 2px 8px rgba(67, 8, 159, 0.1);
}
.user-avatar {
  width: 22px; height: 22px; border-radius: 50%; background: var(--clay-ube);
  color: #fff; display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
}
.chevron { transition: transform 0.2s ease; }
.chevron.is-flipped { transform: rotate(180deg); }

/* Dropdown panel */
.user-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  min-width: 180px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid var(--clay-border);
  border-radius: 12px;
  box-shadow: var(--clay-shadow), 0 8px 32px rgba(0, 0, 0, 0.08);
  padding: 6px;
  z-index: 200;
}
.dropdown-item {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 14px; border-radius: 8px; font-size: 14px;
  font-weight: 500; color: var(--clay-text); cursor: pointer;
  transition: background-color 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), color 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  text-decoration: none;
}
.dropdown-item:hover {
  background: var(--clay-lemon); color: #000;
  transform: translateX(4px);
  box-shadow: var(--clay-shadow);
}
.dropdown-item--danger:hover {
  background: var(--clay-pomegranate-bg); color: var(--clay-pomegranate);
}
.dropdown-divider {
  height: 1px; background: var(--clay-border-light); margin: 4px 8px;
}

/* Dropdown transition */
.dropdown-enter-active { transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); }
.dropdown-leave-active { transition: all 0.15s ease; }
.dropdown-enter-from { opacity: 0; transform: translateY(-8px) scale(0.95); }
.dropdown-leave-to { opacity: 0; transform: translateY(-4px) scale(0.98); }

.content-body { flex: 1; display: flex; overflow: hidden; }
.view-container { flex: 1; min-width: 0; }

/* ===== Floating AI Chat Drawer ===== */
.chat-drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 90;
  background: rgba(0, 0, 0, 0.08);
  backdrop-filter: blur(2px);
  -webkit-backdrop-filter: blur(2px);
}
.drawer-backdrop-enter-active { transition: opacity 0.35s ease; }
.drawer-backdrop-leave-active { transition: opacity 0.25s ease; }
.drawer-backdrop-enter-from,
.drawer-backdrop-leave-to { opacity: 0; }

.chat-drawer {
  position: fixed;
  top: 24px;
  right: 24px;
  bottom: 24px;
  width: 400px;
  z-index: 100;
  transform: translateX(calc(100% + 30px));
  transition: transform 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
  will-change: transform;
  contain: layout paint style;
}
.chat-drawer.is-open {
  transform: translateX(0);
}

/* Clay capsule pull handle — sits on left edge of drawer */
.drawer-handle {
  position: absolute;
  left: -22px;
  top: 50%;
  transform: translateY(-50%);
  width: 22px;
  height: 72px;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-right: none;
  border-radius: 12px 0 0 12px;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: var(--clay-text-muted);
  transition: background-color 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), color 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), width 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), left 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
  will-change: width, left;
}
.drawer-handle:hover {
  background: var(--clay-ube-bg);
  color: var(--clay-ube);
  width: 26px;
  left: -26px;
  box-shadow: -6px 0 20px rgba(67, 8, 159, 0.1);
}

.chat-drawer__panel {
  width: 100%;
  height: 100%;
  background: var(--glass-bg);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border-radius: 24px;
  border: 1px solid var(--glass-border);
  box-shadow:
    var(--glass-shadow),
    -8px 0 32px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  contain: layout paint style;
  will-change: transform, opacity;
}
.chat-drawer__panel > * {
  height: 100%;
}

.app-layout.is-sidebar-animating .sidebar,
.app-layout.is-sidebar-animating .topbar,
.app-layout.is-chat-animating .chat-drawer__panel,
.app-layout.is-chat-animating .drawer-handle,
.app-layout.is-chat-animating .chat-drawer-backdrop {
  backdrop-filter: none;
  -webkit-backdrop-filter: none;
}

.app-layout.is-sidebar-animating .sidebar,
.app-layout.is-chat-animating .chat-drawer__panel {
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
}

.app-layout.is-sidebar-animating .sidebar,
.app-layout.is-chat-animating .chat-drawer__panel,
.app-layout.is-chat-animating .drawer-handle {
  background: rgba(255, 255, 255, 0.88);
}

</style>
