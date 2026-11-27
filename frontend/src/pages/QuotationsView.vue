<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header><ViewBreadcrumbs routeName="Quotations" /></template>
      <template #right-header>
        <div class="flex flex-wrap items-center gap-2">
          <Button v-if="canManageApproval" variant="subtle" :label="__('Discount Approval')" iconLeft="sliders" @click="showApprovalSettings = true" />
          <Button variant="subtle" :label="__('Templates')" iconLeft="layers" @click="router.push({ name: 'QuotationTemplates' })" />
          <Button v-if="canCreate" variant="solid" :label="__('Create Quotation')" iconLeft="plus" @click="router.push({ name: 'QuotationCreate' })" />
        </div>
      </template>
    </LayoutHeader>
    <div class="flex flex-wrap items-center gap-2 border-b px-5 py-3">
      <TextInput v-model="search" type="search" :placeholder="__('Search quotation, customer or deal')" @keyup.enter="load(true)" />
      <select v-model="status" class="rounded border px-2 py-1 text-sm" @change="load(true)">
        <option value="">{{ __('All statuses') }}</option><option v-for="s in statuses" :key="s">{{ s }}</option>
      </select>
      <select v-model="expiryFilter" class="rounded border px-2 py-1 text-sm" @change="load(true)">
        <option value="">{{ __('All validity') }}</option>
        <option value="expired">{{ __('Expired') }}</option>
        <option value="not_expired">{{ __('Not Expired') }}</option>
      </select>
      <select v-model="approvalFilter" class="rounded border px-2 py-1 text-sm" @change="load(true)">
        <option value="">{{ __('All approvals') }}</option>
        <option v-for="a in approvalStatuses" :key="a" :value="a">{{ __(a) }}</option>
      </select>
      <Button :label="__('Search')" @click="load(true)" /><Button :label="__('Refresh')" :loading="loading" @click="load(true)" />
    </div>
    <div class="flex-1 overflow-auto p-5">
      <ErrorMessage v-if="error" :message="error" />
      <div v-if="loading && !rows.length" class="p-8 text-center">{{ __('Loading quotations...') }}</div>
      <div v-else-if="!rows.length && !error" class="p-8 text-center text-ink-gray-5">{{ __('No quotations found.') }}</div>
      <div v-else-if="rows.length" class="overflow-x-auto rounded border">
        <table class="w-full min-w-[860px] text-left text-sm">
          <thead>
            <tr>
              <th class="p-3">{{ __('Quotation') }}</th>
              <th>{{ __('Customer') }}</th>
              <th>{{ __('Deal') }}</th>
              <th>{{ __('Date') }}</th>
              <th>{{ __('Valid Until') }}</th>
              <th>{{ __('Status') }}</th>
              <th>{{ __('Approval') }}</th>
              <th class="p-3 text-right">{{ __('Grand Total') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in rows" :key="row.name" class="cursor-pointer border-t hover:bg-surface-gray-1" @click="router.push({ name: 'QuotationDetail', params: { quotationId: row.name } })">
              <td class="p-3"><button class="hover:underline">{{ row.name }}</button></td>
              <td>{{ customerLabels[row.company || row.contact] || row.company || row.contact || '—' }}</td>
              <td><button v-if="dealLabels[row.deal]" class="hover:underline" @click.stop="openDeal(row.deal)">{{ dealLabels[row.deal] }}</button><span v-else>—</span></td>
              <td>{{ row.quotation_date }}</td>
              <td>{{ row.valid_until || '—' }}</td>
              <td>
                <span class="rounded-full px-2 py-0.5 text-xs font-medium" :class="statusBadgeClass(row.status)">{{ __(row.status) }}</span>
                <span v-if="isQuotationExpired(row, siteToday)" class="ml-2 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-800">{{ __('Expired') }}</span>
              </td>
              <td>
                <span
                  v-if="row.approval_status"
                  class="rounded-full px-2 py-0.5 text-xs font-medium"
                  :class="approvalBadgeClass(row.approval_status)"
                >
                  {{ __(row.approval_status) }}
                </span>
                <span v-else class="rounded-full bg-surface-gray-2 px-2 py-0.5 text-xs text-ink-gray-6">{{ __('Legacy / Unknown') }}</span>
              </td>
              <td class="p-3 text-right">{{ money(row.grand_total) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    <div v-if="hasMore" class="border-t p-3 text-center"><Button :label="__('Load More')" :loading="loading" @click="load(false)" /></div>
    <DiscountApprovalSettingsModal v-model="showApprovalSettings" />
  </div>
</template>
<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, ErrorMessage, TextInput, call } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import DiscountApprovalSettingsModal from '@/components/Modals/DiscountApprovalSettingsModal.vue'
import { approvalBadgeClass, isQuotationExpired, message, money } from '@/utils/quotation'

const router = useRouter()
const statuses = ['Draft', 'Sent', 'Accepted', 'Rejected']
const approvalStatuses = ['Required', 'Pending', 'Approved', 'Rejected', 'Not Required']
const search = ref(''), status = ref(''), expiryFilter = ref(''), approvalFilter = ref(''), rows = ref([]), error = ref('')
const customerLabels = ref({})
const dealLabels = ref({})
const loading = ref(false), hasMore = ref(false), canCreate = ref(false), canManageApproval = ref(false)
const siteToday = ref('')
const showApprovalSettings = ref(false)
const statusBadgeClass = value => ({ Draft: 'bg-gray-100 text-gray-700', Sent: 'bg-blue-100 text-blue-700', Accepted: 'bg-green-100 text-green-700', Rejected: 'bg-red-100 text-red-700' }[value] || 'bg-surface-gray-2')

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
async function ensureSiteToday() {
  if (siteToday.value) return siteToday.value
  try {
    const res = await call('doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation.get_site_today')
    if (res?.today) siteToday.value = res.today
  } catch { /* fallback handled by helper */ }
  return siteToday.value || new Date().toISOString().slice(0, 10)
}
async function load(reset) {
  if (loading.value) return
  loading.value = true
  error.value = ''
  if (reset) { rows.value = []; hasMore.value = false; dealLabels.value = {} }
  try {
    await ensureSiteToday()
    const data = await call('doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation.list_quotations', {
      search: search.value.trim(), status: status.value, expiry: expiryFilter.value,
      approval_status: approvalFilter.value, limit_start: rows.value.length, limit_page_length: 20,
    })
    rows.value.push(...(data || [])); hasMore.value = data?.length === 20
    await Promise.allSettled([loadCustomerLabels(data || []), loadDealLabels(data || [])])
  } catch (e) { error.value = message(e) } finally { loading.value = false }
}
onMounted(async () => {
  status.value = router.currentRoute.value.query.status || ''
  load(true)
  const [createRes, approvalRes] = await Promise.allSettled([
    call('frappe.client.has_permission', { doctype: 'DoubleT Quotation', docname: '', perm_type: 'create' }),
    call('doublet_crm.doublet_crm.doctype.doublet_quotation.doublet_quotation.get_discount_approval_settings'),
  ])
  canCreate.value = createRes.status === 'fulfilled' && Boolean(createRes.value?.has_permission)
  canManageApproval.value = approvalRes.status === 'fulfilled' && Boolean(approvalRes.value?.can_manage)
})
</script>
