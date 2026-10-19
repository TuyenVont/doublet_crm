<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">

    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Leads" />
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

    <!-- Controls -->
    <div
      class="flex items-center justify-between gap-2 border-b border-outline-gray-2/60 bg-surface-white px-5 py-3"
    >
      <div class="flex flex-1 items-center gap-2">

        <!-- Search -->
        <div class="relative w-64">
          <TextInput
            v-model="searchQuery"
            type="search"
            :placeholder="__('Search leads...')"
          >
            <template #prefix>
              <FeatherIcon
                name="search"
                class="h-4 w-4 text-ink-gray-4"
              />
            </template>
          </TextInput>
        </div>

        <!-- Status -->
        <Dropdown :options="statusDropdownOptions">
          <template #default="{ open }">
            <Button
              variant="subtle"
              :label="
                selectedStatus
                  ? selectedStatus
                  : __('All Statuses')
              "
              :iconRight="
                open ? 'chevron-up' : 'chevron-down'
              "
            >
              <template #prefix>
                <FilterIcon class="h-4 w-4" />
              </template>
            </Button>
          </template>
        </Dropdown>

        <!-- Source -->
        <Dropdown :options="sourceDropdownOptions">
          <template #default="{ open }">
            <Button
              variant="subtle"
              :label="
                selectedSource
                  ? selectedSource
                  : __('All Sources')
              "
              :iconRight="
                open ? 'chevron-up' : 'chevron-down'
              "
            />
          </template>
        </Dropdown>

      </div>

      <!-- Refresh -->
      <div class="flex items-center gap-2">
        <Button
          :tooltip="__('Refresh')"
          :icon="RefreshIcon"
          :loading="leadsResource.loading"
          @click="reload"
        />
      </div>
    </div>

    <!-- List -->
    <div class="relative flex-1 overflow-hidden">

      <div
        v-if="
          leadsResource.loading &&
          !filteredRows.length
        "
        class="flex h-64 items-center justify-center text-sm text-ink-gray-5"
      >
        <div class="flex items-center gap-2">
          <LoadingIndicator class="size-5" />
          <span>{{ __('Loading leads...') }}</span>
        </div>
      </div>

      <LeadsListView
        v-else-if="filteredRows.length"
        :rows="filteredRows"
        :columns="columns"
        :options="{
          selectable: true,
          showTooltip: true,
          resizeColumn: true,
        }"
        @loadMore="loadMore"
      />

      <EmptyState
        v-else
        name="Leads"
        :title="__('No Leads Found')"
        :description="
          __('No DoubleT leads match the selected criteria.')
        "
      />
    </div>

  </div>
</template>

<script setup>
import { computed, ref } from 'vue'

import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import LeadsListView from '@/components/ListViews/FrappeLeadsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'

import FilterIcon from '@/components/Icons/FilterIcon.vue'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'

import { useDoubleTLeads } from '@/composables/useDoubleTLeads'

import {
  Button,
  TextInput,
  Dropdown,
  FeatherIcon,
} from 'frappe-ui'

const {
  leadsResource,
  columns,
  rows,
  totalCount,
  reload,
  loadMore,
} = useDoubleTLeads()

const searchQuery = ref('')
const selectedStatus = ref('')
const selectedSource = ref('')

const statuses = [
  'NEW',
  'CONTACTED',
  'NURTURE',
  'QUALIFIED',
  'CONVERTED',
  'UNQUALIFIED',
  'JUNK',
]

const statusDropdownOptions = computed(() => {
  return [
    {
      label: __('All Statuses'),
      onClick: () => {
        selectedStatus.value = ''
      },
    },

    ...statuses.map((status) => ({
      label: status,
      onClick: () => {
        selectedStatus.value = status
      },
    })),
  ]
})

const availableSources = computed(() => {
  return [
    ...new Set(
      rows.value
        .map((row) => row.source)
        .filter(
          (value) =>
            value &&
            value !== '-'
        )
    ),
  ]
})

const sourceDropdownOptions = computed(() => {
  return [
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
  ]
})

const filteredRows = computed(() => {
  let result = rows.value

  if (selectedStatus.value) {
    result = result.filter(
      (row) =>
        row.status?.label === selectedStatus.value
    )
  }

  if (selectedSource.value) {
    result = result.filter(
      (row) =>
        row.source === selectedSource.value
    )
  }

  if (searchQuery.value.trim()) {
    const query =
      searchQuery.value
        .trim()
        .toLowerCase()

    result = result.filter((row) => {
      return (
        String(row.full_name || '')
          .toLowerCase()
          .includes(query) ||

        String(row.email || '')
          .toLowerCase()
          .includes(query) ||

        String(row.company_name || '')
          .toLowerCase()
          .includes(query) ||

        String(row.phone || '')
          .toLowerCase()
          .includes(query) ||

        String(row.name || '')
          .toLowerCase()
          .includes(query)
      )
    })
  }

  return result
})

function openDeskCreate() {
  window.open(
    '/app/doublet-lead/new',
    '_blank'
  )
}
</script>
