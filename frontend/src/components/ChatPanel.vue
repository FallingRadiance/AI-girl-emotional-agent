<template>
  <div class="chat-panel">
    <div class="messages" ref="scrollRef">
      <div v-for="(m, idx) in messages" :key="idx" :class="['msg', m.role]">
        <div class="meta">{{ m.role }} · {{ m.emotion || '-' }}</div>
        <div class="text">{{ m.content }}</div>
      </div>
    </div>

    <form class="composer" @submit.prevent="submit">
      <input v-model="draft" placeholder="和她聊点什么..." />
      <button :disabled="loading">发送</button>
    </form>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'

const props = defineProps({
  messages: { type: Array, required: true },
  loading: { type: Boolean, default: false }
})
const emit = defineEmits(['send'])

const draft = ref('')
const scrollRef = ref(null)

function submit() {
  const val = draft.value.trim()
  if (!val) return
  emit('send', val)
  draft.value = ''
}

watch(
  () => props.messages.length,
  async () => {
    await nextTick()
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  }
)
</script>
