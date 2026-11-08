<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header><Button variant="subtle" :label="__('Quotations')" @click="router.push({ name: 'Quotations' })" /><span class="ml-2 text-base font-semibold">{{ isNew ? __('New Quotation') : (doc?.name || __('Quotation')) }}</span></template>
      <template #right-header>
        <Button v-if="!isNew && doc && !editing" :label="__('Export PDF')" :loading="exporting" @click="exportPdf" />
        <Button v-if="!isNew && doc?.deal" :label="__('Back to Deal')" @click="router.push({ name: 'DealDetail', params: { dealId: doc.deal }, hash: '#quotations' })" />
        <Button v-if="!isNew && doc && canWrite && doc.status === 'Draft' && !editing" :label="__('Edit')" @click="editing = true" />
        <Button v-if="editable" variant="solid" :label="isNew ? __('Create') : __('Save')" :loading="saving" :disabled="dealLoading" @click="save" />
        <Button v-if="!isNew && editing" :label="__('Cancel')" @click="loadDocument" />
        <Button v-if="doc && canDelete && doc.status === 'Draft' && !editing" :label="__('Delete')" :loading="saving" @click="remove" />
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5">
      <div v-if="loading" class="p-8 text-center">{{ __('Loading quotation...') }}</div>
      <template v-else>
        <ErrorMessage v-if="error" class="mb-4" :message="error" />
        <Button v-if="conflict" class="mb-4" :label="__('Reload latest quotation')" @click="loadDocument" />
        <div v-if="doc" class="mx-auto max-w-5xl space-y-5">
          <div class="flex flex-wrap items-center gap-3">
            <span class="font-semibold">{{ __('Status') }}: {{ doc.status || 'Draft' }}</span>
            <span v-if="doc.deal">{{ __('Deal') }}: <button v-if="dealLabel" class="font-medium hover:underline" @click="openDeal">{{ dealLabel }}</button><span v-else>—</span></span>
            <template v-if="!isNew && !editing && canWrite">
              <Button v-if="doc.status === 'Draft'" :label="__('Mark as Sent')" :loading="saving" @click="changeStatus('Sent')" />
              <template v-if="doc.status === 'Sent'"><Button :label="__('Mark Accepted')" :loading="saving" @click="changeStatus('Accepted')" /><Button :label="__('Mark Rejected')" :loading="saving" @click="changeStatus('Rejected')" /></template>
            </template>
            <span v-if="doc.status === 'Sent'" class="text-xs text-ink-gray-5">{{ __('Marked as sent manually; no email was sent.') }}</span>
          </div>
          <fieldset :disabled="!editable" class="grid gap-4 sm:grid-cols-2">
            <label class="field">{{ __('Customer Type') }} *<select v-model="doc.customer_type" :disabled="!!doc.deal" @change="customerChanged"><option value="">{{ __('Select') }}</option><option value="PERSONAL">Personal</option><option value="COMPANY">Company</option></select></label>
            <label class="field">{{ __('Deal') }}<select v-model="doc.deal" @change="selectDeal($event.target.value)"><option value="">{{ __('None') }}</option><option v-if="doc.deal && !deals.some(x => x.name === doc.deal)" :value="doc.deal">{{ dealLabel || __('Unavailable') }}</option><option v-for="deal in deals" :key="deal.name" :value="deal.name">{{ deal.deal_title || deal.name }}</option></select></label>
            <label v-if="doc.customer_type === 'COMPANY'" class="field">{{ __('Company') }} *<select v-model="doc.company" :disabled="!!doc.deal"><option value="">{{ __('Select') }}</option><option v-if="doc.company && !companies.some(x => x.name === doc.company)" :value="doc.company">{{ doc.company }} ({{ __('unavailable') }})</option><option v-for="company in companies" :key="company.name" :value="company.name">{{ company.company_name || company.name }}</option></select></label>
            <label class="field">{{ __('Contact') }} {{ doc.customer_type === 'PERSONAL' ? '*' : '' }}<select v-model="doc.contact" :disabled="!!doc.deal"><option value="">{{ __('None') }}</option><option v-if="doc.contact && !contacts.some(x => x.name === doc.contact)" :value="doc.contact">{{ doc.contact }} ({{ __('unavailable') }})</option><option v-for="contact in availableContacts" :key="contact.name" :value="contact.name">{{ [contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.name }}</option></select></label>
            <label class="field">{{ __('Quotation Date') }} *<TextInput v-model="doc.quotation_date" type="date" /></label>
            <label class="field">{{ __('Valid Until') }} *<TextInput v-model="doc.valid_until" type="date" /></label>
            <label class="field sm:col-span-2">{{ __('Notes') }}<textarea v-model="doc.notes" rows="2" /></label>
          </fieldset>
          <div v-if="optionsError" class="text-sm text-red-600">{{ optionsError }}</div>
          <div class="overflow-x-auto rounded border">
            <table class="w-full min-w-[820px] text-left text-sm"><thead><tr><th class="p-3">{{ __('Product') }}</th><th>{{ __('SKU') }}</th><th>{{ __('Unit Price') }}</th><th>{{ __('Quantity') }}</th><th>{{ __('Discount %') }}</th><th>{{ __('Line Total') }}</th><th /></tr></thead>
              <tbody><tr v-for="(item, index) in doc.items" :key="item.name || index" class="border-t">
                <td class="p-3"><select v-if="editable && !item.name" v-model="item.product" @change="selectProduct(item)"><option value="">{{ __('Select product') }}</option><option v-for="product in products" :key="product.name" :value="product.name">{{ product.product_name }} ({{ product.sku }})</option></select><span v-else>{{ item.product_name || item.product || '—' }}</span></td>
                <td>{{ item.sku || '—' }}</td>
                <td><TextInput v-if="editable" v-model="item.unit_price" type="number" min="0" step="1" /><span v-else>{{ money(item.unit_price) }}</span></td>
                <td><TextInput v-if="editable" v-model="item.quantity" type="number" min="0" step="any" /><span v-else>{{ item.quantity }}</span></td>
                <td><TextInput v-if="editable" v-model="item.discount_percent" type="number" min="0" max="100" step="any" /><span v-else>{{ item.discount_percent }}</span></td>
                <td>{{ money(editable ? lineAmounts(item).total : item.line_total) }}</td>
                <td><Button v-if="editable" :label="__('Remove')" @click="doc.items.splice(index, 1)" /></td>
              </tr></tbody>
            </table>
          </div>
          <Button v-if="editable" :label="__('Add item')" iconLeft="plus" @click="doc.items.push({ product: '', product_name: '', sku: '', quantity: 1, unit_price: '', discount_percent: 0 })" />
          <div class="ml-auto max-w-xs space-y-2 text-right text-sm"><p>{{ __('Subtotal') }}: {{ money(editable ? totals.gross : doc.subtotal) }}</p><p>{{ __('Total discount') }}: {{ money(editable ? totals.discount : doc.total_discount) }}</p><p class="font-semibold">{{ __('Grand total') }}: {{ money(editable ? totals.total : doc.grand_total) }}</p><p v-if="editable" class="text-xs text-ink-gray-5">{{ __('Preview; final amounts are calculated by the server.') }}</p></div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, TextInput, call } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { lineAmounts, message, money } from '@/utils/quotation'

const route = useRoute(), router = useRouter()
const isNew = computed(() => route.name === 'QuotationCreate')
const doc = ref(null), loading = ref(true), saving = ref(false), editing = ref(false)
const exporting = ref(false)
const canWrite = ref(false), canDelete = ref(false), error = ref(''), optionsError = ref(''), conflict = ref(false)
const contacts = ref([]), companies = ref([]), deals = ref([]), products = ref([])
const dealLoading = ref(false)
const dealLabel = ref('')
let dealRequestId = 0
const editable = computed(() => (isNew.value && canWrite.value) || (!isNew.value && editing.value && canWrite.value && doc.value?.status === 'Draft'))
const availableContacts = computed(() => doc.value?.customer_type === 'COMPANY' ? contacts.value.filter(c => c.company === doc.value.company) : contacts.value)
const totals = computed(() => (doc.value?.items || []).reduce((sum, item) => { const a = lineAmounts(item); sum.gross += a.gross; sum.discount += a.discount; sum.total += a.total; return sum }, { gross: 0, discount: 0, total: 0 }))
const list = (doctype, fields, filters = {}) => call('frappe.client.get_list', { doctype, fields, filters, limit_page_length: 500 })
async function loadOptions() {
  const results = await Promise.allSettled([
    list('DoubleT Contact', ['name', 'first_name', 'last_name', 'company']),
    list('DoubleT Company', ['name', 'company_name']),
    list('DoubleT Deal', ['name', 'deal_title']),
    list('DoubleT Product', ['name', 'product_name', 'sku', 'price'], { is_active: 1 }),
  ])
  ;[contacts, companies, deals, products].forEach((target, i) => { if (results[i].status === 'fulfilled') target.value = results[i].value || [] })
  if (results.some(r => r.status === 'rejected')) optionsError.value = __('Some linked records could not be loaded. Check your access and retry.')
}
async function loadDocument() {
  loading.value = true; error.value = ''; conflict.value = false
  try {
    if (isNew.value) {
      const permission = await call('frappe.client.has_permission', { doctype: 'DoubleT Quotation', docname: '', perm_type: 'create' })
      canWrite.value = Boolean(permission?.has_permission)
      if (!canWrite.value) throw new Error(__('You do not have permission to create quotations.'))
      doc.value = { doctype: 'DoubleT Quotation', status: 'Draft', customer_type: '', contact: '', company: '', deal: '', quotation_date: '', valid_until: '', notes: '', items: [] }
    } else {
      const [data, permissions] = await Promise.all([
        call('frappe.client.get', { doctype: 'DoubleT Quotation', name: route.params.quotationId }),
        call('frappe.client.get_doc_permissions', { doctype: 'DoubleT Quotation', docname: route.params.quotationId }),
      ])
      doc.value = data; canWrite.value = Boolean(permissions?.permissions?.write); canDelete.value = Boolean(permissions?.permissions?.delete)
      await loadDealLabel(data.deal)
    }
    editing.value = false
  } catch (e) { error.value = message(e); doc.value = null } finally { loading.value = false }
}
function customerChanged() { if (doc.value.customer_type === 'PERSONAL') doc.value.company = ''; doc.value.deal = ''; dealLabel.value = '' }
function dealName(value) { return typeof value === 'string' ? value.trim() : '' }
async function loadDealLabel(value) {
  const name = dealName(value)
  dealLabel.value = ''
  if (!name) return
  try {
    const data = await list('DoubleT Deal', ['name', 'deal_title'], { name })
    const deal = data?.[0]
    if (deal?.name === name) dealLabel.value = deal.deal_title || __('Unnamed Deal')
  } catch { /* An unread Deal stays neutral in the UI. */ }
}
function openDeal() { if (doc.value?.deal && dealLabel.value) router.push({ name: 'DealDetail', params: { dealId: doc.value.deal } }) }
function isPermissionError(e) { return e?.httpStatusCode === 403 || e?.status === 403 || e?.exc_type === 'PermissionError' || /\b(permission|not permitted|not allowed)\b/i.test(message(e)) }
async function selectDeal(value = doc.value?.deal) {
  const requestId = ++dealRequestId
  const name = dealName(value)
  if (!name) {
    doc.value.deal = ''
    dealLoading.value = false
    dealLabel.value = ''
    error.value = ''
    return
  }

  doc.value.deal = name
  dealLoading.value = true
  try {
    const deal = await call('frappe.client.get', { doctype: 'DoubleT Deal', name })
    if (requestId !== dealRequestId) return
    if (!deal?.name) throw new Error(__('The selected Deal could not be found.'))
    if (!['PERSONAL', 'COMPANY'].includes(deal.deal_type) || (deal.deal_type === 'COMPANY' && !deal.company) || (deal.deal_type === 'PERSONAL' && !deal.contact)) {
      throw new Error(__('The Deal customer information is incomplete or unavailable. Check the Deal customer or ask an administrator to check your access.'))
    }
    Object.assign(doc.value, { customer_type: deal.deal_type, contact: deal.contact || '', company: deal.company || '' })
    await loadDealLabel(name)
    error.value = ''
  } catch (e) {
    if (requestId !== dealRequestId) return
    error.value = isPermissionError(e)
      ? __('You do not have permission to read the selected Deal.')
      : message(e)
    doc.value.deal = ''
    dealLabel.value = ''
  } finally { if (requestId === dealRequestId) dealLoading.value = false }
}
function selectProduct(item) {
  const p = products.value.find(p => p.name === item.product)
  if (p) Object.assign(item, { product_name: p.product_name, sku: p.sku, unit_price: p.price })
}
function validate() {
  const d = doc.value
  if (!['PERSONAL', 'COMPANY'].includes(d.customer_type) || (d.customer_type === 'PERSONAL' && (!d.contact || d.company)) || (d.customer_type === 'COMPANY' && !d.company)) return __('Select a valid customer.')
  if (d.customer_type === 'COMPANY' && d.contact && contacts.value.some(c => c.name === d.contact && c.company !== d.company)) return __('Contact must belong to the selected Company.')
  if (!d.quotation_date || !d.valid_until || d.valid_until < d.quotation_date) return __('Enter valid quotation and expiry dates.')
  if (!d.items.length) return __('Add at least one item.')
  const decimal = value => /^\d+(\.\d+)?$/.test(String(value ?? '')) && Number.isFinite(Number(value))
  if (d.items.some(i => !i.product || !decimal(i.quantity) || Number(i.quantity) <= 0 || !decimal(i.unit_price) || !decimal(i.discount_percent) || Number(i.discount_percent) > 100)) return __('Check product, quantity, price and discount for each item.')
  return ''
}
function setError(e) {
  const text = message(e)
  if (e?.exc_type === 'TimestampMismatchError' || /modified after/i.test(text)) { conflict.value = true; error.value = __('This quotation was changed by another user. Reload the latest version before saving.') }
  else error.value = text
}
async function exportPdf() {
  if (exporting.value || !doc.value?.name) return
  exporting.value = true; error.value = ''
  try {
    const query = new URLSearchParams({ name: doc.value.name })
    const response = await fetch(`/api/method/doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_pdf.download_quotation_pdf?${query}`, { credentials: 'same-origin', headers: { Accept: 'application/pdf' } })
    if (!response.ok) throw new Error(response.status === 403 ? __('You do not have permission to export this quotation.') : __('Unable to export this quotation. Please try again.'))
    if (!response.headers.get('content-type')?.includes('application/pdf')) throw new Error(__('Unable to export this quotation. Please sign in and try again.'))
    const url = URL.createObjectURL(await response.blob())
    const link = document.createElement('a'); link.href = url; link.download = `${doc.value.name.replace(/[\\/]/g, '-')}.pdf`; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (e) { error.value = message(e) } finally { exporting.value = false }
}
async function save() {
  if (saving.value || dealLoading.value || !editable.value) return
  error.value = validate(); if (error.value) return
  saving.value = true
  try {
    const saved = await call(isNew.value ? 'frappe.client.insert' : 'frappe.client.save', { doc: doc.value })
    if (isNew.value) await router.replace({ name: 'QuotationDetail', params: { quotationId: saved.name } })
    await loadDocument()
  } catch (e) { setError(e) } finally { saving.value = false }
}
async function changeStatus(status) {
  if (saving.value || !canWrite.value || editing.value) return
  if (status === 'Sent' && !window.confirm(__('Mark as sent? This does not send an email.'))) return
  saving.value = true
  try { await call('frappe.client.save', { doc: { ...doc.value, status } }); await loadDocument() } catch (e) { setError(e) } finally { saving.value = false }
}
async function remove() {
  if (saving.value || !canDelete.value || doc.value.status !== 'Draft' || !window.confirm(__('Delete this draft quotation?'))) return
  saving.value = true
  try { await call('frappe.client.delete', { doctype: 'DoubleT Quotation', name: doc.value.name }); await router.push({ name: 'Quotations' }) } catch (e) { setError(e) } finally { saving.value = false }
}
onMounted(async () => {
  loadOptions()
  await loadDocument()
  const queryDeal = Array.isArray(route.query.deal) ? '' : dealName(route.query.deal)
  if (isNew.value && queryDeal && doc.value) await selectDeal(queryDeal)
})
</script>

<style scoped>
.field { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.875rem; }
select, textarea { width: 100%; border: 1px solid #d1d5db; border-radius: 0.25rem; padding: 0.4rem; background: white; }
fieldset:disabled { opacity: 0.8; }
</style>
