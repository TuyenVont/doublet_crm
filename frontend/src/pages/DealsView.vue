<template>
  <div class="flex h-full flex-col overflow-hidden bg-surface-white">
    <!-- Header -->
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

    <!-- Controls -->
    <div
      class="flex items-center justify-between gap-2 border-b border-outline-gray-2/60 bg-surface-white px-5 py-3"
    >
      <!-- Left -->
      <div class="flex flex-1 items-center gap-2">
        <!-- Search -->
        <div class="relative w-64">
          <TextInput
            v-model="searchQuery"
            type="search"
            :placeholder="__('Search deals...')"
          >
            <template #prefix>
              <FeatherIcon
                name="search"
                class="h-4 w-4 text-ink-gray-4"
              />
            </template>
          </TextInput>
        </div>

        <!-- Stage Filter -->
        <Dropdown :options="stageDropdownOptions">
          <template #default="{ open }">
            <Button
              variant="subtle"
              :label="selectedStageLabel"
              :iconRight="open ? 'chevron-up' : 'chevron-down'"
            >
              <template #prefix>
                <FilterIcon class="h-4 w-4" />
              </template>
            </Button>
          </template>
        </Dropdown>
      </div>

      <!-- Right -->
      <div class="flex items-center gap-2">
        <!-- View Mode -->
        <div
          class="flex items-center rounded-lg border border-outline-gray-2 bg-surface-white p-1"
        >
          <Button
            icon="list"
            variant="ghost"
            :class="viewMode === 'list' ? 'bg-surface-gray-2' : ''"
            :tooltip="__('List View')"
            :disabled="!!pendingMove"
            @click="setViewMode('list')"
          />

          <Button
            icon="columns"
            variant="ghost"
            :class="viewMode === 'kanban' ? 'bg-surface-gray-2' : ''"
            :tooltip="__('Kanban View')"
            :disabled="!!pendingMove"
            @click="setViewMode('kanban')"
          />
        </div>

        <!-- Refresh -->
        <Button
          :tooltip="__('Refresh')"
          :icon="RefreshIcon"
          :loading="dealsResource.loading"
          :disabled="!!pendingMove"
          @click="reload"
        />
      </div>
    </div>

    <p
      v-if="moveError"
      role="alert"
      class="border-b border-red-200 bg-red-50 px-5 py-2 text-sm text-red-700"
    >
      {{ moveError }}
    </p>

    <!-- Main -->
    <div class="relative flex-1 overflow-hidden">
      <!-- Loading -->
      <div
        v-if="dealsResource.loading && !dealsResource.data?.length"
        class="flex h-64 items-center justify-center text-sm text-ink-gray-5"
      >
        <div class="flex items-center gap-2">
          <LoadingIndicator class="size-5" />
          <span>{{ __('Loading deals...') }}</span>
        </div>
      </div>

      <!-- Kanban -->
      <DoubleTDealKanban
        v-else-if="viewMode === 'kanban'"
        :stages="stages"
        :deals="rawDeals"
        @create="openDeskCreate"
        @move="handleDealMove"
      />

      <!-- List -->
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

      <!-- Empty -->
      <EmptyState
        v-else
        name="Deals"
        :title="__('No Deals Found')"
        :description="__('No DoubleT deals match the selected criteria.')"
      />
    </div>
    <!-- LOST MODAL -->
<div
  v-if="showLostModal"
  class="fixed inset-0 z-[100] flex items-center justify-center bg-black/35 px-4 py-6"
  @click.self="cancelPendingMove"
>
  <div
    class="w-full max-w-[720px] overflow-hidden rounded-2xl bg-white shadow-2xl"
  >
    <!-- Header -->
    <div class="flex items-center gap-4 border-b border-outline-gray-2 px-7 py-6">
      <div
        class="flex size-12 shrink-0 items-center justify-center rounded-xl bg-red-50"
      >
        <FeatherIcon
          name="x-circle"
          class="size-6 text-red-600"
        />
      </div>

      <div>
        <h2 class="text-xl font-semibold text-ink-gray-9">
          {{ __('Mark Deal as Lost') }}
        </h2>

        <p class="mt-1 text-sm text-ink-gray-5">
          {{ __('Enter the reason this deal was lost.') }}
        </p>
      </div>
    </div>

    <!-- Body -->
    <div class="px-7 py-6">
      <label class="mb-2 block text-sm font-medium text-ink-gray-8">
        {{ __('Lost Reason') }}
        <span class="text-red-500">*</span>
      </label>

      <textarea
        v-model="lostReason"
        rows="7"
        autofocus
        maxlength="500"
        class="w-full resize-none rounded-xl border border-outline-gray-2 bg-white px-4 py-3 text-sm text-ink-gray-9 outline-none transition focus:border-red-400 focus:ring-2 focus:ring-red-100"
        :placeholder="__('Example: Budget issue, competitor selected, no response...')"
      />

      <div class="mt-2 flex justify-between text-xs text-ink-gray-4">
        <span>{{ __('Required') }}</span>
        <span>{{ lostReason.length }}/500</span>
      </div>
    </div>

    <!-- Footer -->
    <div
      class="flex items-center justify-end gap-3 border-t border-outline-gray-2 bg-surface-gray-1 px-7 py-5"
    >
      <Button
        :label="__('Cancel')"
        variant="subtle"
        :disabled="savingMove"
        @click="cancelPendingMove"
      />

      <Button
        :label="__('Mark as Lost')"
        variant="solid"
        :loading="savingMove"
        :disabled="savingMove || !lostReason.trim()"
        class="!bg-red-600 !text-white hover:!bg-red-700 disabled:!bg-red-300"
        @click="confirmLost"
      />
    </div>
  </div>
</div>


<!-- WON MODAL -->
<div
  v-if="showWonModal"
  class="fixed inset-0 z-[100] flex items-center justify-center bg-black/35 px-4 py-6"
  @click.self="cancelPendingMove"
>
  <div
    class="w-full max-w-[680px] overflow-hidden rounded-2xl bg-white shadow-2xl"
  >
    <!-- Header -->
    <div class="flex items-center gap-4 border-b border-outline-gray-2 px-7 py-6">
      <div
        class="flex size-12 shrink-0 items-center justify-center rounded-xl bg-green-50"
      >
        <FeatherIcon
          name="check-circle"
          class="size-6 text-green-600"
        />
      </div>

      <div>
        <h2 class="text-xl font-semibold text-ink-gray-9">
          {{ __('Mark Deal as Won') }}
        </h2>

        <p class="mt-1 text-sm text-ink-gray-5">
          {{ __('Confirm that this deal has been successfully closed.') }}
        </p>
      </div>
    </div>

    <!-- Body -->
    <div class="px-7 py-6">
      <div
        class="rounded-xl border border-green-200 bg-green-50 px-5 py-4"
      >
        <div class="flex items-start gap-3">
          <FeatherIcon
            name="check"
            class="mt-0.5 size-5 shrink-0 text-green-600"
          />

          <div>
            <div class="text-sm font-medium text-green-900">
              {{ __('Deal completed successfully') }}
            </div>

            <div class="mt-1 text-sm leading-5 text-green-700">
              {{
                __('The deal will move to Won and the won date will be recorded automatically.')
              }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div
      class="flex items-center justify-end gap-3 border-t border-outline-gray-2 bg-surface-gray-1 px-7 py-5"
    >
      <Button
        :label="__('Cancel')"
        variant="subtle"
        :disabled="savingMove"
        @click="cancelPendingMove"
      />

      <Button
        :label="__('Mark as Won')"
        variant="solid"
        :loading="savingMove"
        :disabled="savingMove"
        class="!bg-green-600 !text-white hover:!bg-green-700"
        @click="confirmWon"
      />
    </div>
  </div>
</div>

 
    
  </div>
</template>

<script setup>
import {
  ref,
  computed,
} from 'vue'

import {
  Button,
  TextInput,
  Dropdown,
  FeatherIcon,
  call,
} from 'frappe-ui'

import {
  useRoute,
  useRouter,
} from 'vue-router'

import LayoutHeader from '@/components/LayoutHeader.vue'
import ViewBreadcrumbs from '@/components/ViewBreadcrumbs.vue'
import DealsListView from '@/components/ListViews/FrappeDealsListView.vue'
import DoubleTDealKanban from '@/components/DoubleTDealKanban.vue'
import EmptyState from '@/components/ListViews/EmptyState.vue'

import FilterIcon from '@/components/Icons/FilterIcon.vue'
import RefreshIcon from '@/components/Icons/RefreshIcon.vue'
import LoadingIndicator from '@/components/Icons/LoadingIndicator.vue'

import {
  useDoubleTDeals,
} from '@/composables/useDoubleTDeals'

const route = useRoute()
const router = useRouter()

const {
  stages,
  dealsResource,
  dealsWithLabels,
  columns,
  rows,
  reload,
  loadMore,
} = useDoubleTDeals({ lifecycle: route.query.lifecycle, stage: route.query.stage })

const VIEW_STORAGE_KEY =
  'doublet-deals-view-mode'

/*
 * Ưu tiên:
 * 1. query ?view=kanban
 * 2. view đã lưu trước đó
 * 3. list
 */
const storedView =
  window.localStorage.getItem(
    VIEW_STORAGE_KEY,
  )

const initialView =
  route.query.view === 'kanban'
    ? 'kanban'
    : storedView === 'kanban'
      ? 'kanban'
      : 'list'

const viewMode = ref(initialView)

const searchQuery = ref('')
const selectedStage = ref(String(route.query.stage || ''))

const pendingMove = ref(null)

const showLostModal = ref(false)
const showWonModal = ref(false)

const lostReason = ref('')
const savingMove = ref(false)
const moveError = ref('')

/*
 * List / Kanban
 */
function setViewMode(mode) {
  viewMode.value = mode

  window.localStorage.setItem(
    VIEW_STORAGE_KEY,
    mode,
  )

  const query = {
    ...route.query,
  }

  if (mode === 'kanban') {
    query.view = 'kanban'
  } else {
    delete query.view
  }

  router.replace({
    query,
  })
}

/*
 * Stage Filter
 */
const stageDropdownOptions =
  computed(() => {
    const options = [
      {
        label: __('All Stages'),

        onClick: () => {
          selectedStage.value = ''
        },
      },
    ]

    stages.value.forEach(
      (stage) => {
        options.push({
          label:
            stage.stage_name ||
            stage.name,

          onClick: () => {
            selectedStage.value =
              stage.name
          },
        })
      },
    )

    return options
  })

const selectedStageLabel =
  computed(() => {
    if (!selectedStage.value) {
      return __('All Stages')
    }

    const stage =
      stages.value.find(
        (item) =>
          item.name ===
          selectedStage.value,
      )

    return (
      stage?.stage_name ||
      stage?.name ||
      selectedStage.value ||
      __('All Stages')
    )
  })

/*
 * Raw Deals dành cho Kanban
 */
const rawDeals = computed(() => {
  let result = dealsWithLabels.value

  if (route.query.lifecycle) {
    const names = stages.value.filter((stage) => stage.stage_type === route.query.lifecycle).map((stage) => stage.name)
    result = result.filter((row) => names.includes(row.stage))
  }
  if (selectedStage.value) {
    result = result.filter(
      (deal) =>
        deal.stage ===
        selectedStage.value,
    )
  }

  const query =
    searchQuery.value
      .trim()
      .toLowerCase()

  if (query) {
    result = result.filter(
      (deal) => {
        return (
          String(
            deal.deal_title || '',
          )
            .toLowerCase()
            .includes(query) ||
          String(
            deal.company || '',
          )
            .toLowerCase()
            .includes(query) ||
          String(
            deal.contact || '',
          )
            .toLowerCase()
            .includes(query) ||
          String(
            deal.name || '',
          )
            .toLowerCase()
            .includes(query)
        )
      },
    )
  }

  return result
})

/*
 * List View
 */
const filteredRows =
  computed(() => {
    const allowedNames =
      new Set(
        rawDeals.value.map(
          (deal) => deal.name,
        ),
      )

    return rows.value.filter(
      (row) =>
        allowedNames.has(
          row.name,
        ),
    )
  })

async function handleDealMove(move) {
  const targetStage = stages.value.find((stage) => stage.name === move.to)
  if (!targetStage || pendingMove.value) {
    move.settle(false)
    return
  }

  pendingMove.value = move
  moveError.value = ''
  lostReason.value = ''
  const stageType = String(targetStage.stage_type || '').toUpperCase()

  if (stageType === 'LOST') {
    showLostModal.value = true
    return
  }

  if (stageType === 'WON') {
    showWonModal.value = true
    return
  }

  await saveDealMove(move)
}

async function saveDealMove(move, reason = null) {
  if (!move || savingMove.value) return

  savingMove.value = true
  let confirmed = false
  try {
    const result = await call('doublet_crm.api.update_deal_stage', {
      deal_name: move.item,
      stage: move.to,
      lost_reason: reason,
    })

    const deal = dealsResource.data?.find((item) => item.name === move.item)
    if (deal) {
      Object.assign(deal, { stage: move.to, lost_reason: reason }, result)
    }
    confirmed = true
  } catch (error) {
    moveError.value = error?.message || __('Could not update the deal stage.')
  } finally {
    finishDealMove(confirmed)
    savingMove.value = false
  }
}

async function confirmLost() {
  const reason = lostReason.value.trim()
  if (reason) await saveDealMove(pendingMove.value, reason)
}

async function confirmWon() {
  await saveDealMove(pendingMove.value)
}

function cancelPendingMove() {
  if (!savingMove.value) finishDealMove(false)
}

function finishDealMove(confirmed) {
  const move = pendingMove.value
  pendingMove.value = null
  showLostModal.value = false
  showWonModal.value = false
  lostReason.value = ''
  move?.settle(confirmed)
}

/*
 * Create Deal
 */
function openDeskCreate() {
  window.open(
    '/app/doublet-deal/new',
    '_blank',
  )
}
</script>
