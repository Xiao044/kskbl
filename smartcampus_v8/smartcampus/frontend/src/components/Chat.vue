<template>
  <div class="chat-inner-container">
    <div class="chat-header">
      <div class="title-area">
        <h3 class="title">DeepSeek AI</h3>
        <span class="subtitle">AIOps 智能分析助理</span>
      </div>
      <div class="chat-header-actions">
        <div class="status-wrap">
          <div class="status-dot"></div>
          <span class="status-text">{{ statusText }}</span>
        </div>
        <button class="header-btn" @click="resetConversation(false)">清空上下文</button>
        <button class="header-btn header-btn--strong" @click="resetConversation(true)">新建对话</button>
      </div>
    </div>

    <div class="chat-messages" ref="messageBox">
      <div v-for="msg in messages" :key="msg.id" :class="['msg-row', msg.senderId === 'me' ? 'is-me' : 'is-ai']">
        <div class="avatar" :class="msg.senderId === 'me' ? 'avatar-me' : 'avatar-ai'">
          {{ msg.senderId === 'me' ? 'U' : 'AI' }}
        </div>

        <div class="msg-content">
          <div class="msg-meta">
            <span class="name">{{ messageSenderName(msg) }}</span>
            <span class="time">{{ msg.time }}</span>
          </div>
          <div class="bubble" :class="{ 'bubble-system': msg.senderId === 'system' }">{{ msg.text }}</div>

          <div v-if="msg.senderId === 'ai' && getQuickActionIps(msg).length" class="quick-actions">
            <span class="quick-actions__label">快捷检索</span>
            <button
              v-for="ip in getQuickActionIps(msg)"
              :key="`${msg.id}-quick-${ip}`"
              class="quick-action-chip"
              type="button"
              @click="openIpDetail(ip)"
            >
              {{ ip }}
            </button>
          </div>

          <div v-if="msg.senderId === 'ai' && hasAnalysisMeta(msg)" class="analysis-panel">
            <div class="analysis-section">
              <div class="analysis-title">当前态势依据</div>
              <div class="analysis-kpis">
                <div class="analysis-kpi">
                  <span class="analysis-kpi__label">高危告警</span>
                  <strong>{{ msg.analysisMeta.context.high_risk_count || 0 }}</strong>
                </div>
                <div class="analysis-kpi">
                  <span class="analysis-kpi__label">中危告警</span>
                  <strong>{{ msg.analysisMeta.context.medium_risk_count || 0 }}</strong>
                </div>
                <div class="analysis-kpi">
                  <span class="analysis-kpi__label">近期告警</span>
                  <strong>{{ msg.analysisMeta.context.recent_alert_count || 0 }}</strong>
                </div>
              </div>

              <div class="analysis-grid">
                <div class="analysis-card" v-if="msg.analysisMeta.context.current_top_talker">
                  <div class="analysis-card__title">Top Talker</div>
                  <button
                    class="analysis-card__main analysis-link"
                    type="button"
                    @click="openIpDetail(msg.analysisMeta.context.current_top_talker.src_ip)"
                  >{{ msg.analysisMeta.context.current_top_talker.src_ip || '暂无数据' }}</button>
                  <div class="analysis-card__sub">
                    {{ msg.analysisMeta.context.current_top_talker.bytes || 0 }} Bytes /
                    {{ msg.analysisMeta.context.current_top_talker.packets || 0 }} Pkts
                  </div>
                </div>

                <div class="analysis-card" v-if="msg.analysisMeta.context.current_abnormal_zone">
                  <div class="analysis-card__title">异常区域</div>
                  <button
                    class="analysis-card__main analysis-link"
                    type="button"
                    @click="openHistoryForZone(msg.analysisMeta.context.current_abnormal_zone.zone)"
                  >{{ msg.analysisMeta.context.current_abnormal_zone.zone || '暂无数据' }}</button>
                  <div class="analysis-card__sub">
                    {{ msg.analysisMeta.context.current_abnormal_zone.mbps || 0 }} Mbps /
                    {{ msg.analysisMeta.context.current_abnormal_zone.packets || 0 }} Pkts
                  </div>
                </div>
              </div>

              <div v-if="hasHighRiskEvents(msg)" class="analysis-events">
                <div class="analysis-title analysis-title--small">最近 3 条高危事件</div>
                <div
                  v-for="(event, index) in msg.analysisMeta.context.latest_high_risk_events"
                  :key="`${msg.id}-event-${index}`"
                  class="analysis-event"
                >
                  <span class="analysis-event__time">{{ event.time }}</span>
                  <span class="analysis-event__text">
                    {{ event.type }} /
                    <button class="analysis-inline-link" type="button" @click="openIpDetail(event.src_ip)">{{ event.src_ip }}</button>
                    /
                    <button class="analysis-inline-link" type="button" @click="openHistoryForZone(event.zone)">{{ event.zone }}</button>
                  </span>
                </div>
              </div>
            </div>

            <div v-if="hasToolCalls(msg)" class="analysis-section">
              <div class="analysis-title">本轮工具调用</div>
              <div
                v-for="(tool, index) in msg.analysisMeta.tool_calls"
                :key="`${msg.id}-tool-${index}`"
                class="tool-card"
              >
                <div class="tool-card__header">
                  <span class="tool-card__name">{{ tool.label || tool.name }}</span>
                  <span class="tool-card__args">{{ formatToolArguments(tool.arguments) }}</span>
                </div>
                <button
                  v-if="extractToolIp(tool)"
                  class="tool-card__action"
                  type="button"
                  @click="openIpDetail(extractToolIp(tool))"
                >打开该 IP 独立画像</button>
                <div
                  v-for="(line, lineIndex) in tool.summary || []"
                  :key="`${msg.id}-tool-${index}-line-${lineIndex}`"
                  class="tool-card__line"
                >
                  {{ line }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="isAiTyping" class="msg-row is-ai">
        <div class="avatar avatar-ai">AI</div>
        <div class="msg-content">
          <div class="bubble typing-bubble">
            <span class="typing-label">{{ pendingStatusLabel }}</span>
            <span class="dot-bounce"></span>
            <span class="dot-bounce"></span>
            <span class="dot-bounce"></span>
          </div>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <div class="input-wrapper">
        <input
          type="text"
          v-model="inputText"
          @keyup.enter="sendMessage"
          @focus="$emit('chat-focus')"
          @blur="$emit('chat-blur')"
          placeholder="Ask AI about network..."
        />
        <button class="btn-send" @click="sendMessage" :disabled="!inputText.trim()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Chat',
  emits: ['chat-focus', 'chat-blur', 'message-sent', 'focus-ip-history', 'focus-zone-history', 'view-ip'],
  props: {
    prefillDisplay: { type: String, default: '' },
    prefillMessage: { type: String, default: '' },
    prefillToken: { type: Number, default: 0 }
  },
  data() {
    return {
      ws: null,
      inputText: '',
      isAiTyping: false,
      pendingStatusLabel: 'AI 正在分析当前态势...',
      messages: [
        {
          id: 'welcome',
          senderId: 'ai',
          targetId: 'me',
          text: '您好！我是 DeepSeek 运维助理。我已接入当前底层探针数据，您可以随时向我询问异常研判或防御策略。',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          analysisMeta: null
        }
      ]
    }
  },
  watch: {
    prefillToken() {
      this.applyPrefillMessage();
    }
  },
  computed: {
    statusText() {
      return this.isAiTyping ? this.pendingStatusLabel : '在线分析中';
    }
  },
  mounted() {
    this.connectChatWS();
    this.applyPrefillMessage();
  },
  beforeUnmount() { if (this.ws) this.ws.close(); },
  methods: {
    messageSenderName(msg) {
      if (msg.senderId === 'me') return '管理员';
      if (msg.senderId === 'system') return 'System';
      return msg.senderName || 'DeepSeek';
    },
    hasAnalysisMeta(msg) {
      return !!(msg && msg.analysisMeta && msg.analysisMeta.context);
    },
    hasHighRiskEvents(msg) {
      return !!(
        this.hasAnalysisMeta(msg) &&
        Array.isArray(msg.analysisMeta.context.latest_high_risk_events) &&
        msg.analysisMeta.context.latest_high_risk_events.length
      );
    },
    hasToolCalls(msg) {
      return !!(
        this.hasAnalysisMeta(msg) &&
        Array.isArray(msg.analysisMeta.tool_calls) &&
        msg.analysisMeta.tool_calls.length
      );
    },
    formatToolArguments(args) {
      const entries = Object.entries(args || {});
      if (!entries.length) return '默认参数';
      return entries.map(([key, value]) => `${key}: ${value}`).join(' / ');
    },
    extractIpsFromText(text) {
      const matches = String(text || '').match(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g) || [];
      const validIps = matches.filter((ip) => ip.split('.').every((part) => {
        const value = Number(part);
        return Number.isInteger(value) && value >= 0 && value <= 255;
      }));
      return Array.from(new Set(validIps));
    },
    extractToolIp(tool) {
      const ip = tool && tool.arguments ? tool.arguments.ip : '';
      return typeof ip === 'string' && ip.trim() ? ip.trim() : '';
    },
    getQuickActionIps(msg) {
      const ips = [];
      const textIps = this.extractIpsFromText(msg && msg.text);
      ips.push(...textIps);

      if (this.hasAnalysisMeta(msg)) {
        const topTalkerIp = msg.analysisMeta.context.current_top_talker && msg.analysisMeta.context.current_top_talker.src_ip;
        if (topTalkerIp) ips.push(topTalkerIp);

        const events = msg.analysisMeta.context.latest_high_risk_events || [];
        events.forEach((event) => {
          if (event && event.src_ip) ips.push(event.src_ip);
        });

        const toolCalls = msg.analysisMeta.tool_calls || [];
        toolCalls.forEach((tool) => {
          const toolIp = this.extractToolIp(tool);
          if (toolIp) ips.push(toolIp);
        });
      }

      return Array.from(new Set(ips)).slice(0, 6);
    },
    openHistoryForIp(ip) {
      if (!ip || typeof ip !== 'string') return;
      this.$emit('focus-ip-history', ip.trim());
    },
    openIpDetail(ip) {
      if (!ip || typeof ip !== 'string') return;
      const normalizedIp = ip.trim();
      if (!normalizedIp) return;
      this.$emit('view-ip', normalizedIp);
    },
    openHistoryForZone(zone) {
      if (!zone || typeof zone !== 'string') return;
      this.$emit('focus-zone-history', zone.trim());
    },
    inferPendingStatus(text) {
      const normalized = String(text || '').toLowerCase();
      if (/(top|排行|topk|top talker)/.test(normalized)) return 'AI 正在查询 Top-K 流量节点...';
      if (/(区域|zone|异常区域)/.test(normalized)) return 'AI 正在查询区域流量统计...';
      if (/(资源|cpu|内存|system)/.test(normalized)) return 'AI 正在查询系统资源状态...';
      if (/(告警|高危|最新事件|latest alert)/.test(normalized)) return 'AI 正在检索最新安全告警...';
      if (/(ip|源地址|历史记录|history)/.test(normalized)) return 'AI 正在检索目标 IP 历史...';
      return 'AI 正在分析当前态势...';
    },
    applyPrefillMessage() {
      const message = String(this.prefillMessage || '').trim();
      if (!message) return;
      this.inputText = message;
      this.$nextTick(() => {
        this.sendMessage({
          displayText: this.prefillDisplay || message,
          silentInputClear: true
        });
      });
    },
    connectChatWS() {
      const serverIp = window.location.hostname;
      this.ws = new WebSocket(`ws://${serverIp}:8000/ws/chat`);

      this.ws.onopen = () => {
        this.applyPrefillMessage();
      };
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.messages.push({
          ...data,
          analysisMeta: data.analysisMeta || null
        });
        if (data.senderId === 'ai' || data.senderId === 'system') this.isAiTyping = false;
        this.scrollToBottom();
      };
      this.ws.onclose = () => { setTimeout(() => this.connectChatWS(), 3000); };
    },
    sendMessage(options = {}) {
      const actualText = String(this.inputText || '').trim();
      if (!actualText || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
      const displayText = String(options.displayText || actualText).trim() || actualText;
      this.pendingStatusLabel = this.inferPendingStatus(actualText);
      const newMsg = {
        id: Date.now().toString(),
        senderId: 'me',
        targetId: 'ai',
        text: displayText,
        promptText: actualText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      this.isAiTyping = true;
      this.ws.send(JSON.stringify(newMsg));
      this.inputText = '';
      this.$emit('message-sent');
      this.scrollToBottom();
    },
    resetConversation(startFresh) {
      this.messages = [
        {
          id: `welcome-${Date.now()}`,
          senderId: 'ai',
          targetId: 'me',
          text: startFresh
            ? '新对话已开始。您可以继续询问当前高危告警、top talker、异常区域或某个 IP 的历史记录。'
            : '上下文已清空。您可以从当前系统态势重新开始提问。',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          analysisMeta: null
        }
      ];
      this.isAiTyping = false;
      this.pendingStatusLabel = 'AI 正在分析当前态势...';
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ action: 'reset_session' }));
      }
      this.scrollToBottom();
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const box = this.$refs.messageBox;
        if (box) box.scrollTop = box.scrollHeight;
      });
    }
  }
}
</script>

<style scoped>
.chat-inner-container { display: flex; flex-direction: column; height: 100%; background: var(--glass-bg, rgba(255,255,255,0.55)); backdrop-filter: var(--glass-blur, blur(12px)); -webkit-backdrop-filter: var(--glass-blur, blur(12px)); box-sizing: border-box; border-radius: 24px; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); }

.chat-header { padding: 24px; border-bottom: 1px solid var(--clay-border, #dad4c8); display: flex; justify-content: space-between; align-items: center; gap: 16px; }
.title { margin: 0; font-size: 18px; font-weight: 600; color: #000000; letter-spacing: -0.36px; }
.subtitle { font-size: 12px; color: var(--clay-text-muted, #9f9b93); font-weight: 500; }
.chat-header-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
.status-wrap { display: flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px; background: rgba(240, 253, 244, 0.72); border: 1px solid rgba(132, 231, 165, 0.42); }
.status-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--clay-matcha, #078a52); box-shadow: 0 0 0 3px rgba(7, 138, 82, 0.2); }
.status-text { font-size: 12px; color: var(--clay-matcha, #078a52); font-weight: 700; }
.header-btn { border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); background: rgba(255,255,255,0.7); color: #000000; border-radius: 999px; padding: 8px 14px; font-size: 12px; font-weight: 700; cursor: pointer; transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease, color 0.2s ease; }
.header-btn:hover { transform: translateY(-1px); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); background: #ffffff; }
.header-btn--strong { background: var(--clay-ube, #43089f); color: #ffffff; border-color: var(--clay-ube, #43089f); }
.header-btn--strong:hover { background: #5a1ad0; color: #ffffff; }

.chat-messages { flex: 1; padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; background: rgba(250, 249, 247, 0.5); }
.chat-messages::-webkit-scrollbar { width: 4px; }
.chat-messages::-webkit-scrollbar-thumb { background: var(--clay-border, #dad4c8); border-radius: 4px; }

.msg-row { display: flex; gap: 12px; max-width: 85%; }
.msg-row.is-me { align-self: flex-end; flex-direction: row-reverse; }

.avatar { width: 36px; height: 36px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; }
.avatar-ai { background: var(--clay-ube, #43089f); color: #ffffff; }
.avatar-me { background: #000000; color: #ffffff; }

.msg-content { display: flex; flex-direction: column; gap: 6px; }
.is-me .msg-content { align-items: flex-end; }

.msg-meta { display: flex; gap: 8px; align-items: baseline; font-size: 12px; margin: 0 4px; }
.name { font-weight: 600; color: var(--clay-text-secondary, #55534e); }
.time { color: var(--clay-text-muted, #9f9b93); font-family: 'Space Mono', monospace; }

.bubble { padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.6; color: #000000; background: rgba(255, 255, 255, 0.6); backdrop-filter: blur(8px); -webkit-backdrop-filter: blur(8px); border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04)); }
.is-me .bubble { background: #000000; color: #ffffff; border: none; border-top-right-radius: 4px; }
.is-ai .bubble { border-top-left-radius: 4px; }
.bubble-system { background: rgba(243, 238, 255, 0.72); color: var(--clay-ube, #43089f); border-color: rgba(193, 176, 255, 0.45); }

.quick-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 6px;
}
.quick-actions__label {
  font-size: 11px;
  font-weight: 800;
  color: var(--clay-text-muted, #9f9b93);
}
.quick-action-chip {
  border: 1px solid rgba(193, 176, 255, 0.42);
  background: rgba(243, 238, 255, 0.88);
  color: var(--clay-ube, #43089f);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 11px;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, background-color 0.2s ease;
}
.quick-action-chip:hover {
  transform: translateY(-1px);
  box-shadow: var(--glass-shadow, 0 4px 24px rgba(0,0,0,0.04));
  background: rgba(231, 223, 255, 0.96);
}

.analysis-panel { display: flex; flex-direction: column; gap: 12px; margin-top: 6px; }
.analysis-section { background: rgba(255, 255, 255, 0.58); border: 1px solid rgba(218,212,200,0.45); border-radius: 18px; padding: 14px; box-shadow: inset 0 1px 0 rgba(255,255,255,0.55); }
.analysis-title { font-size: 12px; font-weight: 800; color: #171717; margin-bottom: 10px; }
.analysis-title--small { margin-bottom: 8px; }
.analysis-kpis { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; margin-bottom: 10px; }
.analysis-kpi { padding: 10px 12px; border-radius: 14px; background: rgba(250, 249, 247, 0.92); border: 1px solid rgba(218,212,200,0.38); display: flex; flex-direction: column; gap: 4px; }
.analysis-kpi__label { font-size: 11px; color: var(--clay-text-muted, #9f9b93); font-weight: 700; }
.analysis-kpi strong { font-size: 16px; color: #171717; }
.analysis-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; margin-bottom: 10px; }
.analysis-card { padding: 12px; border-radius: 16px; background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(247,244,239,0.82)); border: 1px solid rgba(218,212,200,0.38); }
.analysis-card__title { font-size: 11px; color: var(--clay-text-muted, #9f9b93); font-weight: 800; text-transform: uppercase; letter-spacing: 0.04em; }
.analysis-card__main { margin-top: 6px; font-size: 14px; font-weight: 800; color: #171717; word-break: break-all; }
.analysis-link {
  display: inline-flex;
  width: fit-content;
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  text-align: left;
  text-decoration: underline;
  text-decoration-color: rgba(67, 8, 159, 0.25);
  text-underline-offset: 3px;
}
.analysis-link:hover { color: var(--clay-ube, #43089f); }
.analysis-card__sub { margin-top: 4px; font-size: 12px; color: var(--clay-text-secondary, #55534e); }
.analysis-events { display: flex; flex-direction: column; gap: 8px; }
.analysis-event { display: flex; gap: 8px; align-items: flex-start; font-size: 12px; line-height: 1.5; color: var(--clay-text-secondary, #55534e); }
.analysis-event__time { flex-shrink: 0; padding: 2px 8px; border-radius: 999px; background: rgba(243, 238, 255, 0.86); color: var(--clay-ube, #43089f); font-family: 'Space Mono', monospace; font-size: 11px; }
.analysis-event__text { word-break: break-word; }
.analysis-inline-link {
  border: none;
  background: transparent;
  padding: 0;
  cursor: pointer;
  color: var(--clay-ube, #43089f);
  font-weight: 700;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.tool-card { padding: 12px; border-radius: 16px; background: rgba(250, 249, 247, 0.92); border: 1px solid rgba(218,212,200,0.38); display: flex; flex-direction: column; gap: 6px; }
.tool-card__header { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; }
.tool-card__name { font-size: 12px; font-weight: 800; color: #171717; }
.tool-card__args { font-size: 11px; color: var(--clay-text-muted, #9f9b93); }
.tool-card__action {
  align-self: flex-start;
  border: 1px solid rgba(193, 176, 255, 0.42);
  background: rgba(243, 238, 255, 0.88);
  color: var(--clay-ube, #43089f);
  border-radius: 999px;
  padding: 6px 10px;
  font-size: 11px;
  font-weight: 800;
  cursor: pointer;
}
.tool-card__action:hover { transform: translateY(-1px); }
.tool-card__line { font-size: 12px; color: var(--clay-text-secondary, #55534e); line-height: 1.5; }

.typing-bubble { display: flex; gap: 4px; align-items: center; padding: 16px; }
.typing-label { font-size: 12px; font-weight: 700; color: var(--clay-text-secondary, #55534e); margin-right: 8px; }
.dot-bounce { width: 6px; height: 6px; background: var(--clay-text-muted, #9f9b93); border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
.dot-bounce:nth-child(1) { animation-delay: -0.32s; }
.dot-bounce:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

.chat-input-area { padding: 20px 24px; background: rgba(255, 255, 255, 0.4); border-top: 1px dashed var(--glass-border, rgba(218,212,200,0.4)); }
.input-wrapper { display: flex; gap: 12px; background: rgba(250, 249, 247, 0.6); padding: 6px 6px 6px 20px; border-radius: 999px; border: 1px solid var(--glass-border, rgba(218,212,200,0.4)); transition: border 0.2s; }
.input-wrapper:focus-within { border-color: var(--clay-ube, #43089f); background: #ffffff; }

input { flex: 1; border: none; background: transparent; outline: none; font-size: 14px; color: #000000; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); }
input::placeholder { color: var(--clay-text-muted, #9f9b93); }

.btn-send { display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; background: #000000; color: #ffffff; border: 1px solid #000000; border-radius: 50%; cursor: pointer; transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); flex-shrink: 0; }
.btn-send:hover:not(:disabled) { transform: rotateZ(-8deg) translateY(-2px); box-shadow: rgb(0,0,0) -7px 7px; background-color: var(--clay-lemon, #fbbd41); border-color: var(--clay-lemon, #fbbd41); }
.btn-send:disabled { background: var(--clay-border, #dad4c8); color: var(--clay-text-muted, #9f9b93); border-color: var(--clay-border, #dad4c8); cursor: not-allowed; }

@media (max-width: 900px) {
  .analysis-kpis,
  .analysis-grid {
    grid-template-columns: 1fr;
  }
}
</style>
