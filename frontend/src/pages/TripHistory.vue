<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'

const items = ref([])

onMounted(async () => {
  const rows = (await getJSON('/api/history')).items
  items.value = rows.map(h => {
    let input = {}, result = {}
    try { input = JSON.parse(h.input_json) } catch { /* keep empty */ }
    try { result = JSON.parse(h.result_json) } catch { /* keep empty */ }
    return { ...h, input, result }
  })
})
</script>

<template>
  <div class="page"><h1>试算记录</h1>
    <table>
      <thead><tr><th>#</th><th>起终</th><th>途经站</th><th>换乘</th><th>加价</th><th>应付</th><th>时间</th></tr></thead>
      <tbody>
        <tr v-for="h in items" :key="h.id">
          <td>#{{ h.id }}</td>
          <td>{{ h.input.start }} → {{ h.input.end }}</td>
          <td>{{ h.result.path ? h.result.path.join(' → ') : '—' }}</td>
          <td>{{ h.result.transfers ?? '—' }}</td>
          <td>{{ h.result.surcharge != null ? '¥' + h.result.surcharge.toFixed(2) : '—' }}</td>
          <td>{{ h.result.fare != null ? '¥' + h.result.fare.toFixed(2) : '—' }}</td>
          <td>{{ h.created_at }}</td>
        </tr>
      </tbody>
    </table>
    <p class="muted">记录保存试算当时的途经站与加价，后续改规则不会改写。</p>
  </div>
</template>
