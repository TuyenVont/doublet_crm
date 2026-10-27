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
            @click="setViewMode('list')"
          />

          <Button
            icon="columns"
            variant="ghost"
            :class="viewMode === 'kanban' ? 'bg-surface-gray-2' : ''"
            :tooltip="__('Kanban View')"
            @click="setViewMode('kanban')"
          />
        </div>

        <!-- Refresh -->
        <Button
          :tooltip="__('Refresh')"
          :icon="RefreshIcon"
          :loading="dealsResource.loading"
          @click="reload"
        />
      </div>
    </div>

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
        :disabled="!lostReason.trim()"
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
  columns,
  rows,
  reload,
  loadMore,
} = useDoubleTDeals()

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
const selectedStage = ref('')

const pendingMove = ref(null)

const showLostModal = ref(false)
const showWonModal = ref(false)

const lostReason = ref('')
const savingMove = ref(false)

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
      __('All Stages')
    )
  })

/*
 * Raw Deals dành cho Kanban
 */
const rawDeals = computed(() => {
  let result =
    dealsResource.data || []

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

/*
 * Drag Deal
 */
async function handleDealMove(
  move,
) {
  const targetStage =
    stages.value.find(
      (stage) =>
        stage.name === move.to,
    )

  if (!targetStage) {
    await reload()
    return
  }

  const stageType =
    String(
      targetStage.stage_type ||
        '',
    ).toUpperCase()

  /*
   * LOST
   */
  if (stageType === 'LOST') {
    pendingMove.value = move
    lostReason.value = ''
    showLostModal.value = true
    return
  }

  /*
   * WON
   */
  if (stageType === 'WON') {
    pendingMove.value = move
    showWonModal.value = true
    return
  }

  /*
   * Normal Stage
   */
  await saveDealMove(
    move,
    'NORMAL',
  )
}

/*
 * Save Deal Stage
 */
async function saveDealMove(
  move,
  terminalType = 'NORMAL',
  reason = '',
) {
  if (!move) {
    return
  }

  savingMove.value = true

  try {
    const result = await call(
      'doublet_crm.api.update_deal_stage',
      {
        deal_name: move.item,
        stage: move.to,

        lost_reason:
          terminalType === 'LOST'
            ? reason.trim()
            : null,
      },
    )

    /*
     * Update local resource.
     * Không reload khi thành công
     * để tránh Kanban bị giật.
     */
    const deal =
      dealsResource.data?.find(
        (item) =>
          item.name === move.item,
      )

    if (deal) {
      Object.assign(
        deal,
        result || {
          stage: move.to,
        },
      )

      /*
       * Đảm bảo local Stage luôn đúng
       * ngay cả khi backend không
       * return stage.
       */
      deal.stage = move.to

      if (
        terminalType === 'LOST'
      ) {
        deal.lost_reason =
          reason.trim()
      }

      if (
        terminalType === 'NORMAL'
      ) {
        deal.lost_reason = null
      }
    }

    closeMoveDialogs()
  } catch (error) {
    console.error(
      'Deal stage update failed:',
      error,
    )

    /*
     * API lỗi -> lấy lại dữ liệu DB
     * để card quay về Stage cũ.
     */
    await reload()

    closeMoveDialogs()

    const message =
      error?.message ||
      'Không thể cập nhật Deal Stage.'

    window.alert(message)
  } finally {
    savingMove.value = false
  }
}

/*
 * Confirm LOST
 */
async function confirmLost() {
  if (
    !lostReason.value.trim()
  ) {
    return
  }

  await saveDealMove(
    pendingMove.value,
    'LOST',
    lostReason.value,
  )
}

/*
 * Confirm WON
 */
async function confirmWon() {
  await saveDealMove(
    pendingMove.value,
    'WON',
  )
}

/*
 * Cancel WON / LOST
 *
 * Card đã bị draggable đưa
 * sang column mới ở UI,
 * nhưng database chưa thay đổi.
 *
 * Reload để đưa card về Stage cũ.
 */
async function cancelPendingMove() {
  showLostModal.value = false
  showWonModal.value = false

  pendingMove.value = null
  lostReason.value = ''

  await reload()
}

/*
 * Close Modal
 */
function closeMoveDialogs() {
  showLostModal.value = false
  showWonModal.value = false

  pendingMove.value = null
  lostReason.value = ''
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