<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Contacts" />
      </template>

      <template #right-header>
        <Button
          variant="solid"
          :label="__('Create')"
          iconLeft="plus"
          @click="openDeskCreate"
        />
      </template>
    </LayoutHeader>

    <div
      class="flex items-center justify-between gap-2 border-b border-outline-gray-2/60 bg-surface-white px-5 py-3"
    >
      <div class="flex flex-1 items-center gap-2">
        <div class="w-64">
          <TextInput
            v-model="searchQuery"
            type="search"
            :placeholder="__('Search contacts...')"
          >
            <template #prefix>
              <FeatherIcon name="search" class="h-4 w-4 text-ink-gray-4" />
            </template>
          </TextInput>
        </div>

        <Dropdown :options="sourceDropdownOptions">
          <template #default="{ open }">
            <Button
              variant="subtle"
              :label="selectedSource || __('All Sources')"
              :iconRight="open ? 'chevron-up' : 'chevron-down'"
            >
              <template #prefix>
                <FilterIcon class="h-4 w-4" />
              </template>
            </Button>
          </template>
        </Dropdown>
      </div>

      <Button
        :tooltip="__('Refresh')"
        :icon="RefreshIcon"
        :loading="contactsResource.loading"
        @click="reload"
      />
    </div>

    <div class="relative flex-1 overflow-hidden">
      <div
        v-if="contactsResource.loading && !filteredRows.length"
        class="flex h-64 items-center justify-center text-sm text-ink-gray-5"
      >
        <LoadingIndicator class="mr-2 size-5" />
        {{ __('Loading contacts...') }}
      </div>

      <DealsListView
        v-else-if="filteredRows.length"
        :rows="filteredRows"
        :columns="columns"
        :rowCount="filteredRows.length"
        :totalCount="totalCount"
        :options="{
          selectable: true,
          showTooltip: true,
          resizeColumn: true,
        }"
        @loadMore="loadMore"
      />

      <EmptyState
        v-else
        name="Contacts"
        :title="__('No Contacts Found')"
        :description="__('No DoubleT contacts match the selected criteria.')"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'

import FilterIcon from '@/components/Icons/FilterIcon.vue'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'

import { useDoubleTContacts } from '@/composables/useDoubleTContacts'

import {
  Button,
  TextInput,
  Dropdown,
  FeatherIcon,
} from 'frappe-ui'

const {
  contactsResource,
  columns,
  rows,
  totalCount,
  reload,
  loadMore,
} = useDoubleTContacts()

const searchQuery = ref('')
const selectedSource = ref('')

const availableSources = computed(() => [
  ...new Set(
    rows.value
      .map((row) => row.source)
      .filter((value) => value && value !== '-')
  ),
])

const sourceDropdownOptions = computed(() => [
  {
    label: __('All Sources'),
    onClick: () => {
      selectedSource.value = ''
    },
  },

  ...availableSources.value.map((source) => ({
    label: source,
    onClick: () => {
      selectedSource.value = source
    },
  })),
])

const filteredRows = computed(() => {
  let result = rows.value

  if (selectedSource.value) {
    result = result.filter(
      (row) => row.source === selectedSource.value
    )
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()

    result = result.filter((row) => {
      return (
        String(row.full_name || '').toLowerCase().includes(q) ||
        String(row.company || '').toLowerCase().includes(q) ||
        String(row.email || '').toLowerCase().includes(q) ||
        String(row.phone || '').toLowerCase().includes(q)
      )
    })
  }

  return result
})

function openDeskCreate() {
  window.open('/app/doublet-contact/new', '_blank')
}
</script>
