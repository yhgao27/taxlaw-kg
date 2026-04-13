<template>
  <div class="query-page">
    <div class="header">
      <h2>智能问答</h2>
    </div>

    <el-row :gutter="20">
      <!-- 问答区域 -->
      <el-col :span="16">
        <el-card class="chat-card">
          <!-- 聊天历史 -->
          <div ref="chatContainer" class="chat-container">
            <div v-if="messages.length === 0" class="empty-state">
              <el-icon size="60" color="#ccc"><ChatDotRound /></el-icon>
              <p>输入您的问题，开始智能问答</p>
            </div>

            <div
              v-for="(msg, index) in messages"
              :key="index"
              :class="['message', msg.type]"
            >
              <div class="message-avatar">
                <el-icon v-if="msg.type === 'user'" size="24"><User /></el-icon>
                <el-icon v-else size="24"><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-text">{{ msg.content }}</div>
                <div class="message-time">{{ msg.time }}</div>
              </div>
            </div>

            <div v-if="loading" class="message assistant">
              <div class="message-avatar">
                <el-icon size="24"><ChatDotRound /></el-icon>
              </div>
              <div class="message-content">
                <div class="message-text loading">
                  <span class="dot"></span>
                  <span class="dot"></span>
                  <span class="dot"></span>
                </div>
              </div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="input-area">
            <el-input
              v-model="question"
              type="textarea"
              :rows="2"
              placeholder="请输入问题，例如：小规模纳税人增值税税率是多少？"
              @keyup.enter.ctrl="sendQuestion"
            />
            <el-button
              type="primary"
              :loading="loading"
              :disabled="!question.trim()"
              @click="sendQuestion"
            >
              发送 (Ctrl+Enter)
            </el-button>
          </div>
        </el-card>
      </el-col>

      <!-- 快捷问题 -->
      <el-col :span="8">
        <el-card title="快捷问题">
          <template #header>
            <span>快捷问题</span>
          </template>

          <el-space direction="vertical" fill style="width: 100%">
            <el-button
              v-for="q in quickQuestions"
              :key="q"
              class="quick-question-btn"
              @click="askQuickQuestion(q)"
            >
              {{ q }}
            </el-button>
          </el-space>
        </el-card>

        <!-- Schema 上下文 -->
        <el-card class="schema-card">
          <template #header>
            <span>当前 Schema 上下文</span>
          </template>

          <div v-if="schemaContext" class="schema-info">
            <h4>实体类型</h4>
            <el-tag
              v-for="et in schemaContext.entity_types"
              :key="et.name"
              size="small"
              class="schema-tag"
            >
              {{ et.name }}
            </el-tag>

            <h4>关系类型</h4>
            <div
              v-for="rt in schemaContext.relation_types"
              :key="rt.name"
              class="relation-item"
            >
              {{ rt.source }} → {{ rt.name }} → {{ rt.target }}
            </div>
          </div>

          <el-empty v-else description="暂无 Schema 配置" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { queryApi, type QueryResponse } from '../api'

interface Message {
  type: 'user' | 'assistant'
  content: string
  time: string
  sources?: QueryResponse['sources']
}

const question = ref('')
const loading = ref(false)
const messages = ref<Message[]>([])
const chatContainer = ref<HTMLElement | null>(null)

const quickQuestions = [
  '小规模纳税人增值税税率是多少？',
  '企业所得税的法定税率是多少？',
  '高新技术企业可以享受哪些税收优惠？',
  '哪些企业可以享受15%的优惠税率？',
  '一般纳税人和小规模纳税人的区别是什么？'
]

const schemaContext = ref<{
  entity_types: { name: string; description: string }[]
  relation_types: { name: string; source: string; target: string }[]
} | null>(null)

const fetchSchemaContext = async () => {
  try {
    schemaContext.value = await queryApi.getSchemaContext()
  } catch (error) {
    console.error('获取 Schema 上下文失败', error)
  }
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatContainer.value) {
      chatContainer.value.scrollTop = chatContainer.value.scrollHeight
    }
  })
}

const sendQuestion = async () => {
  const q = question.value.trim()
  if (!q || loading.value) return

  // 添加用户消息
  const now = new Date()
  messages.value.push({
    type: 'user',
    content: q,
    time: now.toLocaleTimeString()
  })

  question.value = ''
  scrollToBottom()

  // 调用问答接口
  loading.value = true
  try {
    const response = await queryApi.ask({
      question: q,
      use_kg: true,
      use_vector: true,
      top_k: 10
    })

    messages.value.push({
      type: 'assistant',
      content: response.answer,
      time: new Date().toLocaleTimeString(),
      sources: response.sources
    })
  } catch (error) {
    ElMessage.error('问答服务暂时不可用')
    messages.value.push({
      type: 'assistant',
      content: '抱歉，问答服务暂时不可用，请稍后重试。',
      time: new Date().toLocaleTimeString()
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const askQuickQuestion = (q: string) => {
  question.value = q
  sendQuestion()
}

onMounted(() => {
  fetchSchemaContext()
})
</script>

<style scoped>
.query-page {
  padding: 20px;
  height: calc(100vh - 60px);
}

.header {
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}

.chat-card {
  height: calc(100vh - 140px);
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.empty-state p {
  margin-top: 10px;
}

.message {
  display: flex;
  gap: 15px;
  margin-bottom: 20px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background-color: #409eff;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message.assistant .message-avatar {
  background-color: #67c23a;
}

.message-content {
  max-width: 70%;
}

.message.user .message-content {
  text-align: right;
}

.message-text {
  padding: 12px 16px;
  border-radius: 8px;
  background-color: #f5f5f5;
  line-height: 1.6;
  white-space: pre-wrap;
}

.message.user .message-text {
  background-color: #409eff;
  color: #fff;
}

.message.assistant .message-text {
  background-color: #f0f9ff;
}

.message-time {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.message-text.loading {
  display: flex;
  gap: 4px;
  padding: 16px 24px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #999;
  animation: bounce 1.4s infinite ease-in-out both;
}

.dot:nth-child(1) { animation-delay: -0.32s; }
.dot:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.input-area {
  display: flex;
  gap: 10px;
  padding: 15px;
  border-top: 1px solid #eee;
}

.input-area .el-textarea {
  flex: 1;
}

.quick-question-btn {
  width: 100%;
  justify-content: flex-start;
  text-align: left;
}

.schema-card {
  margin-top: 20px;
}

.schema-info h4 {
  margin: 10px 0 5px;
  font-size: 14px;
  color: #666;
}

.schema-tag {
  margin-right: 5px;
  margin-bottom: 5px;
}

.relation-item {
  font-size: 12px;
  color: #666;
  padding: 4px 0;
}
</style>
