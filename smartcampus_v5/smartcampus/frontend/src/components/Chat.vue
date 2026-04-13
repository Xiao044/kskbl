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
      this.ws = new WebSocket("ws://localhost:8000/ws/chat");
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
.chat-inner-container { display: flex; flex-direction: column; height: 100%; background: #ffffff; box-sizing: border-box; }

/* 头部 */
.chat-header { padding: 24px; border-bottom: 1px solid #f4f4f5; display: flex; justify-content: space-between; align-items: center; }
.title { margin: 0; font-size: 18px; font-weight: 700; color: #171717; }
.subtitle { font-size: 12px; color: #737373; font-weight: 500; }
.status-dot { width: 10px; height: 10px; border-radius: 50%; background: #16a34a; box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.2); }

/* 消息区 */
.chat-messages { flex: 1; padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; background: #fafafa; }
.chat-messages::-webkit-scrollbar { width: 4px; }
.chat-messages::-webkit-scrollbar-thumb { background: #d4d4d8; border-radius: 4px; }

.msg-row { display: flex; gap: 12px; max-width: 85%; }
.msg-row.is-me { align-self: flex-end; flex-direction: row-reverse; }

/* 头像设计 */
.avatar { width: 36px; height: 36px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 14px; flex-shrink: 0; }
.avatar-ai { background: #6d28d9; color: #ffffff; } /* AI 使用深紫色 */
.avatar-me { background: #171717; color: #ffffff; } /* 用户使用纯黑色 */

.msg-content { display: flex; flex-direction: column; gap: 6px; }
.is-me .msg-content { align-items: flex-end; }

.msg-meta { display: flex; gap: 8px; align-items: baseline; font-size: 12px; margin: 0 4px; }
.name { font-weight: 600; color: #52525b; }
.time { color: #a1a1aa; }

/* 气泡设计 */
.bubble { padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.6; color: #171717; background: #ffffff; border: 1px solid #e4e4e7; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.is-me .bubble { background: #171717; color: #ffffff; border: none; border-top-right-radius: 4px; }
.is-ai .bubble { border-top-left-radius: 4px; }

/* 思考动画 */
.typing-bubble { display: flex; gap: 4px; align-items: center; padding: 16px; }
.dot-bounce { width: 6px; height: 6px; background: #a1a1aa; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
.dot-bounce:nth-child(1) { animation-delay: -0.32s; }
.dot-bounce:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* 底部输入区 */
.chat-input-area { padding: 20px 24px; background: #ffffff; border-top: 1px solid #f4f4f5; }
.input-wrapper { display: flex; gap: 12px; background: #f4f4f5; padding: 6px 6px 6px 20px; border-radius: 999px; border: 1px solid transparent; transition: border 0.2s; }
.input-wrapper:focus-within { border-color: #d4d4d8; background: #ffffff; }

input { flex: 1; border: none; background: transparent; outline: none; font-size: 14px; color: #171717; }
input::placeholder { color: #a1a1aa; }

/* 纯黑胶囊按钮 */
.btn-send { display: flex; align-items: center; justify-content: center; width: 40px; height: 40px; background: #171717; color: #ffffff; border: none; border-radius: 50%; cursor: pointer; transition: background 0.2s, transform 0.1s; flex-shrink: 0; }
.btn-send:hover:not(:disabled) { background: #262626; transform: scale(1.05); }
.btn-send:disabled { background: #d4d4d8; color: #a1a1aa; cursor: not-allowed; }
</style>