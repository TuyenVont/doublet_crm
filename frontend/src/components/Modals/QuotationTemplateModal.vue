<template>
  <Dialog
    v-model:open="open"
    :title="isEdit ? __('Edit Quotation Template') : __('Create Quotation Template')"
    size="3xl"
    :dismissible="!saving"
    :showCloseButton="!saving"
  >
    <form class="flex max-h-[80vh] min-h-0 flex-col" @submit.prevent="save">
      <div class="min-h-0 flex-1 space-y-4 overflow-y-auto px-1 pb-4">
        <ErrorMessage v-if="error" :message="error" />

        <div class="grid gap-4 sm:grid-cols-2">
          <label class="field">
            {{ __('Template Name') }} *
            <TextInput v-model="form.template_name" required :disabled="saving || isEdit" />
          </label>
          <label class="field">
            {{ __('Product / Service Group') }}
            <select v-model="form.product_category" :disabled="saving">
              <option value="">{{ __('All / Unspecified') }}</option>
              <option v-for="cat in categories" :key="cat.name" :value="cat.name">
                {{ cat.category_name || cat.name }}
              </option>
            </select>
          </label>
          <label class="field sm:col-span-2">
            {{ __('Description') }}
            <textarea v-model="form.description" rows="2" :disabled="saving" />
          </label>
          <label class="field sm:col-span-2">
            {{ __('Terms & Conditions') }}
            <textarea v-model="form.terms" rows="3" :disabled="saving" />
          </label>
          <label class="flex items-center gap-2 text-sm text-ink-gray-8 sm:col-span-2">
            <input v-model="form.is_active" type="checkbox" class="h-4 w-4" :disabled="saving" />
            <span>{{ __('Active (available for Quotation Drafts)') }}</span>
          </label>
        </div>

        <div class="space-y-2">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <p class="text-sm font-semibold text-ink-gray-8">{{ __('Template Products & Default Quantities') }}</p>
            <Button type="button" variant="subtle" :label="__('Add Product')" iconLeft="plus" :disabled="saving" @click="addRow" />
          </div>
          <p class="text-xs text-ink-gray-5">
            {{ __('Unit prices are not stored on templates; Quotation Drafts resolve current customer prices automatically.') }}
          </p>
          <div class="overflow-x-auto rounded border border-outline-gray-2">
            <table class="w-full min-w-[560px] text-left text-sm">
              <thead class="bg-surface-gray-1 text-ink-gray-6">
                <tr>
                  <th class="p-3">{{ __('Product') }}</th>
                  <th class="w-36 p-3">{{ __('Default Quantity') }}</th>
                  <th class="w-14 p-3" />
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, index) in form.items" :key="index" class="border-t border-outline-gray-2">
                  <td class="p-3">
                    <select v-model="row.product" :disabled="saving" @change="productChanged(row)">
                      <option value="">{{ __('Select sellable product') }}</option>
                      <option v-for="p in rowProductOptions(row)" :key="p.name" :value="p.name">
                        {{ productPickerLabel(p) }}
                      </option>
                    </select>
                  </td>
                  <td class="p-3">
                    <TextInput v-model="row.default_quantity" type="number" min="0.01" step="any" :disabled="saving" />
                  </td>
                  <td class="p-3 text-right">
                    <Button type="button" icon="trash-2" variant="ghost" :disabled="saving" @click="form.items.splice(index, 1)" />
                  </td>
                </tr>
                <tr v-if="!form.items.length">
                  <td colspan="3" class="p-4 text-center text-ink-gray-5">{{ __('Add at least one product.') }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div class="flex shrink-0 justify-end gap-2 border-t border-outline-gray-2 bg-surface-white pt-3">
        <Button type="button" :label="__('Cancel')" :disabled="saving" @click="open = false" />
        <Button type="submit" variant="solid" :label="isEdit ? __('Save') : __('Create')" :loading="saving" />
      </div>
    </form>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, ErrorMessage, TextInput, call } from 'frappe-ui'
import { useSellableProducts } from '@/composables/useSellableProducts'
import { message, productOptionsForItem } from '@/utils/quotation'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  template: { type: Object, default: null },
})
const emit = defineEmits(['update:modelValue', 'saved'])

const open = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
const isEdit = computed(() => Boolean(props.template?.name))
const saving = ref(false)
const error = ref('')
const categories = ref([])
const form = reactive({
  name: '',
  template_name: '',
  product_category: '',
  description: '',
  terms: '',
  is_active: true,
  items: [],
})

const { products, loadProducts, productPickerLabel } = useSellableProducts()

function rowProductOptions(row) {
  return productOptionsForItem(products.value, row)
}

function addRow() {
  form.items.push({ product: '', product_name: '', sku: '', default_quantity: 1 })
}

function productChanged(row) {
  const product = products.value.find((p) => p.name === row.product)
  row.product_name = product?.product_name || ''
  row.sku = product?.sku || ''
}

function resetForm() {
  error.value = ''
  const t = props.template
  form.name = t?.name || ''
  form.template_name = t?.template_name || ''
  form.product_category = t?.product_category || ''
  form.description = t?.description || ''
  form.terms = t?.terms || ''
  form.is_active = t ? Boolean(Number(t.is_active)) : true
  form.items = (t?.items || []).map((row) => ({
    name: row.name,
    product: row.product || '',
    product_name: row.product_name || '',
    sku: row.sku || '',
    default_quantity: row.default_quantity || 1,
  }))
  if (!form.items.length) addRow()
}

async function loadCategories() {
  try {
    categories.value = await call('frappe.client.get_list', {
      doctype: 'DoubleT Product Category',
      fields: ['name', 'category_name'],
      order_by: 'category_name asc',
      limit_page_length: 200,
    })
  } catch {
    categories.value = []
  }
}

watch(open, (visible) => {
  if (!visible) return
  resetForm()
  loadCategories()
  loadProducts()
})

async function save() {
  if (saving.value) return
  error.value = ''
  const name = form.template_name.trim()
  if (!name) {
    error.value = __('Template Name is required.')
    return
  }
  if (!form.items.length || form.items.some((row) => !row.product || !(Number(row.default_quantity) > 0))) {
    error.value = __('Select a valid product and positive default quantity for every row.')
    return
  }

  saving.value = true
  try {
    const payload = {
      doctype: 'DoubleT Quotation Template',
      template_name: name,
      product_category: form.product_category || null,
      description: form.description || '',
      terms: form.terms || '',
      is_active: form.is_active ? 1 : 0,
      items: form.items.map((row) => ({
        ...(row.name ? { name: row.name } : {}),
        product: row.product,
        default_quantity: Number(row.default_quantity),
      })),
    }
    if (isEdit.value) {
      await call('frappe.client.save', { doc: { ...props.template, ...payload } })
    } else {
      await call('frappe.client.insert', { doc: payload })
    }
    emit('saved')
    open.value = false
  } catch (e) {
    error.value = message(e)
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.field { display: flex; flex-direction: column; gap: 0.3rem; font-size: 0.875rem; }
select, textarea { width: 100%; border: 1px solid #d1d5db; border-radius: 0.25rem; padding: 0.4rem; background: white; }
</style>
