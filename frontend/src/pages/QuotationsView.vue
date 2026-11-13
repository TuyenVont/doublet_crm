<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header><ViewBreadcrumbs routeName="Quotations" /></template>
      <template #right-header><Button v-if="canCreate" variant="solid" :label="__('Create Quotation')" iconLeft="plus" @click="router.push({ name: 'QuotationCreate' })" /></template>
    </LayoutHeader>
    <div class="flex flex-wrap items-center gap-2 border-b px-5 py-3">
      <TextInput v-model="search" type="search" :placeholder="__('Search quotation number')" @keyup.enter="load(true)" />
      <select v-model="status" class="rounded border px-2 py-1 text-sm" @change="load(true)">
        <option value="">{{ __('All statuses') }}</option><option v-for="s in statuses" :key="s">{{ s }}</option>
      </select>
      <Button :label="__('Search')" @click="load(true)" /><Button :label="__('Refresh')" :loading="loading" @click="load(true)" />
    </div>
    <div class="flex-1 overflow-auto p-5">
      <ErrorMessage v-if="error" :message="error" />
      <div v-if="loading && !rows.length" class="p-8 text-center">{{ __('Loading quotations...') }}</div>
      <div v-else-if="!rows.length && !error" class="p-8 text-center text-ink-gray-5">{{ __('No quotations found.') }}</div>
      <div v-else-if="rows.length" class="overflow-x-auto rounded border">
        <table class="w-full min-w-[760px] text-left text-sm">
          <thead><tr><th class="p-3">{{ __('Quotation') }}</th><th>{{ __('Customer') }}</th><th>{{ __('Deal') }}</th><th>{{ __('Date') }}</th><th>{{ __('Status') }}</th><th class="p-3 text-right">{{ __('Grand Total') }}</th></tr></thead>
          <tbody><tr v-for="row in rows" :key="row.name" class="cursor-pointer border-t hover:bg-surface-gray-1" @click="router.push({ name: 'QuotationDetail', params: { quotationId: row.name } })"><td class="p-3"><button class="hover:underline">{{ row.name }}</button></td><td>{{ customerLabels[row.company || row.contact] || row.company || row.contact || '—' }}</td><td><button v-if="dealLabels[row.deal]" class="hover:underline" @click.stop="openDeal(row.deal)">{{ dealLabels[row.deal] }}</button><span v-else>—</span></td><td>{{ row.quotation_date }}</td><td>{{ row.status }}</td><td class="p-3 text-right">{{ money(row.grand_total) }}</td></tr></tbody>
        </table>
      </div>
    </div>
    <div v-if="hasMore" class="border-t p-3 text-center"><Button :label="__('Load More')" :loading="loading" @click="load(false)" /></div>
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, TextInput, call } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import { money, message } from '@/utils/quotation'

const router = useRouter()
const statuses = ['Draft', 'Sent', 'Accepted', 'Rejected']
const search = ref(''), status = ref(''), rows = ref([]), error = ref('')
const customerLabels = ref({})
const dealLabels = ref({})
const loading = ref(false), hasMore = ref(false), canCreate = ref(false)
async function loadCustomerLabels(data) {
  const names = (field) => [...new Set(data.map(row => row[field]).filter(Boolean))]
  const [companies, contacts] = await Promise.allSettled([
    names('company').length ? call('frappe.client.get_list', { doctype: 'DoubleT Company', fields: ['name', 'company_name'], filters: { name: ['in', names('company')] }, limit_page_length: 20 }) : [],
    names('contact').length ? call('frappe.client.get_list', { doctype: 'DoubleT Contact', fields: ['name', 'first_name', 'last_name'], filters: { name: ['in', names('contact')] }, limit_page_length: 20 }) : [],
  ])
  if (companies.status === 'fulfilled') for (const c of companies.value) customerLabels.value[c.name] = c.company_name || c.name
  if (contacts.status === 'fulfilled') for (const c of contacts.value) customerLabels.value[c.name] = [c.first_name, c.last_name].filter(Boolean).join(' ') || c.name
}
async function loadDealLabels(data) {
  const names = [...new Set(data.map(row => row.deal).filter(Boolean))]
  if (!names.length) return
  const deals = await call('frappe.client.get_list', { doctype: 'DoubleT Deal', fields: ['name', 'deal_title'], filters: { name: ['in', names] }, limit_page_length: names.length })
  for (const deal of deals || []) dealLabels.value[deal.name] = deal.deal_title || __('Unnamed Deal')
}
function openDeal(dealId) { router.push({ name: 'DealDetail', params: { dealId } }) }
async function load(reset) {
  if (loading.value) return
  loading.value = true
  error.value = ''
  if (reset) { rows.value = []; hasMore.value = false; dealLabels.value = {} }
  try {
    const filters = []
    if (search.value.trim()) filters.push(['name', 'like', `%${search.value.trim()}%`])
    if (status.value) filters.push(['status', '=', status.value])
    const data = await call('frappe.client.get_list', { doctype: 'DoubleT Quotation', fields: ['name', 'contact', 'company', 'deal', 'quotation_date', 'status', 'grand_total'], filters, order_by: 'modified desc', limit_start: rows.value.length, limit_page_length: 20 })
    rows.value.push(...(data || [])); hasMore.value = data?.length === 20
    await Promise.allSettled([loadCustomerLabels(data || []), loadDealLabels(data || [])])
  } catch (e) { error.value = message(e) } finally { loading.value = false }
}
onMounted(async () => {
  status.value = router.currentRoute.value.query.status || ''
  load(true)
  try { canCreate.value = Boolean((await call('frappe.client.has_permission', { doctype: 'DoubleT Quotation', docname: '', perm_type: 'create' }))?.has_permission) } catch { canCreate.value = false }
})
</script>
