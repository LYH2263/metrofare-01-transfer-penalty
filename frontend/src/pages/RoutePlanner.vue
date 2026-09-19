<script setup>
import { onMounted, ref } from 'vue'
import { getJSON, postJSON } from '../api'

const stations = ref([])
const start = ref('A1')
const end = ref('B2')
const out = ref(null)
const error = ref('')
const saved = ref(false)

onMounted(async () => { stations.value = (await getJSON('/api/stations')).items })

const nameOf = (code) => stations.value.find(s => s.code === code)?.name || code

const run = async (persist) => {
  error.value = ''
  saved.value = false
  try {
    out.value = await postJSON('/api/quote', { start: start.value, end: end.value, persist })
    saved.value = persist && out.value.run_id != null
  } catch (e) { error.value = e.message }
}
</script>

<template>
  <div class="page"><h1>最短站数票价</h1>
    <div class="panel">
      <select v-model="start"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}({{ s.code }})</option></select>
      →
      <select v-model="end"><option v-for="s in stations" :key="s.code" :value="s.code">{{ s.name }}({{ s.code }})</option></select>
      <button @click="run(false)">试算</button>
      <button class="ghost" @click="run(true)">试算并保存</button>
      <p v-if="error" class="error">{{ error }}</p>
    </div>

    <div v-if="out" class="panel">
      <template v-if="out.reachable">
        <div class="path-row">
          <template v-for="(code, i) in out.path" :key="i">
            <span v-if="i > 0" class="edge-tag" :class="{ hot: out.edge_lines[i - 1] !== out.edge_lines[i] }">{{ out.edge_lines[i - 1] }} →</span>
            <span class="station-chip">{{ nameOf(code) }}<small>{{ code }}</small></span>
          </template>
        </div>

        <h2>换线明细</h2>
        <ul v-if="out.transfer_events && out.transfer_events.length">
          <li v-for="(t, i) in out.transfer_events" :key="i">
            在 {{ nameOf(t.at) }}({{ t.at }}) 换线：{{ t.from_line }} → {{ t.to_line }}，加价 ¥{{ t.amount.toFixed(2) }}
          </li>
        </ul>
        <p v-else class="muted">全程同线，无换乘</p>

        <p>站数 {{ out.hops }} · 基础票价 ¥{{ out.base_fare.toFixed(2) }} · 换乘 {{ out.transfers }} 次 · 加价合计 ¥{{ out.surcharge.toFixed(2) }}</p>
        <p>应付 <span class="hero-num">¥{{ out.fare.toFixed(2) }}</span></p>
        <p class="muted">{{ saved ? `已保存为记录 #${out.run_id}` : '只读试算，未写入记录' }}</p>
      </template>
      <p v-else class="muted">不可达</p>
    </div>
  </div>
</template>
