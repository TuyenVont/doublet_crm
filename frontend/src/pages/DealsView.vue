<template>
  <div class="flex flex-col h-full overflow-hidden bg-surface-white">
    <!-- Layout Header: Teleports to #app-header -->
    <LayoutHeader>
      <template #left-header>
        <ViewBreadcrumbs routeName="Deals" />
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

    <!-- Filter & Control Bar matching Frappe CRM ViewControls styling -->
    <div class="flex items-center justify-between gap-2 px-5 py-3 border-b border-outline-gray-2/60 bg-surface-white">
      <div class="flex flex-1 items-center gap-2">
        <!-- Search Input -->
        <div class="relative w-64">
          <TextInput
            v-model="searchQuery"
            type="search"
            :placeholder="__('Search deals...')"
          >
            <template #prefix>
              <FeatherIcon name="search" class="h-4 w-4 text-ink-gray-4" />
            </template>
          </TextInput>
        </div>

        <!-- Stage Filter Dropdown -->
        <Dropdown :options="stageDropdownOptions">
          <template #default="{ open }">
            <Button
              variant="subtle"
              :label="selectedStage ? selectedStage : __('All Stages')"
              :iconRight="open ? 'chevron-up' : 'chevron-down'"
            >
              <template #prefix>
                <FilterIcon class="h-4 w-4" />
              </template>
            </Button>
          </template>
        </Dropdown>
      </div>

      <!-- Right controls: Refresh -->
      <div class="flex items-center gap-2">
        <Button
          :tooltip="__('Refresh')"
          :icon="RefreshIcon"
          :loading="dealsResource.loading"
          @click="reload"
        />
      </div>
    </div>

    <!-- Main List Container -->
    <div class="flex-1 overflow-hidden relative">
      <div
        v-if="dealsResource.loading && !filteredRows.length"
        class="flex h-64 items-center justify-center text-sm text-ink-gray-5"
      >
        <div class="flex items-center gap-2">
          <LoadingIndicator class="size-5" />
          <span>{{ __('Loading deals...') }}</span>
        </div>
      </div>

      <DealsListView
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
        name="Deals"
        :title="__('No Deals Found')"
        :description="__('No DoubleT deals match the selected criteria.')"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import DealsListView from '@/components/ListViews/FrappeDealsListView.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'
import FilterIcon from '@/components/Icons/FilterIcon.vue'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'
import { useDoubleTDeals } from '@/composables/useDoubleTDeals'
import { Button, TextInput, Dropdown, FeatherIcon } from 'frappe-ui'

const { stages, dealsResource, columns, rows, totalCount, reload, loadMore } = useDoubleTDeals()

const searchQuery = ref('')
const selectedStage = ref('')

const stageDropdownOptions = computed(() => {
  const options = [
    {
      label: __('All Stages'),
      onClick: () => {
        selectedStage.value = ''
      },
    },
  ]
  stages.value.forEach((stage) => {
    options.push({
      label: stage.stage_name || stage.name,
      onClick: () => {
        selectedStage.value = stage.stage_name || stage.name
      },
    })
  })
  return options
})

const filteredRows = computed(() => {
  let res = rows.value
  if (selectedStage.value) {
    res = res.filter((r) => r.stage?.label === selectedStage.value)
  }
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    res = res.filter((r) => {
      return (
        String(r.deal_title || '').toLowerCase().includes(q) ||
        String(r.company || '').toLowerCase().includes(q) ||
        String(r.contact || '').toLowerCase().includes(q) ||
        String(r.name || '').toLowerCase().includes(q)
      )
    })
  }
  return res
})

function openDeskCreate() {
  window.open('/app/doublet-deal/new', '_blank')
}
</script>
