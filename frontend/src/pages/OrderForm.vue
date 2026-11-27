<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <Button variant="subtle" :label="__('Orders')" @click="router.push({ name: 'Orders' })" />
        <span class="ml-2 text-base font-semibold">{{ isNew ? __('New Order') : (doc?.name || __('Order')) }}</span>
      </template>
      <template #right-header>
        <Button v-if="doc && !isNew && !editing && canWrite && doc.status === 'Draft'" :label="__('Edit')" :disabled="saving" @click="editing = true" />
        <Button v-if="doc && !isNew && !editing && canDelete && doc.status === 'Draft'" :label="__('Delete')" :loading="saving" @click="remove" />
        <Button v-if="editable" variant="solid" :label="isNew ? __('Create') : __('Save')" :loading="saving" :disabled="dealLoading || pricingPending" @click="save" />
        <Button v-if="editing" :label="__('Cancel editing')" :disabled="saving" @click="loadDocument" />
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5">
      <div v-if="loading" class="p-8 text-center">{{ __('Loading order...') }}</div>
      <template v-else>
        <ErrorMessage v-if="error" class="mb-4" :message="error" />
        <Button v-if="conflict" class="mb-4" :label="__('Reload latest Order')" @click="loadDocument" />
        <div v-if="doc" class="mx-auto max-w-5xl space-y-5">
          <div class="flex flex-wrap items-center gap-3">
            <span class="rounded bg-surface-gray-2 px-3 py-1 text-sm">{{ doc.status }}</span>
            <span class="text-sm text-ink-gray-6">{{ doc.currency }}</span>
            <Button v-for="action in statusActions" :key="action.status" :label="__(action.label)" :loading="saving" @click="changeStatus(action.status)" />
          </div>
          <div v-if="doc.quotation" class="text-sm">
            {{ __('Source Quotation') }}:
            <RouterLink class="text-ink-blue-2 hover:underline" :to="{ name: 'QuotationDetail', params: { quotationId: doc.quotation } }">{{ doc.quotation }}</RouterLink>
          </div>
          <div v-if="!editable" class="grid gap-4 rounded border p-4 text-sm sm:grid-cols-2">
            <div>{{ __('Customer Type') }}: {{ doc.customer_type }}</div>
            <div>{{ __('Order Date') }}: {{ doc.order_date }}</div>
            <div v-if="doc.company">{{ __('Company') }}: <RouterLink class="hover:underline" :to="{ name: 'CompanyDetail', params: { companyId: doc.company } }">{{ companyLabel }}</RouterLink></div>
            <div v-if="doc.contact">{{ __('Contact') }}: <RouterLink class="hover:underline" :to="{ name: 'ContactDetail', params: { contactId: doc.contact } }">{{ contactLabel }}</RouterLink></div>
            <div v-if="doc.deal">{{ __('Deal') }}: <RouterLink class="hover:underline" :to="{ name: 'DealDetail', params: { dealId: doc.deal } }">{{ dealLabel || doc.deal }}</RouterLink></div>
          </div>
          <fieldset v-else :disabled="saving" class="grid gap-4 sm:grid-cols-2">
            <label class="field">{{ __('Customer Type') }} *
              <select v-model="doc.customer_type" :disabled="customerLocked" @change="customerTypeChanged"><option value="">{{ __('Select') }}</option><option value="PERSONAL">Personal</option><option value="COMPANY">Company</option></select>
            </label>
            <label class="field">{{ __('Order Date') }} *<TextInput v-model="doc.order_date" type="date" /></label>
            <label v-if="doc.customer_type === 'COMPANY'" class="field">{{ __('Company') }} *
              <select v-model="doc.company" :disabled="customerLocked" @change="companyChanged"><option value="">{{ __('Select') }}</option><option v-if="doc.company && !companies.some(c => c.name === doc.company)" :value="doc.company">{{ doc.company }}</option><option v-for="company in companies" :key="company.name" :value="company.name">{{ company.company_name || company.name }}</option></select>
            </label>
            <label class="field">{{ __('Contact') }} {{ doc.customer_type === 'PERSONAL' ? '*' : '' }}
              <select v-model="doc.contact" :disabled="customerLocked" @change="contactChanged"><option value="">{{ __('None') }}</option><option v-if="doc.contact && !availableContacts.some(c => c.name === doc.contact)" :value="doc.contact">{{ doc.contact }}</option><option v-for="contact in availableContacts" :key="contact.name" :value="contact.name">{{ contactName(contact) }}</option></select>
            </label>
            <label class="field">{{ __('Deal') }}
              <select v-model="doc.deal" :disabled="!!doc.quotation || dealLoading" @change="selectDeal"><option value="">{{ __('None') }}</option><option v-if="doc.deal && !matchingDeals.some(d => d.name === doc.deal)" :value="doc.deal">{{ dealLabel || doc.deal }}</option><option v-for="deal in matchingDeals" :key="deal.name" :value="deal.name">{{ deal.deal_title || deal.name }}</option></select>
              <span v-if="dealLoading" class="text-xs text-ink-gray-5">{{ __('Loading Deal customer...') }}</span>
              <span v-if="dealError" class="text-xs text-red-600">{{ dealError }}</span>
            </label>
          </fieldset>
          <ErrorMessage v-if="optionsError" :message="optionsError" />
          <div v-if="editable" class="flex flex-wrap items-end gap-2 rounded border p-3">
            <label class="min-w-64 flex-1 text-sm">{{ __('Search sellable products') }}<TextInput v-model="productSearch" type="search" :placeholder="__('Search name or SKU...')" /></label>
            <Button v-if="productHasNextPage" variant="subtle" :label="__('Load more products')" :loading="productsLoading" @click="loadProducts({ append: true })" />
            <span class="text-xs text-ink-gray-5">{{ __('Only active Standard Products and Variants are available.') }}</span>
          </div>
          <ErrorMessage v-if="editable && productPickerError" :message="productPickerError" />
          <div class="overflow-x-auto rounded border">
            <table class="w-full min-w-[760px] table-fixed text-left text-sm">
              <colgroup><col class="w-[26%]" /><col class="w-[15%]" /><col class="w-[10%]" /><col class="w-[16%]" /><col class="w-[14%]" /><col class="w-[14%]" /><col class="w-[5%]" /></colgroup>
              <thead class="bg-surface-gray-1"><tr><th class="p-2.5">{{ __('Product') }}</th><th class="p-2.5">{{ __('Unit Price (USD)') }}</th><th class="p-2.5">{{ __('Quantity') }}</th><th class="p-2.5">{{ __('Discount Type') }}</th><th class="p-2.5">{{ __('Discount') }}</th><th class="p-2.5 text-right">{{ __('Line Total (USD)') }}</th><th /></tr></thead>
              <tbody>
                <tr v-for="(item, index) in doc.items" :key="item.name || index" class="border-t align-top">
                  <td class="min-w-0 p-2.5">
                    <select v-if="editable && !item.name" v-model="item.product" :disabled="saving" @change="selectProduct(item)"><option value="">{{ __('Select product') }}</option><option v-if="item.product && !products.some(p => p.name === item.product)" :value="item.product">{{ item.product_name || item.product }}</option><option v-for="product in products" :key="product.name" :value="product.name">{{ productPickerLabel(product) }}</option></select>
                    <span v-else class="break-words">{{ item.product_name || item.product }}</span>
                    <div v-if="item.sku" class="mt-1 text-xs text-ink-gray-5">{{ item.sku }}</div>
                  </td>
                  <td class="min-w-0 p-2.5"><TextInput v-if="editable" v-model="item.unit_price" type="number" min="0" step="0.01" :disabled="saving" @update:modelValue="markManualPrice(item)" /><span v-else>{{ money(item.unit_price) }}</span><div v-if="itemPricing(item).loading" class="mt-1 text-xs">{{ __('Loading price...') }}</div><div v-if="itemPricing(item).error" class="mt-1 break-words text-xs text-red-600">{{ itemPricing(item).error }}</div></td>
                  <td class="min-w-0 p-2.5"><TextInput v-if="editable" v-model="item.quantity" type="number" min="0" step="any" :disabled="saving" /><span v-else>{{ item.quantity }}</span></td>
                  <td class="min-w-0 p-2.5"><select v-if="editable" v-model="item.discount_type" :disabled="saving" @change="discountTypeChanged(item)"><option value="Percentage">{{ __('Percentage') }}</option><option value="Amount">{{ __('Amount') }}</option></select><span v-else>{{ item.discount_type === 'Amount' ? __('Amount') : __('Percentage') }}</span></td>
                  <td class="min-w-0 p-2.5"><TextInput v-if="editable && item.discount_type === 'Amount'" v-model="item.discount_amount" type="number" min="0" step="0.01" :disabled="saving" /><TextInput v-else-if="editable" v-model="item.discount_percent" type="number" min="0" max="100" step="any" :disabled="saving" /><span v-else>{{ item.discount_type === 'Amount' ? money(item.discount_amount) : `${item.discount_percent || 0}%` }}</span></td>
                  <td class="p-2.5 text-right">{{ money(editable ? lineAmounts(item).total : item.subtotal) }}</td>
                  <td class="p-2.5"><Button v-if="editable" icon="trash-2" variant="ghost" :tooltip="__('Remove')" :disabled="saving" @click="doc.items.splice(index, 1)" /></td>
                </tr>
                <tr v-if="!doc.items.length"><td colspan="7" class="p-8 text-center text-ink-gray-5">{{ __('No products added yet.') }}</td></tr>
              </tbody>
            </table>
          </div>
          <Button v-if="editable" :label="__('Add item')" iconLeft="plus" :disabled="saving" @click="addItem" />
          <div class="ml-auto max-w-xs space-y-2 text-right text-sm">
            <p>{{ __('Subtotal before Discounts') }}: {{ money(editable ? totals.gross : doc.subtotal) }}</p>
            <p>{{ __('Total Discount') }}: {{ money(editable ? totals.discount : doc.total_discount) }}</p>
            <p class="font-semibold">{{ __('Total') }}: {{ money(editable ? totals.total : doc.total) }}</p>
            <p v-if="editable" class="text-xs text-ink-gray-5">{{ __('Preview; final amounts are calculated by the server.') }}</p>
          </div>
          <label class="field">{{ __('Notes') }}<textarea v-if="editable" v-model="doc.notes" rows="3" :disabled="saving" /><span v-else class="whitespace-pre-wrap">{{ doc.notes || '—' }}</span></label>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, TextInput, call } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { useSellableProducts } from '@/composables/useSellableProducts'
import { contactsForCustomer, dealsForCustomer, lineAmounts, message, money } from '@/utils/quotation'

const route = useRoute(), router = useRouter()
const isNew = computed(() => route.name === 'OrderCreate')
const doc = ref(null), loading = ref(true), saving = ref(false), editing = ref(false)
const canWrite = ref(false), canDelete = ref(false), error = ref(''), conflict = ref(false)
const contacts = ref([]), companies = ref([]), deals = ref([]), optionsError = ref('')
const dealLoading = ref(false), dealError = ref(''), dealLabel = ref('')
const { products, productSearch, productsLoading, productHasNextPage, productPickerError, loadProducts, productPickerLabel } = useSellableProducts()
const pricingStates = new WeakMap()
let loadVersion = 0, dealVersion = 0
const editable = computed(() => canWrite.value && !!doc.value && (isNew.value || (editing.value && doc.value.status === 'Draft')))
const customerLocked = computed(() => !!doc.value?.quotation)
const availableContacts = computed(() => contactsForCustomer(contacts.value, doc.value))
const matchingDeals = computed(() => dealsForCustomer(deals.value, doc.value))
const contactName = contact => [contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.name
const companyLabel = computed(() => companies.value.find(c => c.name === doc.value?.company)?.company_name || doc.value?.company)
const contactLabel = computed(() => { const contact = contacts.value.find(c => c.name === doc.value?.contact); return contact ? contactName(contact) : doc.value?.contact })
const totals = computed(() => (doc.value?.items || []).reduce((sum, item) => {
  const amount = lineAmounts(item)
  sum.gross += amount.gross; sum.discount += amount.discount; sum.total += amount.total
  return sum
}, { gross: 0, discount: 0, total: 0 }))
const pricingPending = computed(() => (doc.value?.items || []).some(item => itemPricing(item).loading))
const transitions = {
  Draft: [{ status: 'Confirmed', label: 'Confirm Order' }, { status: 'Cancelled', label: 'Cancel Order' }],
  Confirmed: [{ status: 'Completed', label: 'Complete Order' }, { status: 'Cancelled', label: 'Cancel Order' }],
}
const statusActions = computed(() => !isNew.value && canWrite.value && !editing.value ? transitions[doc.value?.status] || [] : [])

async function loadOptions() {
  const results = await Promise.allSettled([
    ['DoubleT Contact', ['name', 'first_name', 'last_name', 'company']],
    ['DoubleT Company', ['name', 'company_name']],
    ['DoubleT Deal', ['name', 'deal_title', 'deal_type', 'contact', 'company']],
  ].map(([doctype, fields]) => call('frappe.client.get_list', { doctype, fields, limit_page_length: 500 })))
  ;[contacts, companies, deals].forEach((target, index) => { if (results[index].status === 'fulfilled') target.value = results[index].value || [] })
  optionsError.value = results.some(result => result.status === 'rejected') ? __('Some linked records could not be loaded. Check your access and refresh.') : ''
}
async function loadDocument() {
  const version = ++loadVersion
  dealVersion += 1
  loading.value = true; doc.value = null; error.value = ''; conflict.value = false
  canWrite.value = false; editing.value = false; dealError.value = ''; dealLoading.value = false; dealLabel.value = ''
  try {
    if (isNew.value) {
      const permission = await call('frappe.client.has_permission', { doctype: 'DoubleT Order', docname: '', perm_type: 'create' })
      if (version !== loadVersion) return
      if (!permission?.has_permission) throw new Error(__('You do not have permission to create Orders.'))
      canWrite.value = true
      const today = new Date(Date.now() - new Date().getTimezoneOffset() * 60000).toISOString().slice(0, 10)
      doc.value = { doctype: 'DoubleT Order', status: 'Draft', order_date: today, currency: 'USD', customer_type: '', contact: '', company: '', deal: '', quotation: '', notes: '', items: [] }
    } else {
      const [data, access] = await Promise.all([
        call('frappe.client.get', { doctype: 'DoubleT Order', name: route.params.orderId }),
        call('frappe.client.get_doc_permissions', { doctype: 'DoubleT Order', docname: route.params.orderId }),
      ])
      if (version !== loadVersion) return
      doc.value = data
      canWrite.value = Boolean(access?.permissions?.write)
      canDelete.value = Boolean(access?.permissions?.delete)
      // Saved rows, including converted Quotation rows, keep their stored prices.
      data.items.forEach(item => itemPricing(item))
    }
  } catch (e) { if (version === loadVersion) { doc.value = null; error.value = message(e) } }
  finally { if (version === loadVersion) loading.value = false }
}
function clearIneligibleDeal() {
  if (doc.value?.deal && !matchingDeals.value.some(d => d.name === doc.value.deal)) {
    doc.value.deal = ''
    dealLabel.value = ''
  }
}
function customerTypeChanged() {
  doc.value.contact = ''; doc.value.company = ''
  clearIneligibleDeal()
  pricingContextChanged()
}
function companyChanged() {
  if (!availableContacts.value.some(c => c.name === doc.value.contact)) doc.value.contact = ''
  clearIneligibleDeal()
  pricingContextChanged()
}
function contactChanged() {
  clearIneligibleDeal()
  pricingContextChanged()
}
async function selectDeal() {
  const name = doc.value.deal
  dealError.value = ''; dealLabel.value = ''
  if (!name) return
  const matched = matchingDeals.value.find(d => d.name === name)
  if (matched) dealLabel.value = matched.deal_title || matched.name
}
async function remove() {
  if (saving.value || !canDelete.value || doc.value?.status !== 'Draft' || !window.confirm(__('Delete this draft order?'))) return
  saving.value = true
  try {
    await call('frappe.client.delete', { doctype: 'DoubleT Order', name: doc.value.name })
    await router.push({ name: 'Orders' })
  } catch (e) { setError(e) } finally { saving.value = false }
}
function itemPricing(item) {
  if (!pricingStates.has(item)) pricingStates.set(item, reactive({ loading: false, error: '', manual: Boolean(item.name), requestId: 0 }))
  return pricingStates.get(item)
}
function addItem() {
  doc.value.items.push({ product: '', product_name: '', sku: '', quantity: 1, unit_price: '', discount_type: 'Percentage', discount_percent: 0, discount_amount: 0 })
}
function markManualPrice(item) {
  const state = itemPricing(item)
  state.requestId += 1; state.manual = true; state.loading = false; state.error = ''
}
async function selectProduct(item) {
  const state = itemPricing(item)
  state.requestId += 1; state.manual = false; state.loading = false; state.error = ''
  item.unit_price = ''
  const product = products.value.find(product => product.name === item.product)
  item.product_name = product?.product_name || ''; item.sku = product?.sku || ''
  if (product) await resolveItemPrice(item)
}
async function resolveItemPrice(item) {
  const state = itemPricing(item)
  if (!item.product || item.name || state.manual) return
  const requestId = ++state.requestId
  const product = item.product
  state.loading = true; state.error = ''; item.unit_price = ''
  try {
    const result = await call('doublet_crm.pricing.get_product_price', { product, customer_type: doc.value.customer_type, contact: doc.value.contact || null, company: doc.value.company || null })
    if (requestId !== state.requestId || product !== item.product || state.manual) return
    if (result?.price === undefined || result?.price === null || result?.price === '') throw new Error(__('The pricing service did not return a price.'))
    item.unit_price = result.price
  } catch (e) { if (requestId === state.requestId) state.error = message(e) }
  finally { if (requestId === state.requestId) state.loading = false }
}
function pricingContextChanged() {
  for (const item of doc.value.items) if (!item.name && !itemPricing(item).manual) void resolveItemPrice(item)
}
function discountTypeChanged(item) {
  if (item.discount_type === 'Amount') item.discount_percent = 0
  else item.discount_amount = 0
}
function validate() {
  const data = doc.value
  if (dealError.value) return dealError.value
  if (!['PERSONAL', 'COMPANY'].includes(data.customer_type) || (data.customer_type === 'PERSONAL' && (!data.contact || data.company)) || (data.customer_type === 'COMPANY' && !data.company)) return __('Select a valid customer.')
  if (!data.order_date) return __('Order Date is required.')
  if (!data.items.length) return __('Add at least one item.')
  const decimal = value => /^\d+(\.\d+)?$/.test(String(value ?? '')) && Number.isFinite(Number(value))
  if (data.items.some(item => {
    if (!item.product || !decimal(item.quantity) || Number(item.quantity) <= 0 || !decimal(item.unit_price)) return true
    if (item.discount_type === 'Amount') return !decimal(item.discount_amount ?? 0) || Number(item.discount_amount) > lineAmounts({ ...item, discount_amount: 0 }).gross
    return !decimal(item.discount_percent ?? 0) || Number(item.discount_percent) > 100
  })) return __('Check product, quantity, price and discount for each item.')
  return ''
}
function setError(e) {
  if (e?.exc_type === 'TimestampMismatchError' || /modified after/i.test(message(e))) {
    conflict.value = true
    error.value = __('This Order was changed by another user. Reload the latest version before saving.')
  } else error.value = message(e)
}
async function save() {
  if (saving.value || dealLoading.value || pricingPending.value || !editable.value) return
  error.value = validate()
  if (error.value) return
  saving.value = true
  try {
    const saved = await call(isNew.value ? 'frappe.client.insert' : 'frappe.client.save', { doc: doc.value })
    if (isNew.value) await router.replace({ name: 'OrderDetail', params: { orderId: saved.name } })
    else await loadDocument()
  } catch (e) { setError(e) } finally { saving.value = false }
}
async function changeStatus(status) {
  if (saving.value || !statusActions.value.some(action => action.status === status)) return
  if (status === 'Cancelled' && !window.confirm(__('Cancel this Order?'))) return
  saving.value = true; error.value = ''
  try {
    await call('frappe.client.save', { doc: { ...doc.value, status } })
    await loadDocument()
  } catch (e) { setError(e) } finally { saving.value = false }
}
watch(() => [route.name, route.params.orderId], loadDocument, { immediate: true })
onMounted(() => { loadOptions(); loadProducts() })
</script>

<style scoped>
.field { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.875rem; }
select, textarea { width: 100%; min-width: 0; border: 1px solid #d1d5db; border-radius: 0.25rem; padding: 0.4rem; background: white; }
fieldset:disabled { opacity: 0.8; }
</style>
