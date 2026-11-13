<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header><Button variant="subtle" :label="__('Quotations')" @click="router.push({ name: 'Quotations' })" /><span class="ml-2 text-base font-semibold">{{ isNew ? __('New Quotation') : (doc?.name || __('Quotation')) }}</span></template>
      <template #right-header>
        <Button v-if="!isNew && doc && !editing" :label="__('Export PDF')" :loading="exporting" @click="exportPdf" />
        <Button v-if="!isNew && doc?.deal" :label="__('Back to Deal')" @click="router.push({ name: 'DealDetail', params: { dealId: doc.deal }, hash: '#quotations' })" />
        <Button v-if="!isNew && doc && canWrite && doc.status === 'Draft' && !editing" :label="__('Edit')" @click="editing = true" />
        <Button v-if="editable" variant="solid" :label="isNew ? __('Create') : __('Save')" :loading="saving" :disabled="dealLoading || pricingPending" @click="save" />
        <Button v-if="!isNew && editing" :label="__('Cancel')" @click="loadDocument" />
        <Button v-if="doc && canDelete && doc.status === 'Draft' && !editing" :label="__('Delete')" :loading="saving" @click="remove" />
      </template>
    </LayoutHeader>
    <div class="flex-1 overflow-auto p-5">
      <div v-if="loading" class="p-8 text-center">{{ __('Loading quotation...') }}</div>
      <template v-else>
        <ErrorMessage v-if="error" class="mb-4" :message="error" />
        <p v-if="emailQueue" class="mb-4 text-sm text-ink-gray-7" role="status">
          {{ __('Email queued. Check Email Queue for delivery status.') }} {{ emailQueue }}
        </p>
        <Button v-if="conflict" class="mb-4" :label="__('Reload latest quotation')" @click="loadDocument" />
        <div v-if="doc" class="mx-auto max-w-5xl space-y-5">
          <div class="flex flex-wrap items-center gap-3">
            <span class="font-semibold">{{ __('Status') }}: {{ doc.status || 'Draft' }}</span>
            <span v-if="doc.deal">{{ __('Deal') }}: <button v-if="dealLabel" class="font-medium hover:underline" @click="openDeal">{{ dealLabel }}</button><span v-else>—</span></span>
            <template v-if="!isNew && !editing && canWrite">
              <Button v-if="doc.status === 'Draft'" :label="__('Send by Email')" :disabled="saving || sendingEmail" @click="openEmailDialog" />
              <Button v-if="doc.status === 'Draft'" :label="__('Mark as Sent')" :loading="saving" @click="changeStatus('Sent')" />
              <template v-if="doc.status === 'Sent'"><Button :label="__('Mark Accepted')" :loading="saving" @click="changeStatus('Accepted')" /><Button :label="__('Mark Rejected')" :loading="saving" @click="changeStatus('Rejected')" /></template>
            </template>
            <span v-if="doc.status === 'Sent'" class="text-xs text-ink-gray-5">{{ __('Delivery confirmed manually.') }}</span>
          </div>
          <fieldset :disabled="!editable" class="grid gap-4 sm:grid-cols-2">
            <label class="field">{{ __('Customer Type') }} *<select v-model="doc.customer_type" :disabled="!!doc.deal" @change="customerChanged"><option value="">{{ __('Select') }}</option><option value="PERSONAL">Personal</option><option value="COMPANY">Company</option></select></label>
            <label class="field">{{ __('Deal') }}<select v-model="doc.deal" @change="selectDeal($event.target.value)"><option value="">{{ __('None') }}</option><option v-if="doc.deal && !matchingDeals.some(x => x.name === doc.deal)" :value="doc.deal">{{ dealLabel || __('Unavailable') }}</option><option v-for="deal in matchingDeals" :key="deal.name" :value="deal.name">{{ deal.deal_title || deal.name }}</option><option v-if="dealContextReady && !matchingDeals.length && !doc.deal" disabled>{{ __('No matching deals') }}</option></select><span v-if="dealError" class="text-xs text-red-600">{{ dealError }}</span></label>
            <label v-if="doc.customer_type === 'COMPANY'" class="field">{{ __('Company') }} *<select v-model="doc.company" :disabled="!!doc.deal" @change="companyChanged"><option value="">{{ __('Select') }}</option><option v-if="doc.company && !companies.some(x => x.name === doc.company)" :value="doc.company">{{ doc.company }} ({{ __('unavailable') }})</option><option v-for="company in companies" :key="company.name" :value="company.name">{{ company.company_name || company.name }}</option></select></label>
            <label class="field">{{ __('Contact') }} {{ doc.customer_type === 'PERSONAL' ? '*' : '' }}<select v-model="doc.contact" :disabled="!!doc.deal" @change="customerContextChanged"><option value="">{{ __('None') }}</option><option v-if="doc.contact && !contacts.some(x => x.name === doc.contact)" :value="doc.contact">{{ doc.contact }} ({{ __('unavailable') }})</option><option v-for="contact in availableContacts" :key="contact.name" :value="contact.name">{{ [contact.first_name, contact.last_name].filter(Boolean).join(' ') || contact.name }}</option></select></label>
            <label class="field">{{ __('Price List') }}<select v-model="doc.price_list" @change="pricingContextChanged"><option value="">{{ __('Automatic (customer/default)') }}</option><option v-if="doc.price_list && !priceLists.some(x => x.name === doc.price_list)" :value="doc.price_list">{{ doc.price_list }} ({{ __('unavailable') }})</option><option v-for="priceList in priceLists" :key="priceList.name" :value="priceList.name">{{ priceList.price_list_name || priceList.name }}</option></select><span class="text-xs text-ink-gray-5">{{ __('Applied when pricing newly added products.') }}</span></label>
            <label class="field">{{ __('Quotation Date') }} *<TextInput v-model="doc.quotation_date" type="date" /></label>
            <label class="field">{{ __('Valid Until') }} *<TextInput v-model="doc.valid_until" type="date" /></label>
            <label class="field sm:col-span-2">{{ __('Notes') }}<textarea v-model="doc.notes" rows="2" /></label>
          </fieldset>
          <div v-if="optionsError" class="text-sm text-red-600">{{ optionsError }}</div>
          <div v-if="editable" class="flex flex-wrap items-end gap-2 rounded border p-3">
            <label class="min-w-64 flex-1 text-sm text-ink-gray-7">{{ __('Search sellable products') }}
              <TextInput v-model="productSearch" type="search" :placeholder="__('Search name or SKU...')" />
            </label>
            <Button v-if="productHasNextPage" variant="subtle" :label="__('Load more products')" :loading="productsLoading" @click="loadProducts({ append: true })" />
            <span v-else-if="productsLoading" class="text-sm text-ink-gray-5">{{ __('Loading products...') }}</span>
            <span class="text-xs text-ink-gray-5">{{ __('Only active Standard Products and Variants are available.') }}</span>
          </div>
          <div v-if="productPickerError" class="mt-2 text-sm text-red-600">{{ productPickerError }}</div>
          <div class="overflow-x-auto rounded-lg border border-outline-gray-2">
            <table class="w-full min-w-[1120px] table-fixed text-left text-sm"><thead class="bg-surface-gray-1 text-ink-gray-6"><tr><th class="w-[29%] p-3">{{ __('Product') }}</th><th class="w-[16%] p-3">{{ __('Unit Price (USD)') }}</th><th class="w-[10%] p-3">{{ __('Quantity') }}</th><th class="w-[13%] p-3">{{ __('Discount Type') }}</th><th class="w-[14%] p-3">{{ __('Discount') }}</th><th class="w-[12%] p-3 text-right">{{ __('Line Total (USD)') }}</th><th class="w-[6%] p-3" /></tr></thead>
              <tbody><tr v-for="(item, index) in doc.items" :key="item.name || index" class="border-t border-outline-gray-2 align-top">
                <td class="p-3"><select v-if="editable && !item.name" v-model="item.product" @change="selectProduct(item)"><option value="">{{ __('Select product') }}</option><option v-for="product in products" :key="product.name" :value="product.name">{{ productPickerLabel(product) }}</option></select><div v-else class="font-medium text-ink-gray-8">{{ item.product_name || item.product || '—' }}</div><div v-if="item.sku" class="mt-1 text-xs text-ink-gray-5">{{ __('SKU') }}: {{ item.sku }}</div></td>
                <td class="p-3"><TextInput v-if="editable" v-model="item.unit_price" type="number" min="0" step="0.01" @update:modelValue="markManualPrice(item)" /><span v-else>{{ money(item.unit_price) }}</span><div v-if="itemPricing(item).loading" class="mt-1 text-xs text-ink-gray-5">{{ __('Loading price...') }}</div><div v-else-if="itemPricing(item).error" class="mt-1 text-xs text-red-600">{{ itemPricing(item).error }}</div><div v-else-if="itemPricing(item).source" class="mt-1 text-xs text-ink-gray-5">{{ pricingSourceLabel(item) }}</div></td>
                <td class="p-3"><TextInput v-if="editable" v-model="item.quantity" type="number" min="0" step="any" /><span v-else>{{ item.quantity }}</span></td>
                <td class="p-3"><select v-if="editable" v-model="item.discount_type" @change="discountTypeChanged(item)"><option value="Percentage">{{ __('Percentage') }}</option><option value="Amount">{{ __('Amount') }}</option></select><span v-else>{{ item.discount_type === 'Amount' ? __('Amount') : __('Percentage') }}</span></td>
                <td class="p-3"><TextInput v-if="editable && item.discount_type === 'Amount'" v-model="item.discount_amount" type="number" min="0" step="0.01" /><TextInput v-else-if="editable" v-model="item.discount_percent" type="number" min="0" max="100" step="any" /><span v-else>{{ item.discount_type === 'Amount' ? money(item.discount_amount) : `${item.discount_percent || 0}%` }}</span></td>
                <td class="p-3 text-right font-medium text-ink-gray-8">{{ money(editable ? lineAmounts(item).total : item.line_total) }}</td>
                <td class="p-3 text-right"><Button v-if="editable" icon="trash-2" variant="ghost" :tooltip="__('Remove')" @click="doc.items.splice(index, 1)" /></td>
              </tr></tbody>
            </table>
          </div>
          <Button v-if="editable" :label="__('Add item')" iconLeft="plus" @click="addItem" />
          <div class="ml-auto max-w-xs space-y-2 text-right text-sm"><p>{{ __('Subtotal') }}: {{ money(editable ? totals.gross : doc.subtotal) }}</p><p>{{ __('Total discount') }}: {{ money(editable ? totals.discount : doc.total_discount) }}</p><p class="font-semibold">{{ __('Grand total') }}: {{ money(editable ? totals.total : doc.grand_total) }}</p><p v-if="editable" class="text-xs text-ink-gray-5">{{ __('Preview; final amounts are calculated by the server.') }}</p></div>
        </div>
      </template>
    </div>
    <Dialog v-model:open="showEmailDialog" :title="__('Send Quotation by Email')" :dismissible="!sendingEmail" :showCloseButton="!sendingEmail">
      <form class="space-y-4" @submit.prevent="sendEmail">
        <label class="field">{{ __('To') }}
          <TextInput v-model="email.recipient" type="email" required :disabled="sendingEmail" />
        </label>
        <label class="field">{{ __('Subject') }}
          <TextInput v-model="email.subject" maxlength="140" required :disabled="sendingEmail" />
        </label>
        <label class="field">{{ __('Message') }}
          <textarea v-model="email.body" rows="4" maxlength="10000" required :disabled="sendingEmail" />
        </label>
        <p class="text-sm text-ink-gray-6">{{ __('Attachment') }}: {{ doc?.name }}.pdf</p>
        <ErrorMessage v-if="emailError" :message="emailError" />
        <div class="flex justify-end gap-2">
          <Button type="button" :label="__('Cancel')" :disabled="sendingEmail" @click="showEmailDialog = false" />
          <Button type="submit" variant="solid" :label="__('Send Email')" :loading="sendingEmail" />
        </div>
      </form>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, Dialog, TextInput, call } from 'frappe-ui'
import LayoutHeader from '@/components/LayoutHeader.vue'
import { dealsForCustomer, lineAmounts, message, money } from '@/utils/quotation'

const route = useRoute(), router = useRouter()
const isNew = computed(() => route.name === 'QuotationCreate')
const doc = ref(null), loading = ref(true), saving = ref(false), editing = ref(false)
const exporting = ref(false)
const showEmailDialog = ref(false), sendingEmail = ref(false), emailError = ref(''), emailQueue = ref('')
const email = reactive({ recipient: '', subject: '', body: '' })
const canWrite = ref(false), canDelete = ref(false), error = ref(''), dealError = ref(''), optionsError = ref(''), conflict = ref(false)
const contacts = ref([]), companies = ref([]), deals = ref([]), priceLists = ref([]), products = ref([])
const productSearch = ref('')
const productsLoading = ref(false), productHasNextPage = ref(true), productPickerError = ref('')
const dealLoading = ref(false)
const dealLabel = ref('')
let dealRequestId = 0
let productRequestId = 0
let productSearchTimer = null
const productPageLength = 20
const pricingStates = new WeakMap()
const editable = computed(() => (isNew.value && canWrite.value) || (!isNew.value && editing.value && canWrite.value && doc.value?.status === 'Draft'))
const availableContacts = computed(() => doc.value?.customer_type === 'COMPANY' ? contacts.value.filter(c => c.company === doc.value.company) : contacts.value)
const dealContextReady = computed(() => doc.value?.customer_type === 'PERSONAL' ? Boolean(doc.value.contact) : doc.value?.customer_type === 'COMPANY' ? Boolean(doc.value.company) : false)
const matchingDeals = computed(() => {
  if (!doc.value || !dealContextReady.value) return []
  return dealsForCustomer(deals.value, doc.value)
})
const totals = computed(() => (doc.value?.items || []).reduce((sum, item) => { const a = lineAmounts(item); sum.gross += a.gross; sum.discount += a.discount; sum.total += a.total; return sum }, { gross: 0, discount: 0, total: 0 }))
const pricingPending = computed(() => (doc.value?.items || []).some(item => itemPricing(item).loading))
const list = (doctype, fields, filters = {}) => call('frappe.client.get_list', { doctype, fields, filters, limit_page_length: 500 })
async function loadOptions() {
  optionsError.value = ''
  const results = await Promise.allSettled([
    list('DoubleT Contact', ['name', 'first_name', 'last_name', 'company']),
    list('DoubleT Company', ['name', 'company_name']),
    list('DoubleT Deal', ['name', 'deal_title', 'deal_type', 'contact', 'company']),
    list('DoubleT Price List', ['name', 'price_list_name'], { is_active: 1 }),
  ])
  ;[contacts, companies, deals, priceLists].forEach((target, i) => { if (results[i].status === 'fulfilled') target.value = results[i].value || [] })
  if (results.some(r => r.status === 'rejected')) optionsError.value = __('Some linked records could not be loaded. Check your access and retry.')
}

watch(productSearch, () => {
  clearTimeout(productSearchTimer)
  productSearchTimer = setTimeout(() => loadProducts(), 250)
})

async function loadProducts({ append = false } = {}) {
  if (productsLoading.value && append) return
  if (append && !productHasNextPage.value) return

  const requestId = ++productRequestId
  const start = append ? products.value.length : 0
  if (!append) {
    products.value = []
    productHasNextPage.value = true
  }
  productsLoading.value = true
  productPickerError.value = ''
  const search = productSearch.value.trim()
  try {
    const data = await call('frappe.client.get_list', {
      doctype: 'DoubleT Product',
      fields: ['name', 'product_name', 'sku', 'product_kind', 'variant_of'],
      filters: [
        ['is_active', '=', 1],
        ['product_kind', 'in', ['Standard', 'Variant']],
      ],
      or_filters: search
        ? [
            ['product_name', 'like', `%${search}%`],
            ['sku', 'like', `%${search}%`],
          ]
        : undefined,
      order_by: 'product_name asc',
      limit_start: start,
      limit_page_length: productPageLength,
    })
    if (requestId !== productRequestId) return

    const page = Array.isArray(data) ? data : []
    const detailedPage = await hydrateProductDetails(page, requestId)
    if (requestId !== productRequestId) return
    const byName = new Map((append ? products.value : []).map((product) => [product.name, product]))
    detailedPage.forEach((product) => byName.set(product.name, product))
    products.value = [...byName.values()]
    productHasNextPage.value = page.length === productPageLength
  } catch (exception) {
    if (requestId === productRequestId) productPickerError.value = message(exception)
  } finally {
    if (requestId === productRequestId) productsLoading.value = false
  }
}

async function hydrateProductDetails(page, requestId) {
  const variantParents = [...new Set(page.map((product) => product.variant_of).filter(Boolean))]
  const variantNames = page.filter((product) => product.product_kind === 'Variant').map((product) => product.name)
  if (!variantParents.length && !variantNames.length) return page

  const [parentsResult, attributesResult] = await Promise.allSettled([
    variantParents.length
      ? call('frappe.client.get_list', {
          doctype: 'DoubleT Product',
          fields: ['name', 'product_name', 'sku'],
          filters: [['name', 'in', variantParents]],
          limit_page_length: variantParents.length,
        })
      : Promise.resolve([]),
    variantNames.length
      ? call('frappe.client.get_list', {
          doctype: 'DoubleT Product Variant Attribute',
          fields: ['parent', 'attribute_name', 'attribute_value'],
          filters: [
            ['parent', 'in', variantNames],
            ['parenttype', '=', 'DoubleT Product'],
            ['parentfield', '=', 'variant_attributes'],
          ],
          limit_page_length: 5000,
        })
      : Promise.resolve([]),
  ])
  if (requestId !== productRequestId) return []

  const parents = parentsResult.status === 'fulfilled' ? parentsResult.value : []
  const attributes = attributesResult.status === 'fulfilled' ? attributesResult.value : []

  const parentByName = new Map((parents || []).map((parent) => [parent.name, parent]))
  const attributesByProduct = {}
  for (const attribute of attributes || []) {
    if (!attribute.parent || !attribute.attribute_name) continue
    const values = attributesByProduct[attribute.parent] || (attributesByProduct[attribute.parent] = [])
    values.push(`${attribute.attribute_name}: ${attribute.attribute_value}`)
  }
  return page.map((product) => ({
    ...product,
    variant_parent: parentByName.get(product.variant_of),
    variant_attributes: attributesByProduct[product.name] || [],
  }))
}
async function loadDocument() {
  loading.value = true; error.value = ''; dealError.value = ''; conflict.value = false
  try {
    if (isNew.value) {
      const permission = await call('frappe.client.has_permission', { doctype: 'DoubleT Quotation', docname: '', perm_type: 'create' })
      canWrite.value = Boolean(permission?.has_permission)
      if (!canWrite.value) throw new Error(__('You do not have permission to create quotations.'))
      doc.value = { doctype: 'DoubleT Quotation', status: 'Draft', customer_type: '', contact: '', company: '', deal: '', price_list: '', quotation_date: '', valid_until: '', notes: '', items: [] }
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
function customerChanged() {
  if (doc.value.customer_type === 'PERSONAL') doc.value.company = ''
  if (doc.value.customer_type === 'COMPANY' && doc.value.contact) {
    const contact = contacts.value.find(row => row.name === doc.value.contact)
    if (contact?.company && !doc.value.company) doc.value.company = contact.company
    else if (contact && contact.company !== doc.value.company) doc.value.contact = ''
  }
  customerContextChanged()
}
function companyChanged() {
  const contact = contacts.value.find(row => row.name === doc.value.contact)
  if (contact && contact.company !== doc.value.company) doc.value.contact = ''
  customerContextChanged()
}
function customerContextChanged() {
  if (doc.value.deal && !matchingDeals.value.some(deal => deal.name === doc.value.deal)) {
    doc.value.deal = ''
    dealLabel.value = ''
    dealError.value = ''
  }
  pricingContextChanged()
}
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
    dealError.value = ''
    return
  }

  doc.value.deal = name
  dealLoading.value = true
  dealError.value = ''
  try {
    const deal = await call('frappe.client.get', { doctype: 'DoubleT Deal', name })
    if (requestId !== dealRequestId) return
    if (!deal?.name) throw new Error(__('The selected Deal could not be found.'))
    if (!['PERSONAL', 'COMPANY'].includes(deal.deal_type) || (deal.deal_type === 'COMPANY' && !deal.company) || (deal.deal_type === 'PERSONAL' && !deal.contact)) {
      throw new Error(__('The Deal customer information is incomplete or unavailable. Check the Deal customer or ask an administrator to check your access.'))
    }
    Object.assign(doc.value, { customer_type: deal.deal_type, contact: deal.contact || '', company: deal.company || '' })
    await loadDealLabel(name)
    dealError.value = ''
    await repriceAutomaticItems()
  } catch (e) {
    if (requestId !== dealRequestId) return
    dealError.value = isPermissionError(e)
      ? __('You do not have permission to read the selected Deal.')
      : message(e)
    dealLabel.value = ''
  } finally { if (requestId === dealRequestId) dealLoading.value = false }
}

function itemPricing(item) {
  if (!pricingStates.has(item)) {
    pricingStates.set(item, reactive({
      loading: false,
      error: '',
      manual: Boolean(item.name),
      auto: false,
      source: '',
      priceList: '',
      requestId: 0,
    }))
  }
  return pricingStates.get(item)
}

function addItem() {
  const item = { product: '', product_name: '', sku: '', quantity: 1, unit_price: '', discount_type: 'Percentage', discount_percent: 0, discount_amount: 0 }
  doc.value.items.push(item)
  itemPricing(item)
}

function discountTypeChanged(item) {
  if (item.discount_type === 'Amount') item.discount_percent = 0
  else item.discount_amount = 0
}

function markManualPrice(item) {
  const state = itemPricing(item)
  state.requestId += 1
  state.loading = false
  state.error = ''
  state.manual = true
  state.auto = false
  state.source = ''
  state.priceList = ''
}

async function selectProduct(item) {
  const product = products.value.find(product => product.name === item.product)
  const state = itemPricing(item)
  state.requestId += 1
  state.error = ''
  state.manual = false
  state.auto = false
  state.loading = false
  state.source = ''
  state.priceList = ''
  item.unit_price = ''
  if (!product) {
    Object.assign(item, { product_name: '', sku: '' })
    return
  }
  Object.assign(item, { product_name: product.product_name, sku: product.sku })
  await resolveItemPrice(item)
}

async function resolveItemPrice(item) {
  if (!item.product || item.name) return
  const state = itemPricing(item)
  if (state.manual) return
  const requestId = ++state.requestId
  const selectedProduct = item.product
  state.loading = true
  state.error = ''
  state.source = ''
  state.priceList = ''
  item.unit_price = ''
  try {
    const result = await call('doublet_crm.pricing.get_product_price', {
      product: selectedProduct,
      customer_type: doc.value.customer_type,
      contact: doc.value.contact || null,
      company: doc.value.company || null,
      price_list: doc.value.price_list || null,
    })
    if (requestId !== state.requestId || item.product !== selectedProduct || state.manual) return
    if (result?.price === undefined || result?.price === null || result?.price === '') {
      throw new Error(__('The pricing service did not return a price.'))
    }
    item.unit_price = result.price
    state.auto = true
    state.source = result.source || ''
    state.priceList = result.price_list || ''
  } catch (exception) {
    if (requestId !== state.requestId || item.product !== selectedProduct || state.manual) return
    item.unit_price = ''
    state.auto = false
    state.error = message(exception) || __('Unable to load the product price.')
  } finally {
    if (requestId === state.requestId) state.loading = false
  }
}

async function repriceAutomaticItems() {
  const items = (doc.value?.items || []).filter(item => {
    const state = itemPricing(item)
    return !item.name && item.product && !state.manual && (state.auto || item.unit_price === '' || item.unit_price === null)
  })
  await Promise.allSettled(items.map(resolveItemPrice))
}

function pricingContextChanged() {
  void repriceAutomaticItems()
}

function pricingSourceLabel(item) {
  const state = itemPricing(item)
  if (state.source === 'price_list' && state.priceList) {
    const priceList = priceLists.value.find(row => row.name === state.priceList)
    return `${__('Price List')}: ${priceList?.price_list_name || state.priceList}`
  }
  return state.source === 'product' ? __('Product default price') : ''
}
function productPickerLabel(product) {
  const details = [product.sku].filter(Boolean)
  if (product.product_kind === 'Variant') {
    if (product.variant_parent) details.push(`${__('Variant of')} ${product.variant_parent.product_name || product.variant_parent.name}`)
    if (product.variant_attributes?.length) details.push(product.variant_attributes.join(', '))
  }
  return `${product.product_name || product.name} — ${details.join(' · ')}`
}
function validate() {
  const d = doc.value
  if (dealError.value) return dealError.value
  if (!['PERSONAL', 'COMPANY'].includes(d.customer_type) || (d.customer_type === 'PERSONAL' && (!d.contact || d.company)) || (d.customer_type === 'COMPANY' && !d.company)) return __('Select a valid customer.')
  if (d.customer_type === 'COMPANY' && d.contact && contacts.value.some(c => c.name === d.contact && c.company !== d.company)) return __('Contact must belong to the selected Company.')
  if (!d.quotation_date || !d.valid_until || d.valid_until < d.quotation_date) return __('Enter valid quotation and expiry dates.')
  if (!d.items.length) return __('Add at least one item.')
  const decimal = value => /^\d+(\.\d+)?$/.test(String(value ?? '')) && Number.isFinite(Number(value))
  if (d.items.some((i) => {
    if (!i.product || !decimal(i.quantity) || Number(i.quantity) <= 0 || !decimal(i.unit_price)) return true
    if ((i.discount_type || 'Percentage') === 'Amount') {
      return !decimal(i.discount_amount ?? 0) || Number(i.discount_amount) > lineAmounts({ ...i, discount_amount: 0 }).gross
    }
    return !decimal(i.discount_percent ?? 0) || Number(i.discount_percent) > 100
  })) return __('Check product, quantity, price and discount for each item.')
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
function openEmailDialog() {
  email.recipient = ''
  email.subject = __('Quotation {0}', [doc.value.name])
  email.body = __('Please find our quotation attached.')
  emailError.value = ''
  showEmailDialog.value = true
}

async function sendEmail() {
  if (sendingEmail.value || doc.value?.status !== 'Draft') return
  sendingEmail.value = true
  emailError.value = ''
  try {
    const result = await call('doublet_crm.doublet_crm.doctype.doublet_quotation.quotation_pdf.send_quotation_email', {
      name: doc.value.name,
      modified: doc.value.modified,
      recipient: email.recipient,
      subject: email.subject,
      body: email.body,
    })
    emailQueue.value = result.email_queue
    showEmailDialog.value = false
  } catch (e) {
    emailError.value = message(e)
  } finally {
    sendingEmail.value = false
  }
}

async function save() {
  if (saving.value || dealLoading.value || pricingPending.value || !editable.value) return
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
  if (status === 'Sent' && !window.confirm(__('Confirm that the quotation PDF has already been sent through the agreed channel. This action only records the delivery; it does not send anything.'))) return
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
  loadProducts()
  await loadDocument()
  const queryDeal = Array.isArray(route.query.deal) ? '' : dealName(route.query.deal)
  if (isNew.value && queryDeal && doc.value) await selectDeal(queryDeal)
})
onBeforeUnmount(() => clearTimeout(productSearchTimer))
</script>

<style scoped>
.field { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.875rem; }
select, textarea { width: 100%; border: 1px solid #d1d5db; border-radius: 0.25rem; padding: 0.4rem; background: white; }
fieldset:disabled { opacity: 0.8; }
</style>
