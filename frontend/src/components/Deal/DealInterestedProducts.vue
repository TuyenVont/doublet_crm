<template>
  <div class="flex min-h-0 w-full flex-col overflow-hidden">
    <div class="flex items-center justify-between gap-3 border-b px-5 py-3">
      <div>
        <h2 class="font-semibold">{{ __('Products') }}</h2>
        <p class="text-xs text-ink-gray-5">{{ __('Reference prices follow the current customer pricing context and do not change Deal Amount.') }}</p>
      </div>
      <div class="flex gap-2">
        <Button :label="__('Refresh')" :loading="loading" @click="load" />
        <Button v-if="canWrite" :label="__('Browse Catalog')" @click="openCatalog" />
        <Button v-if="canWrite" variant="solid" :label="__('Save Products')" :loading="saving" @click="save" />
      </div>
    </div>

    <div class="flex-1 overflow-auto p-5">
      <p v-if="error" class="mb-3 text-sm text-red-600" role="alert">{{ error }}</p>
      <p v-if="loading && !rows.length" class="p-8 text-center">{{ __('Loading products...') }}</p>
      <p v-else-if="!rows.length && !error" class="p-8 text-center text-ink-gray-5">{{ __('No interested products on this Deal.') }}</p>
      <div v-else-if="rows.length" class="overflow-x-auto rounded border">
        <table class="w-full min-w-[720px] text-left text-sm">
          <thead>
            <tr><th class="p-3">{{ __('Product') }}</th><th>{{ __('SKU') }}</th><th>{{ __('Variant') }}</th><th>{{ __('Quantity') }}</th><th class="text-right">{{ __('Reference Price') }}</th><th class="p-3"></th></tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in rows" :key="row.product" class="border-t">
              <td class="p-3 font-medium">{{ row.product_name || row.product }}</td>
              <td>{{ row.sku }}</td>
              <td>{{ row.variant_attributes || '—' }}</td>
              <td class="py-2"><TextInput v-if="canWrite" v-model="row.quantity" type="number" min="0.000001" step="any" class="w-28" /><span v-else>{{ row.quantity }}</span></td>
              <td class="text-right">{{ row.reference_price === '' ? '—' : money(row.reference_price) }}</td>
              <td class="p-3 text-right"><Button v-if="canWrite" variant="ghost" :label="__('Remove')" @click="rows.splice(index, 1)" /></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <Dialog v-model="showCatalog" :options="{ title: __('Select Products'), size: 'xl' }">
      <template #body-content>
        <div class="space-y-3">
          <div class="grid gap-2 md:grid-cols-2">
            <TextInput v-model="productSearch" :placeholder="__('Search Product or SKU')" />
            <select v-model="productCategory" class="rounded border px-3 py-2 text-sm">
              <option value="">{{ __('All categories') }}</option>
              <option v-for="category in productCategories" :key="category.name" :value="category.name">{{ category.category_name || category.name }}</option>
            </select>
          </div>
          <p v-if="productPickerError" class="text-sm text-red-600">{{ productPickerError }}</p>
          <div class="max-h-[55vh] overflow-auto rounded border">
            <label v-for="product in products" :key="product.name" class="flex items-center gap-3 border-b p-3 last:border-b-0">
              <input type="checkbox" :checked="Boolean(selected[product.name])" :disabled="existingProducts.has(product.name)" @change="toggle(product, $event.target.checked)" />
              <span class="min-w-0 flex-1 text-sm">{{ productPickerLabel(product) }}</span>
              <TextInput v-if="selected[product.name]" v-model="quantities[product.name]" type="number" min="0.000001" step="any" class="w-24" />
              <span v-else-if="existingProducts.has(product.name)" class="text-xs text-ink-gray-5">{{ __('Already added') }}</span>
            </label>
            <p v-if="productsLoading && !products.length" class="p-6 text-center">{{ __('Loading products...') }}</p>
            <p v-else-if="!products.length && !productPickerError" class="p-6 text-center text-ink-gray-5">{{ __('No sellable products found.') }}</p>
          </div>
          <Button v-if="productHasNextPage" :label="__('Load More')" :loading="productsLoading" @click="loadProducts({ append: true })" />
        </div>
      </template>
      <template #actions>
        <Button :label="__('Cancel')" @click="showCatalog = false" />
        <Button variant="solid" :label="__('Add Selected')" @click="addSelected" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, TextInput, call } from 'frappe-ui'
import { useSellableProducts } from '@/composables/useSellableProducts'
import { message, money } from '@/utils/quotation'
import { appendInterestedProductSelections } from '@/utils/dealProducts'

const props = defineProps({ dealId: { type: String, required: true } })
const rows = ref([]), modified = ref(''), canWrite = ref(false), loading = ref(false), saving = ref(false), error = ref('')
const showCatalog = ref(false), selected = reactive({}), quantities = reactive({})
const {
  products, productSearch, productCategory, productCategories, productsLoading,
  productHasNextPage, productPickerError, loadProducts, loadProductCategories, productPickerLabel,
} = useSellableProducts()
const existingProducts = computed(() => new Set(rows.value.map(row => row.product)))

async function load() {
  loading.value = true; error.value = ''
  try {
    const result = await call('doublet_crm.sales_completion.get_deal_products', { deal_name: props.dealId })
    rows.value = (result?.products || []).map(row => ({ ...row }))
    modified.value = result?.modified || ''
    canWrite.value = Boolean(result?.can_write)
  } catch (exception) { error.value = message(exception) } finally { loading.value = false }
}

async function save() {
  if (!canWrite.value || saving.value) return
  saving.value = true; error.value = ''
  try {
    const result = await call('doublet_crm.sales_completion.save_deal_products', {
      deal_name: props.dealId,
      products: rows.value.map(row => ({ product: row.product, quantity: row.quantity })),
      modified: modified.value,
    })
    rows.value = (result?.products || []).map(row => ({ ...row }))
    modified.value = result?.modified || ''
  } catch (exception) { error.value = message(exception) } finally { saving.value = false }
}

function toggle(product, checked) {
  if (checked) { selected[product.name] = product; quantities[product.name] = quantities[product.name] || 1 }
  else { delete selected[product.name]; delete quantities[product.name] }
}
function openCatalog() {
  Object.keys(selected).forEach(key => delete selected[key])
  Object.keys(quantities).forEach(key => delete quantities[key])
  showCatalog.value = true
  void Promise.all([loadProducts(), loadProductCategories()])
}
function addSelected() {
  appendInterestedProductSelections(
    rows.value,
    Object.entries(selected).map(([name, product]) => ({ product, quantity: quantities[name] ?? 1 })),
  )
  showCatalog.value = false
}

watch(() => props.dealId, load, { immediate: true })
</script>
