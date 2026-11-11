<template>
  <Dialog v-model:open="show" :size="'xl'">
    <template #body>
      <div class="bg-surface-elevation-1 px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-xl font-semibold text-ink-gray-9">
            {{ isEditMode ? __('Edit Price List') : __('New Price List') }}
          </h3>
          <Button variant="ghost" class="w-7" icon="lucide-x" @click="show = false" />
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <label class="space-y-1 sm:col-span-2">
            <span class="text-sm text-ink-gray-7">{{ __('Price List Name') }} *</span>
            <TextInput v-model="form.price_list_name" :disabled="isEditMode" :placeholder="__('For example, Retail')" />
            <span v-if="isEditMode" class="block text-xs text-ink-gray-5">{{ __('Price List Name cannot be changed after creation.') }}</span>
            <span v-if="fieldErrors.price_list_name" class="block text-xs text-red-600">{{ fieldErrors.price_list_name }}</span>
          </label>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <input v-model="form.is_active" type="checkbox" class="rounded border-outline-gray-3" />
            {{ __('Active') }}
          </label>
          <label class="flex items-center gap-2 text-sm text-ink-gray-7">
            <input v-model="form.is_default" type="checkbox" class="rounded border-outline-gray-3" />
            {{ __('Default Price List') }}
          </label>
        </div>

        <div class="mt-6 overflow-hidden rounded border border-outline-gray-2">
          <div class="flex items-center justify-between border-b border-outline-gray-2 bg-surface-gray-1 px-4 py-3">
            <div>
              <h4 class="font-medium text-ink-gray-8">{{ __('Product Prices') }}</h4>
              <p class="mt-0.5 text-xs text-ink-gray-5">{{ __('Add Standard Products or Variants. Templates are not available.') }}</p>
            </div>
            <Button variant="subtle" size="sm" :label="__('Add Product')" iconLeft="plus" @click="addItem" />
          </div>

          <div v-if="form.items.length" class="overflow-x-auto">
            <table class="w-full min-w-[620px] text-sm">
              <thead class="bg-surface-gray-1 text-left text-ink-gray-6">
                <tr>
                  <th class="px-4 py-3 font-medium">{{ __('Product / Variant') }}</th>
                  <th class="w-44 px-4 py-3 text-right font-medium">{{ __('Price') }}</th>
                  <th class="w-16 px-4 py-3"><span class="sr-only">{{ __('Remove') }}</span></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in form.items" :key="item.key" class="border-t border-outline-gray-2">
                  <td class="px-4 py-2">
                    <Link
                      v-model="item.product"
                      doctype="DoubleT Product"
                      :filters="productFilters"
                      :placeholder="__('Search Product or Variant')"
                    />
                    <span v-if="itemErrors[index]?.product" class="mt-1 block text-xs text-red-600">{{ itemErrors[index].product }}</span>
                  </td>
                  <td class="px-4 py-2">
                    <TextInput v-model="item.price" type="number" min="0" step="1" class="text-right" :placeholder="__('0')" />
                    <span v-if="itemErrors[index]?.price" class="mt-1 block text-xs text-red-600">{{ itemErrors[index].price }}</span>
                  </td>
                  <td class="px-3 py-2 text-right">
                    <Button variant="subtle" icon="trash-2" :aria-label="__('Remove product price')" @click="removeItem(index)" />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else class="px-4 py-8 text-center text-sm text-ink-gray-5">
            {{ __('No Product prices yet. Product default prices will be used until you add one.') }}
          </div>
        </div>

        <ErrorMessage v-if="error" class="mt-4" :message="error" />
      </div>
      <div class="flex justify-end gap-2 px-4 pb-6 pt-4 sm:px-6">
        <Button variant="subtle" :label="__('Cancel')" @click="show = false" />
        <Button variant="solid" :label="isEditMode ? __('Save') : __('Create')" :loading="submitting" @click="save" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, TextInput, call } from 'frappe-ui'

import Link from '@/components/Controls/Link.vue'

const props = defineProps({ priceList: { type: Object, default: null } })
const emit = defineEmits(['saved'])
const show = defineModel({ type: Boolean })
const submitting = ref(false)
const error = ref('')
const fieldErrors = reactive({})
const itemErrors = reactive({})
const form = reactive({ price_list_name: '', is_active: true, is_default: false, items: [] })
const productFilters = [['product_kind', 'in', ['Standard', 'Variant']]]

const isEditMode = computed(() => Boolean(props.priceList?.name))

watch(show, (isOpen) => {
  if (isOpen) populateForm()
})
watch(() => props.priceList, () => {
  if (show.value) populateForm()
})

function isChecked(value) {
  return value === 1 || value === '1' || value === true
}

function makeItem(item = {}) {
  return {
    key: item.name || `${Date.now()}-${Math.random()}`,
    name: item.name,
    product: item.product || '',
    price: item.price ?? '',
  }
}

function populateForm() {
  error.value = ''
  clearErrors()
  Object.assign(form, {
    price_list_name: props.priceList?.price_list_name || '',
    is_active: props.priceList ? isChecked(props.priceList.is_active) : true,
    is_default: props.priceList ? isChecked(props.priceList.is_default) : false,
    items: (props.priceList?.items || []).map(makeItem),
  })
}

function addItem() {
  form.items.push(makeItem())
}

function removeItem(index) {
  form.items.splice(index, 1)
  delete itemErrors[index]
}

function clearErrors() {
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
  Object.keys(itemErrors).forEach((key) => delete itemErrors[key])
}

function validate() {
  clearErrors()
  if (!form.price_list_name.trim()) fieldErrors.price_list_name = __('Price List Name is required.')
  const products = new Set()
  form.items.forEach((item, index) => {
    const errors = {}
    if (!item.product) errors.product = __('Select a Product or Variant.')
    else if (products.has(item.product)) errors.product = __('A Product can only appear once.')
    products.add(item.product)
    if (item.price === '' || Number.isNaN(Number(item.price)) || Number(item.price) < 0) {
      errors.price = __('Price must be a nonnegative number.')
    }
    if (Object.keys(errors).length) itemErrors[index] = errors
  })
  return Object.keys(fieldErrors).length || Object.keys(itemErrors).length
}

async function save() {
  if (submitting.value || validate()) return
  error.value = ''
  submitting.value = true
  const fields = {
    price_list_name: form.price_list_name.trim(),
    is_active: form.is_active ? 1 : 0,
    is_default: form.is_default ? 1 : 0,
    items: form.items.map((item) => ({
      ...(item.name ? { name: item.name } : {}),
      product: item.product,
      price: Number(item.price),
    })),
  }
  const doc = isEditMode.value
    ? { ...props.priceList, ...fields, price_list_name: props.priceList.price_list_name }
    : { doctype: 'DoubleT Price List', ...fields }
  try {
    const saved = await call(isEditMode.value ? 'frappe.client.save' : 'frappe.client.insert', { doc })
    emit('saved', saved)
    show.value = false
  } catch (exception) {
    error.value = exception?.messages?.[0] || exception?.message || __('Unable to save Price List.')
  } finally {
    submitting.value = false
  }
}
</script>
