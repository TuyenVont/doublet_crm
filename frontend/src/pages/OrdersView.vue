<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header><ViewBreadcrumbs routeName="Orders" /></template>
      <template #right-header><Button v-if="canCreate" variant="solid" :label="__('Create Order')" iconLeft="plus" @click="router.push({ name: 'OrderCreate' })" /></template>
    </LayoutHeader>
    <div class="flex flex-wrap items-center gap-2 border-b px-5 py-3">
      <TextInput v-model="search" type="search" :placeholder="__('Search order number')" @keyup.enter="load(true)" />
      <select v-model="status" class="rounded border px-2 py-1 text-sm" @change="load(true)">
        <option value="">{{ __('All statuses') }}</option><option v-for="s in statuses" :key="s">{{ s }}</option>
      </select>
      <Button :label="__('Search')" @click="load(true)" /><Button :label="__('Refresh')" :loading="loading" @click="load(true)" />
    </div>
    <div class="flex-1 overflow-auto p-5">
      <ErrorMessage v-if="error" :message="error" />
      <div v-if="loading && !rows.length" class="p-8 text-center">{{ __('Loading orders...') }}</div>
      <div v-else-if="!rows.length && !error" class="p-8 text-center text-ink-gray-5">{{ __('No orders found.') }}</div>
      <div v-else-if="rows.length" class="overflow-x-auto rounded border">
        <table class="w-full min-w-[760px] text-left text-sm">
          <thead><tr><th class="p-3">{{ __('Order') }}</th><th>{{ __('Customer') }}</th><th>{{ __('Deal') }}</th><th>{{ __('Date') }}</th><th>{{ __('Status') }}</th><th class="p-3 text-right">{{ __('Total') }}</th></tr></thead>
          <tbody><tr v-for="row in rows" :key="row.name" class="cursor-pointer border-t hover:bg-surface-gray-1" @click="router.push({ name: 'OrderDetail', params: { orderId: row.name } })"><td class="p-3"><button class="hover:underline">{{ row.name }}</button></td><td><RouterLink v-if="row.company || row.contact" class="hover:underline" :to="customerRoute(row)" @click.stop>{{ customerLabels[row.company || row.contact] || row.company || row.contact }}</RouterLink><span v-else>—</span></td><td><button v-if="dealLabels[row.deal]" class="hover:underline" @click.stop="openDeal(row.deal)">{{ dealLabels[row.deal] }}</button><span v-else>—</span></td><td>{{ row.order_date }}</td><td>{{ row.status }}</td><td class="p-3 text-right">{{ money(row.total) }}</td></tr></tbody>
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
const statuses = ['Draft', 'Confirmed', 'Completed', 'Cancelled']
const search = ref(''), status = ref(''), rows = ref([]), error = ref('')
const customerLabels = ref({})
const dealLabels = ref({})
const loading = ref(false), hasMore = ref(false), canCreate = ref(false)
let requestVersion = 0
function customerRoute(row) {
  return row.company ? { name: 'CompanyDetail', params: { companyId: row.company } } : { name: 'ContactDetail', params: { contactId: row.contact } }
}
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
  if (loading.value && !reset) return
  const version = ++requestVersion
  loading.value = true
  error.value = ''
  if (reset) { rows.value = []; hasMore.value = false; dealLabels.value = {} }
  try {
    const filters = []
    if (search.value.trim()) filters.push(['name', 'like', `%${search.value.trim()}%`])
    if (status.value) filters.push(['status', '=', status.value])
    const data = await call('frappe.client.get_list', { doctype: 'DoubleT Order', fields: ['name', 'contact', 'company', 'deal', 'order_date', 'status', 'total'], filters, order_by: 'modified desc', limit_start: rows.value.length, limit_page_length: 20 })
    if (version !== requestVersion) return
    rows.value.push(...(data || [])); hasMore.value = data?.length === 20
    await Promise.allSettled([loadCustomerLabels(data || []), loadDealLabels(data || [])])
  } catch (e) { if (version === requestVersion) error.value = message(e) } finally { if (version === requestVersion) loading.value = false }
}
onMounted(async () => {
  status.value = router.currentRoute.value.query.status || ''
  load(true)
  try { canCreate.value = Boolean((await call('frappe.client.has_permission', { doctype: 'DoubleT Order', docname: '', perm_type: 'create' }))?.has_permission) } catch { canCreate.value = false }
})
</script>
