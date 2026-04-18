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
  emits: ['chat-focus', 'chat-blur', 'message-sent'],
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
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]
    }
  },
  computed: {
    statusText() {
      return this.isAiTyping ? this.pendingStatusLabel : '在线分析中';
    }
  },
  mounted() { this.connectChatWS(); },
  beforeUnmount() { if (this.ws) this.ws.close(); },
  methods: {
    messageSenderName(msg) {
      if (msg.senderId === 'me') return '管理员';
      if (msg.senderId === 'system') return 'System';
      return msg.senderName || 'DeepSeek';
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
    connectChatWS() {
      const serverIp = window.location.hostname;
      this.ws = new WebSocket(`ws://${serverIp}:8000/ws/chat`);

      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.messages.push(data);
        if (data.senderId === 'ai' || data.senderId === 'system') this.isAiTyping = false;
        this.scrollToBottom();
      };
      this.ws.onclose = () => { setTimeout(() => this.connectChatWS(), 3000); };
    },
    sendMessage() {
      if (!this.inputText.trim() || !this.ws) return;
      this.pendingStatusLabel = this.inferPendingStatus(this.inputText);
      const newMsg = {
        id: Date.now().toString(),
        senderId: 'me',
        targetId: 'ai',
        text: this.inputText,
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
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
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
</style>
