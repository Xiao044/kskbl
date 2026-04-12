<template>
  <div class="chat-container">
    <div class="chat-header">
      <div class="header-info">
        <h3>网络运维 AI 助手</h3>
        <span class="status"><span class="dot online"></span> Gemini 引擎已连接</span>
      </div>
    </div>
    
    <div class="chat-messages" ref="messageBox">
      <div v-for="msg in messages" :key="msg.id" :class="['message-wrapper', msg.senderId === 'me' ? 'mine' : 'others']">
        <div class="avatar">{{ msg.senderName.charAt(0) }}</div>
        <div class="message-content">
          <div class="message-info">
            <span class="name">{{ msg.senderName }}</span>
            <span class="time">{{ msg.time }}</span>
          </div>
          <div class="bubble">{{ msg.text }}</div>
        </div>
      </div>
      <div v-if="isAiTyping" class="message-wrapper others">
        <div class="avatar">A</div>
        <div class="message-content">
          <div class="bubble typing">AI 正在思考中<span class="dots">...</span></div>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <input 
        type="text" 
        v-model="inputText" 
        @keyup.enter="sendMessage"
        placeholder="输入指令，例如：当前网络有什么异常告警吗？"
      />
      <button @click="sendMessage" :disabled="!inputText.trim()">发送指令</button>
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
          id: 'welcome',
          senderId: 'ai',
          targetId: 'me',
          senderName: '网络运维 AI',
          text: '您好！我是集成在 Net Monitor 中的大模型运维助手。您可以随时向我询问当前的网络状态、威胁研判建议或防御策略。',
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]
    }
  },
  mounted() {
    this.connectChatWS()
  },
  beforeUnmount() {
    if (this.ws) this.ws.close()
  },
  methods: {
    connectChatWS() {
      this.ws = new WebSocket("ws://localhost:8000/ws/chat")
      
      this.ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        // 收到消息，加入列表
        this.messages.push(data)
        // 如果收到的是 AI 的回复，关闭“思考中”状态
        if (data.senderId === 'ai') {
          this.isAiTyping = false
        }
        this.scrollToBottom()
      }

      this.ws.onclose = () => {
        setTimeout(() => this.connectChatWS(), 3000)
      }
    },
    sendMessage() {
      if (!this.inputText.trim() || !this.ws) return;

      const newMsg = {
        id: Date.now().toString(),
        senderId: 'me',
        targetId: 'ai', // 🌟 核心暗号：明确告诉后端这是发给 AI 的
        senderName: '管理员',
        text: this.inputText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }

      // 开启 AI 思考动画
      this.isAiTyping = true
      
      // 发送给后端
      this.ws.send(JSON.stringify(newMsg))
      
      this.inputText = ''
      this.scrollToBottom()
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const box = this.$refs.messageBox
        if (box) {
          box.scrollTop = box.scrollHeight
        }
      })
    }
  }
}
</script>

<style scoped>
.chat-container { display: flex; flex-direction: column; height: 100%; background: #ffffff; border-radius: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.03); border: 1px solid #f1f5f9; overflow: hidden; }
.chat-header { padding: 20px 24px; border-bottom: 1px solid #f1f5f9; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; }
.header-info h3 { margin: 0 0 6px 0; color: #1e293b; font-size: 16px; }
.status { font-size: 13px; color: #64748b; display: flex; align-items: center; gap: 6px; }
.dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; } .dot.online { background-color: #10b981; }
.chat-messages { flex: 1; padding: 24px; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; background: #f4f7f6; }
.message-wrapper { display: flex; gap: 12px; max-width: 80%; }
.message-wrapper.mine { align-self: flex-end; flex-direction: row-reverse; }
.avatar { width: 40px; height: 40px; border-radius: 12px; background: #e2e8f0; color: #64748b; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 16px; flex-shrink: 0; }
.mine .avatar { background: #0ea5e9; color: white; } .others .avatar { background: #10b981; color: white; }
.message-content { display: flex; flex-direction: column; gap: 4px; }
.mine .message-content { align-items: flex-end; }
.message-info { display: flex; gap: 8px; font-size: 12px; color: #94a3b8; margin: 0 4px; }
.bubble { padding: 12px 16px; border-radius: 16px; font-size: 14px; line-height: 1.5; color: #334155; background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.mine .bubble { background: #0ea5e9; color: #ffffff; border-top-right-radius: 4px; } .others .bubble { border-top-left-radius: 4px; }
.typing { color: #94a3b8; font-style: italic; } .dots { animation: blink 1.5s infinite; } @keyframes blink { 0% { opacity: .2; } 20% { opacity: 1; } 100% { opacity: .2; } }
.chat-input-area { padding: 20px 24px; background: #ffffff; border-top: 1px solid #f1f5f9; display: flex; gap: 12px; }
input { flex: 1; padding: 12px 16px; border: 1px solid #e2e8f0; border-radius: 8px; outline: none; font-size: 14px; transition: border-color 0.2s; } input:focus { border-color: #0ea5e9; }
button { padding: 0 24px; background: #0ea5e9; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; } button:hover { background: #0284c7; } button:disabled { background: #cbd5e1; cursor: not-allowed; }
</style>