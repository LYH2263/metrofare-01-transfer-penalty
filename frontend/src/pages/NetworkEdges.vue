<script setup>
import { onMounted, ref } from 'vue'
import { getJSON } from '../api'
const items = ref([])
onMounted(async () => { items.value = (await getJSON('/api/edges')).items })
</script>
<template>
  <div class="page"><h1>邻接区间</h1>
    <table>
      <thead><tr><th>起点</th><th>终点</th><th>所属线路</th></tr></thead>
      <tbody><tr v-for="(e,i) in items" :key="i"><td>{{ e.a }}</td><td>{{ e.b }}</td><td>{{ e.line }}</td></tr></tbody>
    </table>
  </div>
</template>
