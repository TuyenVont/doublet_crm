<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header><ViewBreadcrumbs routeName="PriceLists" /></template>
      <template #right-header>
        <Button variant="solid" :label="__('Create Price List')" iconLeft="plus" @click="openCreate" />
      </template>
    </LayoutHeader>

    <div class="flex flex-wrap items-center gap-2 border-b border-outline-gray-2/60 px-5 py-3">
      <div class="w-full sm:w-72">
        <TextInput v-model="searchQuery" type="search" :placeholder="__('Search Price Lists...')">
          <template #prefix><FeatherIcon name="search" class="h-4 w-4 text-ink-gray-4" /></template>
        </TextInput>
      </div>
      <Dropdown :options="statusOptions">
        <template #default="{ open }">
          <Button variant="subtle" :label="statusLabel" :iconRight="open ? 'chevron-up' : 'chevron-down'" />
        </template>
      </Dropdown>
      <Button class="ml-auto" :tooltip="__('Refresh')" icon="refresh-cw" :loading="priceListsResource.loading" @click="reload" />
    </div>

    <div class="relative flex-1 overflow-auto p-5">
      <div v-if="priceListsResource.loading && !priceLists.length" class="flex h-48 items-center justify-center text-sm text-ink-gray-5">
        {{ __('Loading Price Lists...') }}
      </div>
      <div v-else-if="resourceError" class="mx-auto max-w-xl pt-8"><ErrorMessage :message="resourceError" /></div>
      <template v-else-if="priceLists.length">
        <ErrorMessage v-if="actionError" class="mb-4" :message="actionError" />
        <div class="overflow-x-auto rounded border border-outline-gray-2">
          <table class="w-full min-w-[720px] text-sm">
            <thead class="bg-surface-gray-1 text-left text-ink-gray-6">
              <tr>
                <th class="px-4 py-3 font-medium">{{ __('Price List') }}</th>
                <th class="px-4 py-3 font-medium">{{ __('Default') }}</th>
                <th class="px-4 py-3 font-medium">{{ __('Status') }}</th>
                <th class="px-4 py-3 font-medium">{{ __('Last Modified') }}</th>
                <th class="w-28 px-4 py-3"><span class="sr-only">{{ __('Actions') }}</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="priceList in priceLists" :key="priceList.name" class="cursor-pointer border-t border-outline-gray-2 hover:bg-surface-gray-1" @click="openEdit(priceList)">
                <td class="px-4 py-3 font-medium text-ink-gray-9">{{ priceList.price_list_name || priceList.name }}</td>
                <td class="px-4 py-3 text-ink-gray-6">{{ isDefault(priceList) ? __('Default') : '—' }}</td>
                <td class="px-4 py-3"><span :class="isActive(priceList) ? 'text-green-600' : 'text-ink-gray-5'">{{ isActive(priceList) ? __('Active') : __('Inactive') }}</span></td>
                <td class="px-4 py-3 text-ink-gray-6">{{ priceList.modified || '—' }}</td>
                <td class="px-4 py-3 text-right"><Button variant="subtle" :label="__('Edit')" @click.stop="openEdit(priceList)" /></td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
      <EmptyState v-else name="Price Lists" :title="__('No Price Lists Found')" :description="__('Create a Price List to set Product and Variant prices for customers.')" />
    </div>

    <div v-if="priceLists.length && priceListsResource.hasNextPage" class="border-t border-outline-gray-2 px-5 py-3 text-center">
      <Button variant="subtle" :label="__('Load More')" :loading="priceListsResource.loading" @click="loadMore" />
    </div>

    <PriceListModal v-model="showModal" :price-list="selectedPriceList" @saved="handleSaved" />
  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Button, Dropdown, FeatherIcon, TextInput, call } from 'frappe-ui'

import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import PriceListModal from '@/components/Modals/PriceListModal.vue'
import { useDoubleTPriceLists } from '@/composables/useDoubleTPriceLists'

const { priceListsResource, setFilters, reload, loadMore } = useDoubleTPriceLists()
const searchQuery = ref('')
const selectedStatus = ref('')
const selectedPriceList = ref(null)
const showModal = ref(false)
const actionError = ref('')
const priceLists = computed(() => priceListsResource.data || [])
const resourceError = computed(() => {
  const error = priceListsResource.error
  return error?.messages?.[0] || error?.message || error || ''
})
const statusOptions = computed(() => [
  { label: __('All Statuses'), onClick: () => { selectedStatus.value = '' } },
  { label: __('Active'), onClick: () => { selectedStatus.value = 'active' } },
  { label: __('Inactive'), onClick: () => { selectedStatus.value = 'inactive' } },
])
const statusLabel = computed(() => selectedStatus.value === 'active' ? __('Active') : selectedStatus.value === 'inactive' ? __('Inactive') : __('All Statuses'))

watch([searchQuery, selectedStatus], () => {
  setFilters({ search: searchQuery.value, status: selectedStatus.value })
})

function isActive(priceList) {
  return priceList.is_active === 1 || priceList.is_active === '1' || priceList.is_active === true
}

function isDefault(priceList) {
  return priceList.is_default === 1 || priceList.is_default === '1' || priceList.is_default === true
}

function openCreate() {
  actionError.value = ''
  selectedPriceList.value = null
  showModal.value = true
}

async function openEdit(priceList) {
  if (!priceList?.name) return
  actionError.value = ''
  try {
    selectedPriceList.value = await call('frappe.client.get', { doctype: 'DoubleT Price List', name: priceList.name })
    showModal.value = true
  } catch (error) {
    actionError.value = error?.messages?.[0] || error?.message || __('Unable to load the latest Price List.')
  }
}

function handleSaved() {
  reload()
}
</script>
