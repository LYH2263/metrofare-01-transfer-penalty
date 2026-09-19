<script setup>
import { computed, onMounted, ref } from 'vue'
import { getJSON, postJSON, putJSON } from '../api'

const items = ref([])
const rules = ref([])
const stations = ref([])
const error = ref('')
const form = ref({ from_line: '', to_line: '', amount: 1 })
const editingId = ref(null)
const editForm = ref({})

const lines = computed(() => [...new Set(stations.value.map(s => s.line).filter(Boolean))])

const reloadRules = async () => { rules.value = (await getJSON('/api/transfer-rules')).items }

onMounted(async () => {
  items.value = (await getJSON('/api/fare-rules')).items
  stations.value = (await getJSON('/api/stations')).items
  await reloadRules()
})

const guard = async (fn) => {
  error.value = ''
  try { await fn(); await reloadRules() } catch (e) { error.value = e.message }
}

const create = () => guard(async () => {
  await postJSON('/api/transfer-rules', { ...form.value, amount: Number(form.value.amount) })
  form.value = { from_line: '', to_line: '', amount: 1 }
})

const startEdit = (r) => {
  editingId.value = r.id
  editForm.value = { from_line: r.from_line, to_line: r.to_line, amount: r.amount, active: r.active }
}
const saveEdit = (id) => guard(async () => {
  await putJSON(`/api/transfer-rules/${id}`, { ...editForm.value, amount: Number(editForm.value.amount) })
  editingId.value = null
})
const disable = (id) => guard(() => postJSON(`/api/transfer-rules/${id}/disable`, {}))
</script>

<template>
  <div class="page">
    <h1>票价阶梯(按站数)</h1>
    <table><thead><tr><th>最多站数</th><th>票价</th></tr></thead>
      <tbody><tr v-for="r in items" :key="r.id"><td>{{ r.max_hops ?? '以上' }}</td><td>{{ r.price }}</td></tr></tbody></table>

    <h1>换乘加价(按线路对)</h1>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="panel">
      <table>
        <thead><tr><th>#</th><th>离开线路</th><th>进入线路</th><th>加价</th><th>状态</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="r in rules" :key="r.id">
            <template v-if="editingId === r.id">
              <td>#{{ r.id }}</td>
              <td><select v-model="editForm.from_line"><option v-for="l in lines" :key="l" :value="l">{{ l }}</option></select></td>
              <td><select v-model="editForm.to_line"><option v-for="l in lines" :key="l" :value="l">{{ l }}</option></select></td>
              <td><input v-model="editForm.amount" type="number" min="0" step="0.5" class="num" /></td>
              <td><label><input v-model="editForm.active" type="checkbox" /> 启用</label></td>
              <td>
                <button @click="saveEdit(r.id)">保存</button>
                <button class="ghost" @click="editingId = null">取消</button>
              </td>
            </template>
            <template v-else>
              <td>#{{ r.id }}</td>
              <td>{{ r.from_line }}</td>
              <td>{{ r.to_line }}</td>
              <td>¥{{ r.amount.toFixed(2) }}</td>
              <td><span :class="r.active ? 'badge-on' : 'badge-off'">{{ r.active ? '启用' : '停用' }}</span></td>
              <td>
                <button class="ghost" @click="startEdit(r)">编辑</button>
                <button v-if="r.active" class="ghost" @click="disable(r.id)">停用</button>
              </td>
            </template>
          </tr>
          <tr v-if="!rules.length"><td colspan="6" class="muted">暂无换乘加价规则</td></tr>
        </tbody>
      </table>
    </div>

    <div class="panel">
      <h2>新增线路对加价</h2>
      <div class="form-row">
        <select v-model="form.from_line"><option disabled value="">离开线路</option>
          <option v-for="l in lines" :key="l" :value="l">{{ l }}</option></select>
        →
        <select v-model="form.to_line"><option disabled value="">进入线路</option>
          <option v-for="l in lines" :key="l" :value="l">{{ l }}</option></select>
        <input v-model="form.amount" type="number" min="0" step="0.5" class="num" placeholder="加价金额" />
        <button :disabled="!form.from_line || !form.to_line" @click="create">创建</button>
      </div>
    </div>
  </div>
</template>
