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
            <span v-if="fieldErrors.product_name" class="block text-xs text-red-600">{{ fieldErrors.product_name }}</span>
          </label>
          <label class="space-y-1">
            <span class="text-sm text-ink-gray-7">{{ __('SKU') }} *</span>
            <TextInput v-model="form.sku" :placeholder="__('SKU')" :disabled="isEditMode" />
            <span class="block text-xs text-ink-gray-5">
              {{ isEditMode ? __('SKU cannot be changed after creation.') : __('A SKU is suggested automatically. You may replace it or leave it blank to generate one when saving.') }}
            </span>
          </label>
          <label class="space-y-1">
            <span class="text-sm text-ink-gray-7">{{ __('Product Kind') }} *</span>
            <select v-model="form.product_kind" :disabled="isExistingVariant" class="h-8 w-full rounded border border-outline-gray-2 bg-surface-white px-2 text-sm" @change="handleKindChange">
              <option value="Standard">{{ __('Standard') }}</option>
              <option value="Template">{{ __('Template') }}</option>
              <option value="Variant">{{ __('Variant') }}</option>
            </select>
            <span v-if="form.product_kind === 'Template'" class="block text-xs text-amber-700">{{ __('Templates organize variants and cannot be sold directly.') }}</span>
          </label>
          <label class="space-y-1">
            <span class="text-sm text-ink-gray-7">{{ __('Primary Category') }} *</span>
            <select v-model="form.category" class="h-8 w-full rounded border border-outline-gray-2 bg-surface-white px-2 text-sm" @change="ensurePrimaryCategory">
              <option value="" disabled>{{ __('Select a category') }}</option>
              <option v-for="category in categories" :key="category.name" :value="category.name">
                {{ category.category_name || category.name }}
              </option>
            </select>
            <span v-if="fieldErrors.category" class="block text-xs text-red-600">{{ fieldErrors.category }}</span>
          </label>
          <div class="space-y-2 sm:col-span-2">
            <span class="text-sm text-ink-gray-7">{{ __('Categories') }}</span>
            <div v-if="selectedCategories.length" class="flex flex-wrap gap-1.5">
              <span v-for="category in selectedCategories" :key="category.name" class="inline-flex items-center gap-1 rounded-full bg-surface-gray-2 px-2 py-1 text-xs text-ink-gray-7">
                {{ category.label }}
                <span v-if="category.name === form.category" class="text-ink-gray-5">{{ __('Primary') }}</span>
                <button
                  v-else
                  type="button"
                  class="ml-0.5 rounded text-ink-gray-5 hover:text-ink-gray-9 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                  :aria-label="__('Remove {0}', [category.label])"
                  @click="removeCategory(category.name)"
                >
                  ×
                </button>
              </span>
            </div>
            <Popover side="bottom" align="start" :collision-padding="16">
              <template #target="{ togglePopover }">
                <button
                  type="button"
                  class="flex h-8 w-full items-center justify-between rounded border border-outline-gray-2 bg-surface-white px-2 text-left text-sm text-ink-gray-7 hover:border-outline-gray-3 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
                  @click="togglePopover"
                >
                  <span>{{ selectedCategories.length ? __('Manage {0} categories', [selectedCategories.length]) : __('Select categories') }}</span>
                  <span class="lucide-chevron-down h-4 w-4" aria-hidden="true" />
                </button>
              </template>
              <template #body>
                <div class="z-[200] w-72 rounded-lg border border-outline-gray-3 bg-white p-1 text-ink-gray-8 shadow-xl">
                  <div class="max-h-[min(16rem,calc(100vh-8rem))] overflow-y-auto overscroll-contain py-1">
                    <label v-for="category in categories" :key="category.name" class="flex cursor-pointer items-center gap-2 rounded px-2 py-2 text-sm text-ink-gray-7 hover:bg-surface-gray-1">
                      <input
                        type="checkbox"
                        class="rounded border-outline-gray-3"
                        :checked="isCategorySelected(category.name)"
                        :disabled="category.name === form.category"
                        @change="toggleCategory(category.name, $event.target.checked)"
                      />
                      <span class="min-w-0 flex-1 truncate">{{ category.category_name || category.name }}</span>
                      <span v-if="category.name === form.category" class="text-xs text-ink-gray-5">{{ __('Primary') }}</span>
                    </label>
                  </div>
                </div>
              </template>
            </Popover>
            <span class="block text-xs text-ink-gray-5">{{ __('The primary category is always included. Choose any additional categories below.') }}</span>
          </div>
          <label class="space-y-1">
            <span class="text-sm text-ink-gray-7">{{ __('Price (USD)') }} *</span>
            <TextInput v-model="form.price" type="number" min="0" step="0.01" :placeholder="__('0.00')" />
            <span v-if="fieldErrors.price" class="block text-xs text-red-600">{{ fieldErrors.price }}</span>
          </label>
          <label class="flex items-center gap-2 self-end pb-1 text-sm text-ink-gray-7">
            <input v-model="form.is_active" type="checkbox" class="rounded border-outline-gray-3" />
            {{ __('Active') }}
          </label>
          <div v-if="form.product_kind === 'Variant'" class="space-y-4 sm:col-span-2">
            <label class="block space-y-1">
              <span class="text-sm text-ink-gray-7">{{ __('Template') }} *</span>
              <select v-model="form.variant_of" :disabled="isExistingVariant" class="h-8 w-full rounded border border-outline-gray-2 bg-surface-white px-2 text-sm">
                <option value="" disabled>{{ __('Select a template') }}</option>
                <option v-for="template in availableTemplates" :key="template.name" :value="template.name">
                  {{ template.product_name || template.name }} — {{ template.sku }}{{ isActive(template.is_active) ? '' : ` (${__('Inactive')})` }}
                </option>
              </select>
              <span v-if="fieldErrors.variant_of" class="block text-xs text-red-600">{{ fieldErrors.variant_of }}</span>
            </label>
            <div class="space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-sm text-ink-gray-7">{{ __('Variant Attributes') }} *</span>
                <Button v-if="!isExistingVariant" variant="subtle" size="sm" :label="__('Add Attribute')" iconLeft="plus" @click="addVariantAttribute" />
              </div>
              <div v-for="(attribute, index) in form.variant_attributes" :key="index" class="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                <TextInput v-model="attribute.attribute_name" :disabled="isExistingVariant" :placeholder="__('Attribute (for example, Color)')" />
                <TextInput v-model="attribute.attribute_value" :disabled="isExistingVariant" :placeholder="__('Value (for example, Red)')" />
                <Button v-if="!isExistingVariant" variant="subtle" icon="trash-2" :aria-label="__('Remove attribute')" @click="removeVariantAttribute(index)" />
              </div>
              <span v-if="fieldErrors.variant_attributes" class="block text-xs text-red-600">{{ fieldErrors.variant_attributes }}</span>
              <span v-if="isExistingVariant" class="block text-xs text-ink-gray-5">{{ __('Variant template and attributes cannot be changed after creation.') }}</span>
            </div>
          </div>
          <label class="space-y-1 sm:col-span-2">
            <span class="text-sm text-ink-gray-7">{{ __('Description') }}</span>
            <textarea v-model="form.description" rows="3" class="w-full rounded border border-outline-gray-2 bg-surface-white px-3 py-2 text-sm" />
          </label>
        </div>

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
import { Button, Dialog, Popover, TextInput, call } from 'frappe-ui'

const props = defineProps({
  product: { type: Object, default: null },
  categories: { type: Array, default: () => [] },
  templates: { type: Array, default: () => [] },
})
const emit = defineEmits(['saved', 'reload-latest'])
const show = defineModel({ type: Boolean })
const submitting = ref(false)
const error = ref('')
const fieldErrors = reactive({})
const needsReload = ref(false)
const form = reactive({
  product_name: '',
  sku: '',
  product_kind: 'Standard',
  category: '',
  categories: [],
  variant_of: '',
  variant_attributes: [],
  price: 0,
  description: '',
  is_active: true,
})

const isEditMode = computed(() => Boolean(props.product?.name))
const isExistingVariant = computed(() => isEditMode.value && props.product?.product_kind === 'Variant')
const availableTemplates = computed(() => props.templates.filter((template) => template.name !== props.product?.name))
const selectedCategories = computed(() => uniqueCategories([form.category, ...form.categories]).map((name) => {
  const category = props.categories.find((item) => item.name === name)
  return { name, label: category?.category_name || name }
}))

watch(show, (isOpen) => {
  if (!isOpen) return
  populateForm()
})

watch(() => props.product, () => {
  if (show.value) populateForm()
})

function populateForm() {
  error.value = ''
  clearFieldErrors()
  needsReload.value = false
  Object.assign(form, {
    product_name: props.product?.product_name || '',
    sku: props.product?.sku || '',
    product_kind: props.product?.product_kind || 'Standard',
    category: props.product?.category || '',
    categories: uniqueCategories([
      ...(props.product?.categories || []).map((row) => row.category),
      props.product?.category,
    ]),
    variant_of: props.product?.variant_of || '',
    variant_attributes: (props.product?.variant_attributes || []).map((row) => ({
      attribute_name: row.attribute_name || '',
      attribute_value: row.attribute_value || '',
    })),
    price: props.product?.price ?? 0,
    description: props.product?.description || '',
    is_active: props.product ? isActive(props.product.is_active) : true,
  })
}

function isActive(value) {
  return value === 1 || value === '1' || value === true
}

function validate() {
  clearFieldErrors()
  if (!form.product_name.trim()) fieldErrors.product_name = __('Product Name is required.')
  if (!form.category) fieldErrors.category = __('Primary Category is required.')
  if (form.price === '' || Number.isNaN(Number(form.price)) || Number(form.price) < 0) {
    fieldErrors.price = __('Price must be a nonnegative number.')
  }
  if (form.product_kind === 'Variant') {
    if (!form.variant_of) fieldErrors.variant_of = __('Template is required for a Variant.')
    const attributes = form.variant_attributes.filter((row) => row.attribute_name.trim() || row.attribute_value.trim())
    const names = new Set()
    if (!attributes.length || attributes.some((row) => !row.attribute_name.trim() || !row.attribute_value.trim())) {
      fieldErrors.variant_attributes = __('Add at least one complete attribute and value.')
    } else if (attributes.some((row) => {
      const name = row.attribute_name.trim().toLocaleLowerCase()
      if (names.has(name)) return true
      names.add(name)
      return false
    })) {
      fieldErrors.variant_attributes = __('Each Variant Attribute can only be used once.')
    }
  }
  return Object.values(fieldErrors)[0] || ''
}

async function saveProduct() {
  if (submitting.value) return
  error.value = validate()
  if (error.value) return

  submitting.value = true
  const fields = {
    product_name: form.product_name.trim(),
    category: form.category,
    categories: uniqueCategories([...form.categories, form.category]).map((category) => ({ category })),
    product_kind: form.product_kind,
    variant_of: form.product_kind === 'Variant' ? form.variant_of : null,
    variant_attributes: form.product_kind === 'Variant'
      ? form.variant_attributes.map((row) => ({
          attribute_name: row.attribute_name.trim(),
          attribute_value: row.attribute_value.trim(),
        }))
      : [],
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

function clearFieldErrors() {
  Object.keys(fieldErrors).forEach((key) => delete fieldErrors[key])
}

function uniqueCategories(categories) {
  return [...new Set(categories.filter(Boolean))]
}

function ensurePrimaryCategory() {
  form.categories = uniqueCategories([...form.categories, form.category])
}

function isCategorySelected(category) {
  return form.categories.includes(category) || form.category === category
}

function toggleCategory(category, selected) {
  if (category === form.category) return
  form.categories = selected
    ? uniqueCategories([...form.categories, category])
    : form.categories.filter((name) => name !== category)
}

function removeCategory(category) {
  if (category !== form.category) toggleCategory(category, false)
}

function handleKindChange() {
  clearFieldErrors()
  if (form.product_kind !== 'Variant') {
    form.variant_of = ''
    form.variant_attributes = []
  } else if (!form.variant_attributes.length) {
    addVariantAttribute()
  }
}

function addVariantAttribute() {
  form.variant_attributes.push({ attribute_name: '', attribute_value: '' })
}

function removeVariantAttribute(index) {
  form.variant_attributes.splice(index, 1)
}

function reloadLatest() {
  emit('reload-latest', props.product?.name)
}
</script>
