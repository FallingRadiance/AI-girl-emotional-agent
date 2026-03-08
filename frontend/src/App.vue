<template>
  <main class="layout">
    <section class="stage">
      <Live2DAvatar :emotion="emotion" />
      <div class="status">
        <span>当前技能: {{ skill }}</span>
        <span>当前情绪: {{ emotion }}</span>
      </div>
    </section>

    <section class="side">
      <ChatPanel :messages="messages" :loading="loading" @send="onSend" />
      <MemoryPanel :short-term="shortTerm" :long-term="longTerm" @refresh="loadMemory" />
      <div class="tools">
        <h3>Tools</h3>
        <ul>
          <li v-for="t in tools" :key="t.name">
            {{ t.name }}: {{ t.description }}
          </li>
        </ul>
      </div>
    </section>
  </main>
</template>

<script setup>
import { onMounted, onUnmounted, ref } from 'vue'
import ChatPanel from './components/ChatPanel.vue'
import Live2DAvatar from './components/Live2DAvatar.vue'
import MemoryPanel from './components/MemoryPanel.vue'
import { checkProactive, fetchMemory, fetchTools, sendMessage } from './services/api'

const sessionId = `user-${Math.random().toString(36).slice(2, 10)}`
const messages = ref([
  { role: 'assistant', content: '嗨，我是你的 AI Girl。今天想聊什么？', emotion: 'happy' }
])
const shortTerm = ref([])
const longTerm = ref([])
const tools = ref([])
const emotion = ref('happy')
const skill = ref('mood_booster')
const loading = ref(false)
let proactiveTimer
const hasUserSpoken = ref(false)

async function loadMemory() {
  const data = await fetchMemory(sessionId)
  shortTerm.value = data.short_term
  longTerm.value = data.long_term
}

async function onSend(text) {
  if (!hasUserSpoken.value) {
    hasUserSpoken.value = true
    if (!proactiveTimer) {
      proactiveTimer = setInterval(proactiveTick, 10000)
    }
  }

  messages.value.push({ role: 'user', content: text, emotion: 'neutral' })
  loading.value = true
  try {
    const res = await sendMessage(sessionId, text)
    emotion.value = res.emotion
    skill.value = res.skill
    messages.value.push({ role: 'assistant', content: res.reply, emotion: res.emotion })
    await loadMemory()
  } catch (e) {
    messages.value.push({ role: 'assistant', content: `请求失败: ${e.message}`, emotion: 'sad' })
    emotion.value = 'sad'
  } finally {
    loading.value = false
  }
}

async function proactiveTick() {
  try {
    const p = await checkProactive(sessionId)
    if (p.has_message) {
      emotion.value = p.emotion || 'neutral'
      skill.value = p.skill || skill.value
      messages.value.push({ role: 'assistant', content: p.reply, emotion: p.emotion || 'neutral' })
      await loadMemory()
    }
  } catch {
    // keep silent on proactive polling errors
  }
}

onMounted(async () => {
  tools.value = await fetchTools()
  await loadMemory()
})

onUnmounted(() => {
  clearInterval(proactiveTimer)
})
</script>
