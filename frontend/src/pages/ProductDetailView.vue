<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <Button variant="subtle" :label="__('Products')" @click="router.push({ name: 'Products' })" />
        <span class="ml-2 truncate text-base font-semibold text-ink-gray-9">
          {{ product?.product_name || product?.name || __('Product') }}
        </span>
      </template>
      <template #right-header>
        <Button
          v-if="product && canWrite"
          variant="solid"
          :label="__('Edit Product')"
          :loading="optionsLoading"
          :disabled="Boolean(optionsError)"
          @click="showProductModal = true"
        />
      </template>
    </LayoutHeader>

    <div class="flex-1 overflow-auto p-5">
      <div v-if="loading" class="flex h-48 items-center justify-center text-sm text-ink-gray-5">
        {{ __('Loading Product...') }}
      </div>
      <div v-else-if="error" class="mx-auto max-w-xl space-y-3 pt-8">
        <ErrorMessage :message="error" />
        <Button variant="subtle" :label="__('Retry')" @click="loadProduct()" />
      </div>
      <div v-else-if="product" class="mx-auto w-full max-w-6xl space-y-6">
        <div v-if="optionsError" class="flex flex-wrap items-center justify-between gap-3 rounded-md border border-outline-gray-2 p-3">
          <ErrorMessage :message="optionsError" />
          <Button variant="subtle" :label="__('Retry supporting data')" :loading="optionsLoading" @click="loadSupportingOptions" />
        </div>

        <section class="grid gap-6 rounded-lg border border-outline-gray-2 p-5 md:grid-cols-[minmax(220px,320px)_1fr]">
          <ProductThumbnail
            class="aspect-square w-full"
            :src="resolvedImage.url"
            :alt="product.product_name || product.name"
          />

          <div class="min-w-0 space-y-5">
            <div>
              <div class="flex flex-wrap items-center gap-2">
                <h1 class="text-2xl font-semibold text-ink-gray-9">{{ product.product_name || product.name }}</h1>
                <span class="rounded-full bg-surface-gray-2 px-2.5 py-1 text-xs text-ink-gray-7">{{ product.product_kind || __('Standard') }}</span>
                <span class="rounded-full px-2.5 py-1 text-xs" :class="isActive(product) ? 'bg-green-50 text-green-700' : 'bg-surface-gray-2 text-ink-gray-5'">
                  {{ isActive(product) ? __('Active') : __('Inactive') }}
                </span>
              </div>
              <p class="mt-1 text-sm text-ink-gray-5">{{ __('SKU') }}: {{ product.sku || product.name }}</p>
              <p v-if="resolvedImage.source === 'template'" class="mt-2 text-xs text-ink-gray-5">{{ __('Using the linked Template image.') }}</p>
            </div>

            <dl class="grid gap-4 sm:grid-cols-2">
              <div>
                <dt class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">{{ __('Base Price') }}</dt>
                <dd class="mt-1 text-lg font-semibold text-ink-gray-9">{{ formatCurrency(product.price || 0) }}</dd>
              </div>
              <div v-if="product.product_kind === 'Variant' && product.variant_of">
                <dt class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">{{ __('Template') }}</dt>
                <dd class="mt-1">
                  <button class="text-sm font-medium text-ink-gray-8 hover:underline" @click="openProduct(product.variant_of)">
                    {{ templateLabel(product.variant_of) }}
                  </button>
                </dd>
              </div>
            </dl>

            <div>
              <h2 class="text-sm font-medium text-ink-gray-7">{{ __('Categories') }}</h2>
              <div v-if="productCategories.length" class="mt-2 flex flex-wrap gap-2">
                <span v-for="category in productCategories" :key="category.name" class="rounded-full bg-surface-gray-2 px-2.5 py-1 text-xs text-ink-gray-7">
                  {{ category.label }}<span v-if="category.primary" class="ml-1 text-ink-gray-5">· {{ __('Primary') }}</span>
                </span>
              </div>
              <p v-else class="mt-1 text-sm text-ink-gray-5">—</p>
            </div>

            <div>
              <h2 class="text-sm font-medium text-ink-gray-7">{{ __('Description') }}</h2>
              <p class="mt-1 whitespace-pre-wrap text-sm leading-6 text-ink-gray-6">{{ product.description || __('No description.') }}</p>
            </div>
          </div>
        </section>

        <section v-if="product.product_kind === 'Template'" class="overflow-hidden rounded-lg border border-outline-gray-2">
          <div class="flex items-center justify-between border-b border-outline-gray-2 px-5 py-4">
            <div>
              <h2 class="text-lg font-semibold text-ink-gray-9">{{ __('Variants') }}</h2>
              <p class="text-sm text-ink-gray-5">{{ __('Products linked to this Template.') }}</p>
            </div>
            <Button v-if="variantsError" variant="subtle" :label="__('Retry')" :loading="variantsLoading" @click="loadVariants(product.name)" />
          </div>

          <div v-if="variantsLoading" class="p-8 text-center text-sm text-ink-gray-5">{{ __('Loading Variants...') }}</div>
          <div v-else-if="variantsError" class="p-5"><ErrorMessage :message="variantsError" /></div>
          <div v-else-if="!variants.length" class="p-8 text-center text-sm text-ink-gray-5">{{ __('This Template has no Variants.') }}</div>
          <div v-else class="overflow-x-auto">
            <table class="w-full min-w-[720px] text-left text-sm">
              <thead class="bg-surface-gray-1 text-ink-gray-6">
                <tr>
                  <th class="px-4 py-3 font-medium">{{ __('Variant') }}</th>
                  <th class="px-4 py-3 font-medium">{{ __('SKU') }}</th>
                  <th class="px-4 py-3 font-medium">{{ __('Attributes') }}</th>
                  <th class="px-4 py-3 text-right font-medium">{{ __('Price') }}</th>
                  <th class="px-4 py-3 font-medium">{{ __('Status') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="variant in variants"
                  :key="variant.name"
                  class="cursor-pointer border-t border-outline-gray-2 hover:bg-surface-gray-1"
                  @click="openProduct(variant.name)"
                >
                  <td class="px-4 py-3 font-medium text-ink-gray-9">{{ variant.product_name || variant.name }}</td>
                  <td class="px-4 py-3 text-ink-gray-6">{{ variant.sku || variant.name }}</td>
                  <td class="px-4 py-3 text-ink-gray-6">{{ variantAttributeLabel(variant.name) }}</td>
                  <td class="px-4 py-3 text-right text-ink-gray-8">{{ formatCurrency(variant.price || 0) }}</td>
                  <td class="px-4 py-3" :class="isActive(variant) ? 'text-green-600' : 'text-ink-gray-5'">
                    {{ isActive(variant) ? __('Active') : __('Inactive') }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>

    <ProductModal
      v-if="product"
      v-model="showProductModal"
      :product="product"
      :categories="categories"
      :templates="templates"
      :can-edit-image="canWrite"
      @saved="handleSaved"
      @reload-latest="loadProduct"
    />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Button, call } from 'frappe-ui'

import LayoutHeader from '@/components/LayoutHeader.vue'
import ProductModal from '@/components/Modals/ProductModal.vue'
import ProductThumbnail from '@/components/ProductThumbnail.vue'
import { formatCurrency } from '@/utils'
import { groupVariantAttributes, hasProductWritePermission, productDetailLocation, resolveProductImage } from '@/utils/productCatalog'

const props = defineProps({ productId: { type: String, default: '' } })
const route = useRoute()
const router = useRouter()

const product = ref(null)
const loading = ref(true)
const error = ref('')
const canWrite = ref(false)
const showProductModal = ref(false)
const categories = ref([])
const templates = ref([])
const optionsLoading = ref(false)
const optionsError = ref('')
const variants = ref([])
const variantAttributes = ref({})
const variantsLoading = ref(false)
const variantsError = ref('')
let productRequestId = 0
let variantsRequestId = 0
let optionsRequestId = 0

const currentProductId = computed(() => String(route.params.productId || props.productId || ''))
const resolvedImage = computed(() => resolveProductImage(product.value, templates.value))
const productCategories = computed(() => {
  if (!product.value) return []
  const names = [product.value.category, ...(product.value.categories || []).map((row) => row.category)]
  return [...new Set(names.filter(Boolean))].map((name) => ({
    name,
    label: categoryLabel(name),
    primary: name === product.value.category,
  }))
})

function errorMessage(exception, fallback) {
  return exception?.messages?.[0] || exception?.message || fallback
}

function isActive(row) {
  return row?.is_active === 1 || row?.is_active === '1' || row?.is_active === true
}

function categoryLabel(name) {
  const category = categories.value.find((row) => row.name === name)
  return category?.category_name || name
}

function templateLabel(name) {
  const template = templates.value.find((row) => row.name === name)
  return template?.product_name || name
}

function variantAttributeLabel(name) {
  const attributes = variantAttributes.value[name] || []
  return attributes.length ? attributes.map((row) => `${row.name}: ${row.value}`).join(' · ') : '—'
}

function openProduct(name) {
  if (name) router.push(productDetailLocation(name))
}

async function loadProduct(name = currentProductId.value) {
  const productName = String(name || currentProductId.value || '')
  const requestId = ++productRequestId
  variantsRequestId += 1
  loading.value = true
  error.value = ''
  canWrite.value = false
  showProductModal.value = false
  product.value = null
  variants.value = []
  variantAttributes.value = {}
  variantsLoading.value = false
  variantsError.value = ''

  try {
    const document = await call('frappe.client.get', {
      doctype: 'DoubleT Product',
      name: productName,
    })
    if (requestId !== productRequestId) return
    product.value = document

    call('frappe.client.get_doc_permissions', {
      doctype: 'DoubleT Product',
      docname: productName,
    }).then((permissions) => {
      if (requestId === productRequestId) canWrite.value = hasProductWritePermission(permissions)
    }).catch(() => {
      if (requestId === productRequestId) canWrite.value = false
    })

    void loadSupportingOptions()
    if (document.product_kind === 'Template') void loadVariants(document.name)
  } catch (exception) {
    if (requestId === productRequestId) {
      error.value = errorMessage(exception, __('Unable to load this Product. Check your access and try again.'))
    }
  } finally {
    if (requestId === productRequestId) loading.value = false
  }
}

async function loadSupportingOptions() {
  const requestId = ++optionsRequestId
  optionsLoading.value = true
  optionsError.value = ''
  const results = await Promise.allSettled([
    call('frappe.client.get_list', {
      doctype: 'DoubleT Product Category',
      fields: ['name', 'category_name'],
      order_by: 'category_name asc',
      limit_page_length: 500,
    }),
    call('frappe.client.get_list', {
      doctype: 'DoubleT Product',
      fields: ['name', 'product_name', 'sku', 'image', 'is_active'],
      filters: { product_kind: 'Template' },
      order_by: 'product_name asc',
      limit_page_length: 500,
    }),
  ])
  if (requestId !== optionsRequestId) return
  if (results[0].status === 'fulfilled') categories.value = results[0].value || []
  if (results[1].status === 'fulfilled') templates.value = results[1].value || []
  if (results.some((result) => result.status === 'rejected')) {
    optionsError.value = __('Some Product supporting data could not be loaded. Detail values remain visible, but editing may be unavailable.')
  }
  optionsLoading.value = false
}

async function loadVariants(templateName) {
  const requestId = ++variantsRequestId
  variantsLoading.value = true
  variantsError.value = ''
  variants.value = []
  variantAttributes.value = {}
  try {
    const rows = await call('frappe.client.get_list', {
      doctype: 'DoubleT Product',
      fields: ['name', 'product_name', 'sku', 'price', 'is_active'],
      filters: { product_kind: 'Variant', variant_of: templateName },
      order_by: 'product_name asc',
      limit_page_length: 500,
    })
    if (requestId !== variantsRequestId || product.value?.name !== templateName) return
    const visibleVariants = Array.isArray(rows) ? rows : []
    const names = visibleVariants.map((row) => row.name).filter(Boolean)
    let attributes = []
    if (names.length) {
      attributes = await call('frappe.client.get_list', {
        doctype: 'DoubleT Product Variant Attribute',
        parent: 'DoubleT Product',
        fields: ['parent', 'attribute_name', 'attribute_value', 'idx'],
        filters: [
          ['parent', 'in', names],
          ['parenttype', '=', 'DoubleT Product'],
          ['parentfield', '=', 'variant_attributes'],
        ],
        order_by: 'parent asc, idx asc',
        limit_page_length: 5000,
      })
    }
    if (requestId !== variantsRequestId || product.value?.name !== templateName) return
    variants.value = visibleVariants
    variantAttributes.value = groupVariantAttributes(attributes)
  } catch (exception) {
    if (requestId === variantsRequestId) {
      variantsError.value = errorMessage(exception, __('Unable to load Variants.'))
    }
  } finally {
    if (requestId === variantsRequestId) variantsLoading.value = false
  }
}

async function handleSaved() {
  await loadProduct(currentProductId.value)
}

watch(currentProductId, (name) => {
  if (name) void loadProduct(name)
}, { immediate: true })
</script>
