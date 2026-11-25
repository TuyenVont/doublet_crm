<template>
  <div class="flex flex-wrap items-center gap-2 border-t border-outline-gray-1 pt-3">
    <Button :label="__('Export CSV')" :loading="exporting" :disabled="!enabled" @click="exportCsv" />
    <select v-model="selected" class="h-8 min-w-44 rounded border border-outline-gray-2 bg-surface-white px-2 text-sm">
      <option value="">{{ __('Saved filters') }}</option>
      <option v-for="item in saved" :key="item.name" :value="item.name">{{ item.name }}</option>
    </select>
    <Button :label="__('Apply saved')" :disabled="!selected" @click="applySaved" />
    <Button :label="__('Save current')" @click="saveCurrent" />
    <Button :label="__('Delete saved')" :disabled="!selected" @click="deleteSaved" />
    <span v-if="status" class="text-xs text-ink-gray-5" role="status">{{ status }}</span>
    <span v-if="error" class="text-xs text-ink-red-3" role="alert">{{ error }}</span>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { call } from 'frappe-ui'

import { message } from '@/utils/quotation'

const props = defineProps({
  reportKey: { type: String, required: true },
  filters: { type: Object, required: true },
  enabled: { type: Boolean, default: false },
})
const emit = defineEmits(['restore'])
const saved = ref([])
const selected = ref('')
const exporting = ref(false)
const status = ref('')
const error = ref('')

async function loadSaved() {
  error.value = ''
  try {
    saved.value = await call('doublet_crm.report_tools.get_saved_filters', { report: props.reportKey })
    if (selected.value && !saved.value.some(item => item.name === selected.value)) selected.value = ''
  } catch (requestError) {
    error.value = message(requestError)
  }
}

async function exportCsv() {
  if (!props.enabled) return
  exporting.value = true; error.value = ''; status.value = ''
  try {
    const result = await call('doublet_crm.report_tools.export_report', { report: props.reportKey, filters: JSON.stringify(props.filters) })
    const url = URL.createObjectURL(new Blob([result.content], { type: result.mime_type }))
    const link = document.createElement('a')
    link.href = url; link.download = result.filename; link.click()
    URL.revokeObjectURL(url)
    status.value = __('Exported {0} authorized row(s).'.replace('{0}', String(result.row_count)))
  } catch (requestError) {
    error.value = message(requestError)
  } finally {
    exporting.value = false
  }
}

async function saveCurrent() {
  const name = window.prompt(__('Name this personal filter'))?.trim()
  if (!name) return
  error.value = ''; status.value = ''
  try {
    saved.value = await call('doublet_crm.report_tools.save_filter', { report: props.reportKey, name, filters: JSON.stringify(props.filters) })
    selected.value = name
    status.value = __('Saved for your account.')
  } catch (requestError) {
    error.value = message(requestError)
  }
}

function applySaved() {
  const item = saved.value.find(entry => entry.name === selected.value)
  if (item) emit('restore', { ...item.filters })
}

async function deleteSaved() {
  if (!selected.value) return
  error.value = ''; status.value = ''
  try {
    saved.value = await call('doublet_crm.report_tools.delete_filter', { report: props.reportKey, name: selected.value })
    selected.value = ''
    status.value = __('Saved filter deleted.')
  } catch (requestError) {
    error.value = message(requestError)
  }
}

watch(() => props.reportKey, loadSaved)
onMounted(loadSaved)
</script>
