# 前端界面现状技术报告（Figma 重构参考）

> **项目**: 智慧校园网络安全态势感知系统 (SmartCampus)
> **技术栈**: Vue 3 + Vue CLI 5 + ECharts 6
> **设计系统**: Clay Design System（已应用）
> **生成日期**: 2026-04-14
> **排除范围**: 登录页面（LoginView.vue / AnimatedCharacters.vue）不在本报告范围内

---

## 一、整体布局

### 1.1 布局架构

```
┌──────────────────────────────────────────────────────────┐
│  App.vue (#main-container) — 100vh                       │
│  ┌──────────┬─────────────────────────────────────────┐  │
│  │          │  main-wrapper (flex: 1)                  │  │
│  │  Sidebar │  ┌─────────────────────────────────────┐ │  │
│  │  260px   │  │  Topbar (72px)                       │ │  │
│  │  fixed   │  ├─────────────────────────────────────┤ │  │
│  │          │  │  content-body (flex: 1)              │ │  │
│  │          │  │  ┌──────────────┬──────────────┐    │ │  │
│  │          │  │  │ view-        │ ai-sidebar   │    │ │  │
│  │          │  │  │ container    │ 380px        │    │ │  │
│  │          │  │  │ (flex: 1)    │ (Chat.vue)   │    │ │  │
│  │          │  │  └──────────────┴──────────────┘    │ │  │
│  │          │  └─────────────────────────────────────┘ │  │
│  └──────────┴─────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

### 1.2 布局参数

| 区域 | 宽度 | 高度 | 弹性 | 备注 |
|------|------|------|------|------|
| Sidebar | 260px (fixed) | 100vh | flex-shrink: 0 | 左侧固定 |
| Topbar | auto | 72px | flex-shrink: 0 | 顶部固定 |
| view-container | flex: 1 | auto | min-width: 0 | 中间自适应 |
| ai-sidebar | 380px (fixed) | auto | flex-shrink: 0 | 右侧 Chat 面板 |
| content-body | auto | flex: 1 | gap: 24px, padding: 24px | flex row 容器 |

### 1.3 页面切换机制

- 无 vue-router，通过 `v-if` + 动态 `<component :is="currentView">` 切换视图
- 使用 `<keep-alive>` 包裹组件，切换时保留状态
- 5 个主视图：Dashboard / Realtime / Rank / History / Alert

### 1.4 响应式规则

- **当前状态**: 无断点适配，全局 `overflow: hidden`，100vh 锁定
- **侧边栏**: 固定 260px，不会折叠
- **Chat 面板**: 固定 380px，不会折叠
- **主内容区**: 自动填充剩余空间

---

## 二、核心组件详解

### 2.1 Sidebar（侧边栏）

**文件**: `App.vue <aside class="sidebar">`

| 元素 | 视觉规格 | Clay 标记 |
|------|---------|----------|
| 背景 | `#ffffff` 纯白 | ✅ Clay 改造 |
| 右边框 | `1px solid #dad4c8` 燕麦实线 | ✅ Clay 改造 |
| 品牌区 Logo | Emoji `🛡️`，28px | 原始 |
| 品牌区分隔 | `1px dashed #dad4c8` 虚线 | ✅ Clay 改造 |
| 标题 "流量监督" | 18px, weight 600, `#000000` | ✅ Clay 改造 |
| 副标题 | 11px, `#9f9b93` warm silver | ✅ Clay 改造 |
| 菜单项（默认） | 14px, weight 500, `#55534e` warm charcoal, border-radius 12px | ✅ Clay 改造 |
| 菜单项（Hover） | bg `#faf9f7`, color `#000000` | ✅ Clay 改造 |
| 菜单项（Active） | bg `#c1b0ff` Ube 300, color `#43089f` Ube 800, weight 600, Clay Shadow | ✅ Clay 改造 |
| 分隔线 | `1px solid #eee9df` oat light | ✅ Clay 改造 |
| 退出按钮 | color `#fc7981` Pomegranate, 燕麦边框 | ✅ Clay 改造 |
| 告警徽章 | bg `#fc7981`, 白字, border-radius 10px | ✅ Clay 改造 |
| 底部探针状态 | 绿点 + 文字 "探针状态：已授权" | 原始 |

**菜单项（自上而下）**:
1. 全局态势看板 → Dashboard
2. 瞬时活跃监控 → Realtime
3. 大流排行追踪 → Rank
4. 历史溯源检索 → History
5. 威胁告警雷达 → Alert（附带红色数字徽章）
6. ── 分隔线 ──
7. 退出系统

### 2.2 Topbar（顶栏）

**文件**: `App.vue <header class="topbar">`

| 元素 | 视觉规格 |
|------|---------|
| 高度 | 72px |
| 背景 | `#ffffff` 纯白 |
| 底边框 | `1px solid #dad4c8` ✅ Clay |
| 页面标题 | 18px, weight 600, letter-spacing -0.36px |
| 当前时间 | 13px, `Space Mono` 等宽字体, `#9f9b93` |
| 用户标签 | bg `#eee9df`, color `#43089f` Ube, border-radius 20px, 13px, weight 600, 燕麦边框 |

**页面标题映射**:
- Dashboard → "宏观态势总览"
- Realtime → "瞬时活跃链路切片监控"
- Rank → "全网流量节点排行榜"
- History → "历史流记录溯源检索"
- Alert → "动态威胁感知雷达"

### 2.3 Chat（AI 助手面板）

**文件**: `Chat.vue` | **位置**: 右侧 ai-sidebar 380px

**整体容器**: border-radius 24px, 燕麦边框 + Clay 冲压阴影

| 区域 | 视觉规格 |
|------|---------|
| 头部 | padding 24px, 底部燕麦实线边框, 标题 "DeepSeek AI" 18px/600 + 副标题 + 绿色状态点 |
| 消息列表 | bg `#faf9f7` 暖奶油, padding 24px, gap 24px, 滚动条 4px 燕麦色 |
| AI 头像 | 36x36, border-radius 12px, bg `#43089f` Ube, 白字 "AI" |
| 用户头像 | 36x36, border-radius 12px, bg `#000000` 纯黑, 白字 "U" |
| AI 气泡 | 白底 + 燕麦边框 + Clay 冲压阴影, border-top-left-radius 4px |
| 用户气泡 | 纯黑底白字, border-top-right-radius 4px |
| 时间戳 | `Space Mono` 等宽, `#9f9b93` |
| 思考动画 | 3 个灰色圆点, bounce 动画 1.4s |
| 输入区 | 底部 dashed 燕麦分隔, 圆角胶囊输入框 (border-radius 999px), bg `#faf9f7` |
| 发送按钮 | 40x40 黑色圆形, Hover 时: `rotateZ(-8deg) translateY(-2px)` + Lemon 黄色 + hard shadow ✅ Clay 标志交互 |

---

## 三、视觉规范

### 3.1 颜色系统（Clay Design System）

#### 全局 CSS 变量

```css
:root {
  --clay-bg: #faf9f7;              /* 页面背景 — 暖奶油 */
  --clay-text: #000000;             /* 主文字 — 纯黑 */
  --clay-text-muted: #9f9b93;       /* 次要文字 — 温暖银灰 */
  --clay-text-secondary: #55534e;   /* 辅助文字 — 温暖炭灰 */
  --clay-border: #dad4c8;           /* 主边框 — 燕麦色 */
  --clay-border-light: #eee9df;     /* 次边框 — 浅燕麦 */
  --clay-shadow: 多层冲压阴影（见 3.3）;
  --clay-shadow-hover: rgb(0,0,0) -7px 7px;
}
```

#### Swatch 色板（命名色）

| 名称 | 色值 | CSS 变量 | 用途 |
|------|------|---------|------|
| Matcha | `#078a52` | `--clay-matcha` | 安全状态、成功指示、绿色点 |
| Matcha Light | `#84e7a5` | `--clay-matcha-light` | 告警边框浅绿 |
| Slushie | `#3bd3fd` | `--clay-slushie` | 图表第二色 |
| Lemon | `#fbbd41` | `--clay-lemon` | 按钮 Hover 变色、警告色、进度条 |
| Ube | `#43089f` | `--clay-ube` | 图表主色、IP 高亮、菜单 Active |
| Ube Light | `#c1b0ff` | `--clay-ube-light` | Active 菜单背景、进度条渐变尾 |
| Pomegranate | `#fc7981` | `--clay-pomegranate` | 告警/危险色、退出按钮 |
| Blueberry | `#01418d` | `--clay-blueberry` | 协议标签文字、图表第六色 |

#### 图表统一配色

所有 ECharts 图表使用同一 6 色板：
```
['#078a52', '#3bd3fd', '#fbbd41', '#43089f', '#fc7981', '#01418d']
```
Rank 页饼图扩展至 10 色，追加：`['#84e7a5', '#c1b0ff', '#f8cc65', '#0089ad']`

### 3.2 间距与圆角

#### 间距体系

| 位置 | 值 |
|------|----|
| 全局 gap | 24px |
| 全局 padding（内容区） | 24px |
| 卡片内 padding | 24px |
| Topbar 左右 padding | 32px |
| 表格 th/td padding | 12-16px |
| 输入框 padding | 10px |

#### 圆角步进

| 元素类型 | border-radius | 备注 |
|---------|--------------|------|
| 卡片容器 | 24px | Clay Feature 尺寸 |
| 聊天整体容器 | 24px | 同卡片 |
| 菜单项 / 按钮 | 12px | Clay Standard |
| 输入框 | 12px | Clay Standard |
| 协议标签 | 999px | 药丸形 |
| 头像 | 12px | Clay Standard |
| 气泡 | 16px（主体）/ 4px（指向角） | 对话气泡异形 |
| LIVE 徽章 | 999px | 药丸形 |
| 等级徽章 | 999px | 药丸形 |
| 用户标签 | 20px | 胶囊形 |
| 状态点 | 50% | 圆形 |

### 3.3 阴影与深度

| 层级 | 定义 | 使用位置 |
|------|------|---------|
| **Clay Shadow (L1)** | `rgba(0,0,0,0.1) 0px 1px 1px, rgba(0,0,0,0.04) 0px -1px 1px inset, rgba(0,0,0,0.05) 0px -0.5px 1px` | 所有卡片、气泡、Active 菜单项 |
| **Hard Shadow (L2)** | `rgb(0,0,0) -7px 7px` | 按钮 Hover 状态（标志交互） |
| **无阴影** | — | 页面背景、表格行 |

**Clay 冲压阴影说明**: 三层结构 = 向下投影 + 向内高光 + 边缘微影，营造"压入黏土"的质感。

### 3.4 字体

| 用途 | 字体栈 | 备注 |
|------|-------|------|
| 全局 UI 文字 | `'Roobert', 'Arial', sans-serif` | Clay 主字体，实际 fallback Arial |
| 等宽数字/IP | `'Space Mono', monospace` | IP 地址、时间戳、数据列 |
| 图表文字 | `'Inter'` (ECharts 内) | 图表 tooltip/轴标签 |
| Emoji | 系统原生 | 🛡️ ⚠️ 🔍 🦠 🕷️ 🔓 📡 ✨ 📊 |

---

## 四、各视图组件

### 4.1 Dashboard（宏观态势总览）

**文件**: `Dashboard.vue` | **布局**: 垂直两段

**上半段 — KPI 指标网格**:
- 4 列等宽 flex 布局，gap 24px
- 每个卡片 140px 高，24px 圆角，白底+燕麦边框+Clay 阴影
- 内含：标题 + SVG 图标（32x32 圆角方块）+ 大数字（32px/800）+ 状态行
- 图标背景色映射：dark=`#f4f4f5`, danger=`#fef2f2`/Pomegranate, warning=`#fef3c7`/Lemon, purple=`#f3e8ff`/Ube

| KPI 卡片 | 大数字颜色 | 图标类型 |
|---------|----------|---------|
| 全网实时吞吐量 | `#000000` 黑 | 心电图 SVG |
| 今日累计拦截威胁 | `#fc7981` Pomegranate | 盾牌 SVG |
| 独立攻击源 (IP) | `#000000` 黑 | 感叹号圆 SVG |
| AIOps 智能引擎 | `#43089f` Ube | 饼图 SVG |

**下半段 — 双图表区**:
- 左侧 flex:7 — **折线图**（全网吞吐量宏观波动）
  - Ube 深紫主线 `#43089f`, 3px 宽, smooth
  - 面积渐变：`rgba(67,8,159,0.2)` → 透明
  - 保留最近 40 个数据点
- 右侧 flex:3 — **环形饼图**（流量协议画像）
  - 内外半径 50%-75%, Clay 6 色板
  - 标签显示协议名+百分比

### 4.2 Realtime（瞬时活跃监控）

**文件**: `Realtime.vue` | **布局**: 上下两段

**上半段 — 双图表** (320px 高):
- 左 — **柱状图**（大流吞吐量瞬时切片）
  - 渐变色：顶部 Ube `#43089f` → 底部 Ube Light `#c1b0ff`
  - 柱顶圆角 6px
- 右 — **环形图**（瞬时应用协议分布）
  - Clay 6 色板

**下半段 — 数据表格**:
- 标题行：左侧 "秒级活跃链路监控" + 右侧 LIVE 药丸徽章
  - LIVE 徽章：bg `#fef2f2`, color Pomegranate, 呼吸灯动画 1.5s
- 5 列表格：源IP / 去向IP / 瞬时吞吐量 / 数据包量 / 识别协议
- IP 地址：`Space Mono` 等宽，源IP 用 Ube 色，目的IP 旁附状态点（内网=Matcha绿，外网=Lemon黄）
- 协议标签：药丸形，浅蓝底+Blueberry 文字+浅燕麦边框
- 空状态：📡 图标 + 灰色提示文字

### 4.3 Rank（大流排行追踪）

**文件**: `Rank.vue` | **布局**: 上下两段

**上半段 — 双图表** (320px 高):
- 左 — **饼图**（Top-10 节点吞吐占比）
  - 40%-70% 环形, 无标签, Clay 10 色扩展板
- 右 — **横向柱状图**（实时吞吐强度对比 Mbps）
  - Ube 纯色 `#43089f`, 右侧圆角 6px

**下半段 — 排行表格**:
- 标题行：左侧标题 + 右侧 **"手动刷新"按钮**
  - 按钮默认：白底+燕麦边框+12px 圆角
  - 按钮 Hover：`rotateZ(-8deg) translateY(-2px)` + Lemon 黄底 + hard shadow `-7px 7px` ✅ **Clay 标志交互**
- 7 列：排名 / 源地址 / 目的地址 / 协议特征 / 吞吐进度条 / 累计流量 / 包数
- 排名数字：24x24 方块，Top3 用 Ube Light 背景+Ube 文字，其余浅灰
- 进度条：8px 高, Ube → Ube Light 渐变
- 所有数据/IP 使用 `Space Mono`

### 4.4 History（历史溯源检索）

**文件**: `History.vue` | **布局**: 筛选栏 + 数据表

**筛选栏**:
- 搜索框：300px 宽, 左侧 🔍 图标, 12px 圆角, 燕麦边框, focus 时 Ube 紫色边框
- 两个 select 下拉：12px 圆角, 燕麦边框
- "清空记录"按钮：默认白底+Pomegranate 文字+燕麦边框, Hover 时 Lemon 黄底+hard shadow ✅ Clay 标志交互

**数据表格**:
- 6 列：捕获时间 / 流量链路 / 主要协议 / 载荷大小 / 状态标识 / 包数
- 表头：bg `#faf9f7` 暖奶油, dashed 燕麦分隔
- 链路列：`IP → IP` 格式, `Space Mono` 等宽, 箭头用燕麦色
- 状态点三色：正常=Matcha绿, 可疑=Lemon黄, 危险=Pomegranate红

**分页器**:
- 底部 dashed 燕麦分隔
- 按钮：白底+燕麦边框, Hover 时 Ube Light 背景+hard shadow ✅ Clay 标志交互
- disabled 态：0.5 opacity + not-allowed

### 4.5 Alert（威胁告警雷达）

**文件**: `Alert.vue` | **布局**: 整体包裹在一个 Clay 卡片中

**上半段** (260px 高):
- 左侧 flex:1.2 — **雷达图**（5 维威胁画像）
  - 维度：DDoS / 扫描 / 蠕虫 / 爬虫 / 外泄
  - Ube 紫色 `#43089f`, 面积填充 `rgba(67,8,159,0.15)`
- 右侧 flex:1 — 状态面板
  - 绿色呼吸灯 + "Heuristic IDS 启发式多维巡检中"
  - 两格统计：累计拦截(黑) / 高危致命(Pomegranate红)

**下半段 — 告警日志表格**:
- 6 列：时间 / 威胁类型 / 攻击源IP / 命中协议 / 危险等级 / 动作
- 威胁类型前附 Emoji 图标
- IP 使用 `Space Mono`, Ube 色高亮
- 等级徽章：高危=浅红底+Pomegranate文字+粉色边框, 中危=浅黄底+Lemon深色文字+黄色边框
- 空状态：✨ 图标 + "当前网络环境纯净"

---

## 五、交互细节

### 5.1 Clay 标志性 Hover 动效 ✅

已应用于以下按钮，统一动效参数：

```css
transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
transform: rotateZ(-8deg) translateY(-2px);
box-shadow: rgb(0,0,0) -7px 7px;
```

| 按钮 | Hover 背景色 | 文件 |
|------|-------------|------|
| Chat 发送按钮 | `#fbbd41` Lemon | Chat.vue |
| Rank 手动刷新 | `#fbbd41` Lemon | Rank.vue |
| History 清空记录 | `#fbbd41` Lemon | History.vue |
| History 分页按钮 | `#c1b0ff` Ube Light | History.vue |

### 5.2 动画列表

| 动画 | 周期 | 元素 |
|------|------|------|
| LIVE 呼吸灯 | 1.5s infinite | Realtime 页 LIVE 徽章内圆点 |
| 安全状态呼吸灯 | 2s infinite | Alert 页 pulse-ring |
| AI 思考弹跳 | 1.4s infinite | Chat 页 3 圆点 |
| 时钟更新 | 1s interval | Topbar 时间戳 |

### 5.3 滚动条

全局统一风格：
- 宽度 4px
- 轨道透明
- 滑块颜色 `#dad4c8` 燕麦色
- 滑块圆角 4px

### 5.4 状态指示点

| 颜色 | 色值 | 含义 |
|------|------|------|
| Matcha 绿 | `#078a52` | 安全/在线/正常/已授权 |
| Lemon 黄 | `#fbbd41` | 警告/可疑/外网 |
| Pomegranate 红 | `#fc7981` | 危险/告警/高危 |

---

## 六、资产盘点

### 6.1 图标

- **无第三方图标库**（未使用 Element Plus / FontAwesome 等）
- 全部使用 **内联 SVG** 或 **Unicode Emoji**
- SVG 图标统一规格：16x16, stroke currentColor, stroke-width 2

### 6.2 依赖清单

| 包名 | 版本 | 用途 |
|------|------|------|
| vue | ^3.5.31 | 框架核心 |
| echarts | ^6.0.0 | 图表引擎 |
| vue-i18n | ^9.14.5 | 国际化（登录页使用） |
| vue-cli-service | ^5.0.9 | 构建工具 |
| axios | ^1.0.0 | HTTP 客户端 |

### 6.3 全局状态指示

| 位置 | 内容 |
|------|------|
| Sidebar 底部 | 绿色状态点 + "探针状态：已授权" |
| Topbar 右侧 | 实时时钟（`Space Mono`）+ "管理员 (Admin)" 胶囊 |
| Alert 页 | 绿色呼吸灯 + "Heuristic IDS 启发式多维巡检中" |
| Dashboard KPI | 绿点 + "探针在线" / "语境注入就绪" |

---

## 七、Figma 重构要点总结

### 7.1 需要延续的 Clay 风格特征

1. **暖奶油背景** `#faf9f7` — 全局画布
2. **燕麦边框** `#dad4c8` — 所有卡片、表格分隔
3. **24px 大圆角** — 所有卡片容器
4. **冲压阴影** — 三层 inset 阴影
5. **Hover 旋转+硬阴影** — 按钮交互标志
6. **Space Mono 等宽字体** — IP/数据/时间
7. **Ube 紫 `#43089f`** — 主强调色（图表主线、Active 菜单、IP 高亮）

### 7.2 当前不一致的地方

| 问题 | 位置 | 说明 |
|------|------|------|
| 图表 tooltip | 全部图表 | 仍使用 `#171717` 深黑背景，未适配 Clay 暖调 |
| 图表网格线 | Dashboard/Realtime | 仍为 `#f4f4f5` 冷灰色，应改为燕麦色 |
| 图表标题 | 全部图表 | `#171717` 冷黑，应统一为 `#000000` |
| 图表轴标签 | 全部图表 | `#737373` 冷灰，应改为 `--clay-text-muted` |
| 字体未实际加载 | 全局 | Roobert 未引入 CDN/本地文件，实际 fallback 到 Arial |

### 7.3 组件层级对照表（供 Figma 建立组件库）

```
App.vue
├── Sidebar
│   ├── Brand (Logo + 标题)
│   ├── NavMenu (5 项 + 分隔线 + 退出)
│   └── StatusFooter (探针状态)
├── Topbar
│   ├── PageTitle
│   └── UserInfo (时钟 + 用户标签)
└── ContentBody
    ├── ViewContainer
    │   ├── Dashboard (KPI Grid + Charts)
    │   ├── Realtime (Charts + Table)
    │   ├── Rank (Charts + Table + Progress)
    │   ├── History (Filter + Table + Pagination)
    │   └── Alert (Radar + Stats + Table)
    └── AISidebar
        └── Chat (Header + Messages + Input)
```
