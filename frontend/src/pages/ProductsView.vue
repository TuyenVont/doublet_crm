<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Products" />
      </template>
      <template #right-header>
        <Button variant="subtle" :label="__('Manage Categories')" @click="router.push({ name: 'ProductCategories' })" />
        <Button variant="solid" :label="__('Create Product')" iconLeft="plus" :loading="openingProduct" @click="openCreate" />
      </template>
    </LayoutHeader>

    <div class="flex flex-wrap items-center gap-2 border-b border-outline-gray-2/60 px-5 py-3">
      <div class="w-full sm:w-64">
        <TextInput v-model="searchQuery" type="search" :placeholder="__('Search product name or SKU...')">
          <template #prefix>
            <FeatherIcon name="search" class="h-4 w-4 text-ink-gray-4" />
          </template>
        </TextInput>
      </div>
      <Dropdown :options="categoryOptions">
        <template #default="{ open }">
          <Button variant="subtle" :label="selectedCategory || __('All Categories')" :iconRight="open ? 'chevron-up' : 'chevron-down'" />
        </template>
      </Dropdown>
      <Dropdown :options="statusOptions">
        <template #default="{ open }">
          <Button variant="subtle" :label="selectedStatusLabel" :iconRight="open ? 'chevron-up' : 'chevron-down'" />
        </template>
      </Dropdown>
      <Button class="ml-auto" :tooltip="__('Refresh')" icon="refresh-cw" :loading="productsResource.loading" @click="reload" />
    </div>

    <div class="px-5 pt-2 text-xs text-ink-gray-5">
      {{ __('Search and filters apply to products loaded in this list.') }}
    </div>

    <div class="relative flex-1 overflow-auto p-5">
      <div v-if="productsResource.loading && !products.length" class="flex h-48 items-center justify-center text-sm text-ink-gray-5">
        {{ __('Loading products...') }}
      </div>
      <div v-else-if="resourceError" class="mx-auto max-w-xl pt-8">
        <ErrorMessage :message="resourceError" />
      </div>
      <template v-else-if="filteredProducts.length">
        <ErrorMessage v-if="actionError" class="mb-4" :message="actionError" />
        <div class="overflow-x-auto rounded border border-outline-gray-2">
        <table class="w-full min-w-[760px] text-sm">
          <thead class="bg-surface-gray-1 text-left text-ink-gray-6">
            <tr>
              <th class="px-4 py-3 font-medium">{{ __('Product Name') }}</th>
              <th class="px-4 py-3 font-medium">{{ __('SKU') }}</th>
              <th class="px-4 py-3 font-medium">{{ __('Category') }}</th>
              <th class="px-4 py-3 text-right font-medium">{{ __('Price') }}</th>
              <th class="px-4 py-3 font-medium">{{ __('Status') }}</th>
              <th class="w-40 px-4 py-3"><span class="sr-only">{{ __('Actions') }}</span></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="product in filteredProducts" :key="product.name" class="cursor-pointer border-t border-outline-gray-2 hover:bg-surface-gray-1" @click="openEdit(product)">
              <td class="px-4 py-3 font-medium text-ink-gray-9">{{ product.product_name || product.name }}</td>
              <td class="px-4 py-3 text-ink-gray-6">{{ product.sku }}</td>
              <td class="px-4 py-3 text-ink-gray-6">{{ product.category }}</td>
              <td class="px-4 py-3 text-right text-ink-gray-8">{{ formatCurrency(product.price || 0) }}</td>
              <td class="px-4 py-3">
                <span :class="isActive(product) ? 'text-green-600' : 'text-ink-gray-5'">
                  {{ isActive(product) ? __('Active') : __('Inactive') }}
                </span>
              </td>
              <td class="px-4 py-3 text-right">
                <Button variant="subtle" :label="__('Edit')" @click.stop="openEdit(product)" />
                <Button variant="subtle" :label="__('Delete')" :loading="deletingName === product.name" @click.stop="deleteProduct(product)" />
              </td>
            </tr>
          </tbody>
        </table>
        </div>
      </template>
      <EmptyState
        v-else
        name="Products"
        :title="__('No Products Found')"
        :description="__('No DoubleT products match the selected criteria.')"
      />
    </div>

    <div v-if="products.length" class="border-t border-outline-gray-2 px-5 py-3 text-center">
      <Button variant="subtle" :label="__('Load More')" :loading="productsResource.loading" @click="loadMore" />
    </div>

    <ProductModal v-model="showProductModal" :product="selectedProduct" @saved="handleSaved" @reload-latest="openEditByName" />
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Button, Dropdown, FeatherIcon, TextInput, call } from 'frappe-ui'

import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import ProductModal from '@/components/Modals/ProductModal.vue'
import { useDoubleTProducts } from '@/composables/useDoubleTProducts'
import { formatCurrency } from '@/utils'

const { productsResource, reload, loadMore } = useDoubleTProducts()
const router = useRouter()
const searchQuery = ref('')
const selectedCategory = ref('')
const selectedStatus = ref('')
const selectedProduct = ref(null)
const showProductModal = ref(false)
const openingProduct = ref(false)
const deletingName = ref('')
const actionError = ref('')

const products = computed(() => productsResource.data || [])
const resourceError = computed(() => {
  const error = productsResource.error
  return error?.messages?.[0] || error?.message || error || ''
})
const categories = computed(() => [...new Set(products.value.map((product) => product.category).filter(Boolean))])
const categoryOptions = computed(() => [
  { label: __('All Categories'), onClick: () => { selectedCategory.value = '' } },
  ...categories.value.map((category) => ({ label: category, onClick: () => { selectedCategory.value = category } })),
])
const statusOptions = computed(() => [
  { label: __('All Statuses'), onClick: () => { selectedStatus.value = '' } },
  { label: __('Active'), onClick: () => { selectedStatus.value = 'active' } },
  { label: __('Inactive'), onClick: () => { selectedStatus.value = 'inactive' } },
])
const selectedStatusLabel = computed(() => {
  if (selectedStatus.value === 'active') return __('Active')
  if (selectedStatus.value === 'inactive') return __('Inactive')
  return __('All Statuses')
})
const filteredProducts = computed(() => {
  const query = searchQuery.value.trim().toLowerCase()
  return products.value.filter((product) => {
    const matchesCategory = !selectedCategory.value || product.category === selectedCategory.value
    const matchesStatus = !selectedStatus.value || (selectedStatus.value === 'active' ? isActive(product) : !isActive(product))
    const matchesSearch = !query || [product.product_name, product.sku].some((value) => String(value || '').toLowerCase().includes(query))
    return matchesCategory && matchesStatus && matchesSearch
  })
})

function isActive(product) {
  return product.is_active === 1 || product.is_active === '1' || product.is_active === true
}

async function openCreate() {
  actionError.value = ''
  openingProduct.value = true
  try {
    const sku = await call('doublet_crm.doublet_crm.doctype.doublet_product.doublet_product.get_suggested_sku')
    selectedProduct.value = { sku }
    showProductModal.value = true
  } catch (error) {
    actionError.value = error?.messages?.[0] || error?.message || __('Unable to suggest a SKU. Leave it blank to generate one when saving.')
    selectedProduct.value = null
    showProductModal.value = true
  } finally {
    openingProduct.value = false
  }
}

async function openEdit(product) {
  if (!product?.name) return
  actionError.value = ''
  openingProduct.value = true
  try {
    selectedProduct.value = await call('frappe.client.get', {
      doctype: 'DoubleT Product',
      name: product.name,
    })
    showProductModal.value = true
  } catch (error) {
    actionError.value = error?.messages?.[0] || error?.message || __('Unable to load the latest Product. Please refresh and try again.')
  } finally {
    openingProduct.value = false
  }
}

function openEditByName(name) {
  openEdit({ name })
}

function handleSaved() {
  reload()
}

async function deleteProduct(product) {
  if (!window.confirm(__('Delete this product? Linked records will not be deleted.'))) return

  actionError.value = ''
  deletingName.value = product.name
  try {
    await call('frappe.client.delete', { doctype: 'DoubleT Product', name: product.name })
    reload()
  } catch (error) {
    actionError.value = error?.messages?.[0] || error?.message || __('Unable to delete product because it is referenced by another record.')
  } finally {
    deletingName.value = ''
  }
}
</script>
