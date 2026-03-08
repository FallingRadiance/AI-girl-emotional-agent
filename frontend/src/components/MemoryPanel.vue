<template>
  <div class="memory-panel">
    <div class="memory-header">
      <h3>记忆系统</h3>
      <button @click="$emit('refresh')">刷新</button>
    </div>
    <div class="memory-grid">
      <section>
        <h4>短期记忆</h4>
        <ul>
          <li v-for="(m, idx) in shortTerm" :key="`s-${idx}`">
            {{ m.role }}: {{ m.content }}
          </li>
        </ul>
      </section>
      <section>
        <h4>长期记忆</h4>
        <ul>
          <li v-for="(m, idx) in longTerm" :key="`l-${idx}`">
            {{ m.key }}: {{ m.value }}
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>

<script setup>
defineProps({
  shortTerm: { type: Array, default: () => [] },
  longTerm: { type: Array, default: () => [] }
})
</script>
