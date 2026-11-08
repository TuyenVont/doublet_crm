<template>
  <div class="flex min-h-0 w-full flex-col overflow-hidden">
    <div class="flex items-center justify-between gap-3 border-b px-5 py-3">
      <h2 class="font-semibold">{{ __('Quotations') }}</h2>
      <div class="flex gap-2">
        <Button :label="__('Refresh')" :loading="loading" @click="load(true)" />
        <Button v-if="canCreate" variant="solid" :label="__('Create Quotation')" @click="router.push({ name: 'QuotationCreate', query: { deal: dealId } })" />
      </div>
    </div>
    <div class="flex-1 overflow-auto p-5">
      <p v-if="denied" class="text-sm text-red-600">{{ __('You do not have permission to view quotations. Ask an administrator for access.') }}</p>
      <div v-else-if="error" class="space-y-2 text-sm text-red-600"><p>{{ error }}</p><Button :label="__('Retry')" @click="load(true)" /></div>
      <p v-if="loading && !rows.length" class="p-8 text-center">{{ __('Loading quotations...') }}</p>
      <p v-else-if="!rows.length && !error && !denied" class="p-8 text-center text-ink-gray-5">{{ __('No quotations for this Deal.') }}</p>
      <div v-else-if="rows.length && !error && !denied" class="overflow-x-auto rounded border">
        <table class="w-full min-w-[650px] text-left text-sm">
          <thead><tr><th class="p-3">{{ __('Quotation') }}</th><th>{{ __('Status') }}</th><th>{{ __('Quotation Date') }}</th><th>{{ __('Valid Until') }}</th><th class="p-3 text-right">{{ __('Grand Total') }}</th></tr></thead>
          <tbody><tr v-for="row in rows" :key="row.name" class="cursor-pointer border-t hover:bg-surface-gray-1" @click="router.push({ name: 'QuotationDetail', params: { quotationId: row.name } })"><td class="p-3"><button class="hover:underline">{{ row.name }}</button></td><td>{{ row.status }}</td><td>{{ row.quotation_date }}</td><td>{{ row.valid_until }}</td><td class="p-3 text-right">{{ money(row.grand_total) }}</td></tr></tbody>
        </table>
      </div>
      <div v-if="hasMore && !error && !denied" class="mt-3 text-center"><Button :label="__('Load More')" :loading="loading" @click="load(false)" /></div>
    </div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { Button, call } from 'frappe-ui'
import { message, money } from '@/utils/quotation'

const props = defineProps({ dealId: { type: String, required: true } })
const router = useRouter()
const rows = ref([]), loading = ref(false), error = ref(''), denied = ref(false), hasMore = ref(false), canCreate = ref(false)
let requestId = 0

async function load(reset) {
  if (!props.dealId || (!reset && loading.value)) return
  const id = ++requestId
  const deal = props.dealId
  if (reset) { rows.value = []; hasMore.value = false }
  loading.value = true; error.value = ''; denied.value = false
  try {
    const data = await call('frappe.client.get_list', {
      doctype: 'DoubleT Quotation',
      fields: ['name', 'status', 'quotation_date', 'valid_until', 'grand_total'],
      filters: { deal }, order_by: 'creation desc', limit_start: rows.value.length, limit_page_length: 20,
    })
    if (id !== requestId) return
    rows.value.push(...(data || [])); hasMore.value = data?.length === 20
  } catch (e) {
    if (id !== requestId) return
    denied.value = e?.status === 403 || e?.exc_type === 'PermissionError'
    if (!denied.value) error.value = message(e)
  } finally { if (id === requestId) loading.value = false }
}

watch(() => props.dealId, () => load(true), { immediate: true })
call('frappe.client.has_permission', { doctype: 'DoubleT Quotation', docname: '', perm_type: 'create' })
  .then(result => { canCreate.value = Boolean(result?.has_permission) })
  .catch(() => { canCreate.value = false })
onBeforeUnmount(() => { requestId++ })
</script>
