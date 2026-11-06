<template>
  <Dialog v-model:open="show" :size="'lg'">
    <template #body>
      <div class="bg-surface-elevation-1 px-4 pb-6 pt-5 sm:px-6">
        <div class="mb-5 flex items-center justify-between">
          <h3 class="text-xl font-semibold text-ink-gray-9">
            {{ isEditMode ? __('Edit Product') : __('New Product') }}
          </h3>
          <Button variant="ghost" class="w-7" icon="lucide-x" @click="show = false" />
        </div>

        <div class="grid gap-4 sm:grid-cols-2">
          <label class="space-y-1 sm:col-span-2">
            <span class="text-sm text-ink-gray-7">{{ __('Product Name') }} *</span>
            <TextInput v-model="form.product_name" :placeholder="__('Product Name')" />
          </label>
          <label class="space-y-1">
            <span class="text-sm text-ink-gray-7">{{ __('SKU') }} *</span>
            <TextInput v-model="form.sku" :placeholder="__('SKU')" :disabled="isEditMode" />
            <span class="block text-xs text-ink-gray-5">
              {{ isEditMode ? __('SKU cannot be changed after creation.') : __('A SKU is suggested automatically. You may replace it or leave it blank to generate one when saving.') }}
            </span>
          </label>
          <label class="space-y-1">
            <span class="text-sm text-ink-gray-7">{{ __('Category') }} *</span>
            <select v-model="form.category" class="h-8 w-full rounded border border-outline-gray-2 bg-surface-white px-2 text-sm">
              <option value="" disabled>{{ __('Select a category') }}</option>
              <option v-for="category in categories" :key="category.name" :value="category.name">
                {{ category.category_name || category.name }}
              </option>
            </select>
          </label>
          <label class="space-y-1">
            <span class="text-sm text-ink-gray-7">{{ __('Price') }} *</span>
            <TextInput v-model="form.price" type="number" min="0" step="0.01" :placeholder="__('0')" />
          </label>
          <label class="flex items-center gap-2 self-end pb-1 text-sm text-ink-gray-7">
            <input v-model="form.is_active" type="checkbox" class="rounded border-outline-gray-3" />
            {{ __('Active') }}
          </label>
          <label class="space-y-1 sm:col-span-2">
            <span class="text-sm text-ink-gray-7">{{ __('Description') }}</span>
            <textarea v-model="form.description" rows="3" class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm" />
          </label>
        </div>

        <div v-if="categoriesResource.loading" class="mt-3 text-sm text-ink-gray-5">
          {{ __('Loading categories...') }}
        </div>
        <ErrorMessage v-if="categoriesError" class="mt-4" :message="categoriesError" />
        <ErrorMessage v-if="error" class="mt-4" :message="error" />
        <Button v-if="needsReload" class="mt-3" variant="subtle" :label="__('Reload latest Product')" @click="reloadLatest" />
      </div>
      <div class="flex justify-end gap-2 px-4 pb-6 pt-4 sm:px-6">
        <Button variant="subtle" :label="__('Cancel')" @click="show = false" />
        <Button variant="solid" :label="isEditMode ? __('Save') : __('Create')" :loading="submitting" @click="saveProduct" />
      </div>
    </template>
  </Dialog>
</template>

<script setup>
import { computed, reactive, ref, watch } from 'vue'
import { Button, Dialog, TextInput, call, createResource } from 'frappe-ui'

const props = defineProps({
  product: { type: Object, default: null },
})
const emit = defineEmits(['saved', 'reload-latest'])
const show = defineModel({ type: Boolean })
const submitting = ref(false)
const error = ref('')
const needsReload = ref(false)
const form = reactive({
  product_name: '',
  sku: '',
  category: '',
  price: 0,
  description: '',
  is_active: true,
})

const isEditMode = computed(() => Boolean(props.product?.name))
const categoriesResource = createResource({
  url: 'frappe.client.get_list',
  params: {
    doctype: 'DoubleT Product Category',
    fields: ['name', 'category_name'],
    order_by: 'category_name asc',
    limit_page_length: 500,
  },
  auto: true,
})
const categories = computed(() => categoriesResource.data || [])
const categoriesError = computed(() => {
  const resourceError = categoriesResource.error
  return resourceError?.messages?.[0] || resourceError?.message || resourceError || ''
})

watch(show, (isOpen) => {
  if (!isOpen) return
  populateForm()
  categoriesResource.reload()
})

watch(() => props.product, () => {
  if (show.value) populateForm()
})

function populateForm() {
  error.value = ''
  needsReload.value = false
  Object.assign(form, {
    product_name: props.product?.product_name || '',
    sku: props.product?.sku || '',
    category: props.product?.category || '',
    price: props.product?.price ?? 0,
    description: props.product?.description || '',
    is_active: props.product ? isActive(props.product.is_active) : true,
  })
}

function isActive(value) {
  return value === 1 || value === '1' || value === true
}

function validate() {
  if (!form.product_name.trim() || !form.category) {
    return __('Product Name and Category are required.')
  }
  if (form.price === '' || Number.isNaN(Number(form.price)) || Number(form.price) < 0) {
    return __('Price must be a nonnegative number.')
  }
  return ''
}

async function saveProduct() {
  if (submitting.value) return
  error.value = validate()
  if (error.value) return

  submitting.value = true
  const fields = {
    product_name: form.product_name.trim(),
    category: form.category,
    price: Number(form.price),
    description: form.description,
    is_active: form.is_active ? 1 : 0,
  }
  const doc = isEditMode.value
    ? { ...props.product, ...fields, sku: props.product.sku }
    : { doctype: 'DoubleT Product', ...fields, sku: form.sku.trim() }

  try {
    const saved = await call(isEditMode.value ? 'frappe.client.save' : 'frappe.client.insert', { doc })
    emit('saved', saved)
    show.value = false
  } catch (exception) {
    const message = exception?.messages?.[0] || exception?.message || __('Unable to save product.')
    if (String(message).toLowerCase().includes('modified after')) {
      error.value = __('This Product was changed by someone else. Reload the latest version before saving your changes.')
      needsReload.value = true
    } else {
      error.value = message
    }
  } finally {
    submitting.value = false
  }
}

function reloadLatest() {
  emit('reload-latest', props.product?.name)
}
</script>
