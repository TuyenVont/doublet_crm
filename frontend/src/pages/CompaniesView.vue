<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Companies" />
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
            :placeholder="__('Search companies...')"
          >
            <template #prefix>
              <FeatherIcon name="search" class="h-4 w-4 text-ink-gray-4" />
            </template>
          </TextInput>
        </div>

        <Dropdown :options="industryDropdownOptions">
          <template #default="{ open }">
            <Button
              variant="subtle"
              :label="selectedIndustry || __('All Industries')"
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
        :loading="companiesResource.loading"
        @click="reload"
      />
    </div>

    <div class="relative flex-1 overflow-hidden">
      <div
        v-if="companiesResource.loading && !filteredRows.length"
        class="flex h-64 items-center justify-center text-sm text-ink-gray-5"
      >
        <LoadingIndicator class="mr-2 size-5" />
        {{ __('Loading companies...') }}
      </div>

      <DealsListView
        v-else-if="filteredRows.length"
        doctype="DoubleT Company"
        detailRoute="CompanyDetail"
        detailParam="companyId"
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
        name="Companies"
        :title="__('No Companies Found')"
        :description="__('No DoubleT companies match the selected criteria.')"
      />
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
const router = useRouter()

import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import DealsListView from '@/components/ListViews/DealsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'

import FilterIcon from '@/components/Icons/FilterIcon.vue'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'

import { useDoubleTCompanies } from '@/composables/useDoubleTCompanies'

import {
  Button,
  TextInput,
  Dropdown,
  FeatherIcon,
} from 'frappe-ui'

const {
  companiesResource,
  columns,
  rows,
  totalCount,
  reload,
  loadMore,
} = useDoubleTCompanies()

const searchQuery = ref('')
const selectedIndustry = ref('')

const industries = computed(() => [
  ...new Set(
    rows.value
      .map((row) => row.industry)
      .filter((value) => value && value !== '-')
  ),
])

const industryDropdownOptions = computed(() => [
  {
    label: __('All Industries'),
    onClick: () => {
      selectedIndustry.value = ''
    },
  },

  ...industries.value.map((industry) => ({
    label: industry,
    onClick: () => {
      selectedIndustry.value = industry
    },
  })),
])

const filteredRows = computed(() => {
  let result = rows.value

  if (selectedIndustry.value) {
    result = result.filter(
      (row) => row.industry === selectedIndustry.value
    )
  }

  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()

    result = result.filter((row) => {
      return (
        String(row.company_name || '').toLowerCase().includes(q) ||
        String(row.industry || '').toLowerCase().includes(q) ||
        String(row.email || '').toLowerCase().includes(q) ||
        String(row.phone || '').toLowerCase().includes(q)
      )
    })
  }

  return result
})

function openDeskCreate() {
  router.push({ name: 'CompanyCreate' })
}
</script>
