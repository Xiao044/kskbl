<template>
  <div class="chat-inner-container">
    
    <div class="chat-header">
      <div class="title-area">
        <h3 class="title">DeepSeek AI</h3>
        <span class="subtitle">AIOps 智能分析助理</span>
      </div>
      <div class="status-dot"></div>
    </div>
    
    <div class="chat-messages" ref="messageBox">
      <div v-for="msg in messages" :key="msg.id" :class="['msg-row', msg.senderId === 'me' ? 'is-me' : 'is-ai']">
        
        <div class="avatar" :class="msg.senderId === 'me' ? 'avatar-me' : 'avatar-ai'">
          {{ msg.senderId === 'me' ? 'U' : 'AI' }}
        </div>
        
        <div class="msg-content">
          <div class="msg-meta">
            <span class="name">{{ msg.senderId === 'me' ? '管理员' : 'DeepSeek' }}</span>
            <span class="time">{{ msg.time }}</span>
          </div>
          <div class="bubble">{{ msg.text }}</div>
        </div>
      </div>

      <div v-if="isAiTyping" class="msg-row is-ai">
        <div class="avatar avatar-ai">AI</div>
        <div class="msg-content">
          <div class="bubble typing-bubble">
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
  data() {
    return {
      ws: null,
      inputText: '',
      isAiTyping: false,
      messages: [
        {
          id: 'welcome', senderId: 'ai', targetId: 'me',
          text: '您好！我是 DeepSeek 运维助理。我已接入当前底层探针数据，您可以随时向我询问异常研判或防御策略。',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]
    }
  },
  mounted() { this.connectChatWS(); },
  beforeUnmount() { if (this.ws) this.ws.close(); },
  methods: {
    connectChatWS() {
      // 🌟 核心修改：动态获取当前浏览器访问的 IP 地址
      const serverIp = window.location.hostname;
      this.ws = new WebSocket(`ws://${serverIp}:8000/ws/chat`);
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        this.messages.push(data);
        if (data.senderId === 'ai') this.isAiTyping = false;
        this.scrollToBottom();
      };
      this.ws.onclose = () => { setTimeout(() => this.connectChatWS(), 3000); };
    },
    sendMessage() {
      if (!this.inputText.trim() || !this.ws) return;
      const newMsg = {
        id: Date.now().toString(), senderId: 'me', targetId: 'ai',
        text: this.inputText, time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      this.isAiTyping = true;
      this.ws.send(JSON.stringify(newMsg));
      this.inputText = '';
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
.chat-inner-container { display: flex; flex-direction: column; height: 100%; background: #ffffff; box-sizing: border-box; border-radius: 24px; border: 1px solid var(--clay-border, #dad4c8); box-shadow: var(--clay-shadow, rgba(0,0,0,0.1) 0px 1px 1px, rgba(0,0,0,0.04) 0px -1px 1px inset, rgba(0,0,0,0.05) 0px -0.5px 1px); }

/* 头部 */
.chat-header { padding: 24px; border-bottom: 1px solid var(--clay-border, #dad4c8); display: flex; justify-content: space-between; align-items: center; }
.title { margin: 0; font-size: 18px; font-weight: 600; color: #000000; letter-spacing: -0.36px; }
.subtitle { font-size: 12px; color: var(--clay-text-muted, #9f9b93); font-weight: 500; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; background: var(--clay-matcha, #078a52); box-shadow: 0 0 0 3px rgba(7, 138, 82, 0.2); }

/* 消息区 */
.chat-messages { flex: 1; padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; background: var(--clay-bg, #faf9f7); }
.chat-messages::-webkit-scrollbar { width: 4px; }
.chat-messages::-webkit-scrollbar-thumb { background: var(--clay-border, #dad4c8); border-radius: 4px; }

.msg-row { display: flex; gap: 12px; max-width: 85%; }
.msg-row.is-me { align-self: flex-end; flex-direction: row-reverse; }

/* 头像设计 — Clay 色板 */
.avatar { width: 36px; height: 36px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; }
.avatar-ai { background: var(--clay-ube, #43089f); color: #ffffff; }
.avatar-me { background: #000000; color: #ffffff; }

.msg-content { display: flex; flex-direction: column; gap: 6px; }
.is-me .msg-content { align-items: flex-end; }

.msg-meta { display: flex; gap: 8px; align-items: baseline; font-size: 12px; margin: 0 4px; }
.name { font-weight: 600; color: var(--clay-text-secondary, #55534e); }
.time { color: var(--clay-text-muted, #9f9b93); font-family: 'Space Mono', monospace; }

/* 气泡设计 — Clay 燕麦边框 + 冲压阴影 */
.bubble { padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.6; color: #000000; background: #ffffff; border: 1px solid var(--clay-border, #dad4c8); box-shadow: var(--clay-shadow, rgba(0,0,0,0.1) 0px 1px 1px, rgba(0,0,0,0.04) 0px -1px 1px inset, rgba(0,0,0,0.05) 0px -0.5px 1px); }
.is-me .bubble { background: #000000; color: #ffffff; border: none; border-top-right-radius: 4px; }
.is-ai .bubble { border-top-left-radius: 4px; }

/* 思考动画 */
.typing-bubble { display: flex; gap: 4px; align-items: center; padding: 16px; }
.dot-bounce { width: 6px; height: 6px; background: var(--clay-text-muted, #9f9b93); border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
.dot-bounce:nth-child(1) { animation-delay: -0.32s; }
.dot-bounce:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* 底部输入区 — Clay 风格 */
.chat-input-area { padding: 20px 24px; background: #ffffff; border-top: 1px dashed var(--clay-border, #dad4c8); }
.input-wrapper { display: flex; gap: 12px; background: var(--clay-bg, #faf9f7); padding: 6px 6px 6px 20px; border-radius: 999px; border: 1px solid var(--clay-border, #dad4c8); transition: border 0.2s; }
.input-wrapper:focus-within { border-color: var(--clay-ube, #43089f); background: #ffffff; }

input { flex: 1; border: none; background: transparent; outline: none; font-size: 14px; color: #000000; font-family: var(--clay-font, 'Roobert', 'Arial', sans-serif); }
input::placeholder { color: var(--clay-text-muted, #9f9b93); }

/* Clay 标志性 Hover 发送按钮 */
.btn-send { display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; background: #000000; color: #ffffff; border: 1px solid #000000; border-radius: 50%; cursor: pointer; transition: all 0.2s cubic-bezier(0.34, 1.56, 0.64, 1); flex-shrink: 0; }
.btn-send:hover:not(:disabled) { transform: rotateZ(-8deg) translateY(-2px); box-shadow: rgb(0,0,0) -7px 7px; background-color: var(--clay-lemon, #fbbd41); border-color: var(--clay-lemon, #fbbd41); }
.btn-send:disabled { background: var(--clay-border, #dad4c8); color: var(--clay-text-muted, #9f9b93); border-color: var(--clay-border, #dad4c8); cursor: not-allowed; }
</style>