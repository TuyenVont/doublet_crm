<template>
  <div class="h-full overflow-x-auto overflow-y-hidden bg-surface-gray-1">
    <div class="flex h-full min-w-max gap-1 px-3 py-3">
      <div
        v-for="column in localColumns"
        :key="column.name"
        class="flex h-full w-80 min-w-80 flex-col"
      >
        <div class="mb-2 px-2">
          <div class="flex items-center justify-between">
            <div class="flex min-w-0 items-center gap-2">
              <span
                class="size-2.5 shrink-0 rounded-full"
                :class="stageColor(column)"
              />

              <h3 class="truncate font-medium text-ink-gray-9">
                {{ column.label }}
              </h3>

              <span class="text-sm text-ink-gray-5">
                {{ column.deals.length }}
              </span>
            </div>

            <Button
              icon="plus"
              variant="ghost"
              size="sm"
              @click="$emit('create', column)"
            />
          </div>

          <div class="mt-2 text-sm font-medium text-ink-gray-8">
            {{ formatAmount(getColumnAmount(column)) }}
          </div>
        </div>

        <Draggable
          :list="column.deals"
          :disabled="movePending"
          item-key="name"
          group="doublet-deals"
          :data-stage="column.name"
          class="flex min-h-24 flex-1 flex-col gap-2 overflow-y-auto rounded-lg p-1.5"
          ghost-class="deal-ghost"
          chosen-class="deal-chosen"
          drag-class="deal-dragging"
          :animation="150"
          :scroll="true"
          :scroll-sensitivity="80"
          :scroll-speed="10"
          @start="onDragStart"
          @end="onDragEnd"
        >
          <template #item="{ element: deal }">
            <div
              :data-name="deal.name"
              class="group cursor-grab select-none rounded-lg border border-outline-gray-2 bg-surface-white px-3.5 py-3 shadow-sm transition-colors hover:border-outline-gray-4 active:cursor-grabbing"
              @click="openDeal(deal)"
            >
              <div class="flex items-start justify-between gap-2">
                <div class="min-w-0 flex-1">
                  <div class="truncate font-medium text-ink-gray-9">
                    {{ deal.deal_title || deal.name }}
                  </div>

                  <div class="mt-1 font-medium text-ink-gray-8">
                    {{ formatAmount(deal.amount) }}
                  </div>
                </div>

                <Button
                  icon="more-horizontal"
                  variant="ghost"
                  size="sm"
                  class="opacity-0 group-hover:opacity-100"
                  @click.stop
                />
              </div>

              <div
                v-if="deal.company || deal.contact"
                class="mt-2 truncate text-sm text-ink-gray-6"
              >
                {{
                  deal.company_label ||
                  deal.contact_label ||
                  deal.company ||
                  deal.contact
                }}
              </div>

              <div
                v-if="deal.deal_owner"
                class="mt-3 flex items-center gap-2 text-sm text-ink-gray-5"
              >
                <FeatherIcon name="user" class="size-3.5" />
                <span class="truncate">
                  {{ deal.deal_owner }}
                </span>
              </div>

              <div
                v-if="deal.expected_close_date"
                class="mt-2 flex items-center gap-2 text-sm text-ink-gray-5"
              >
                <FeatherIcon name="clock" class="size-3.5" />
                <span>{{ deal.expected_close_date }}</span>
              </div>
            </div>
          </template>

          <template #footer>
            <div
              v-if="!column.deals.length"
              class="flex min-h-20 items-center justify-center rounded-lg border border-dashed border-outline-gray-2 text-sm text-ink-gray-4"
            >
              {{ __('Drop deal here') }}
            </div>
          </template>
        </Draggable>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import Draggable from 'vuedraggable'
import { Button, FeatherIcon } from 'frappe-ui'

const props = defineProps({
  stages: {
    type: Array,
    default: () => [],
  },
  deals: {
    type: Array,
    default: () => [],
  },
})

const emit = defineEmits(['create', 'move'])

const router = useRouter()

const STORAGE_KEY = 'doublet-deal-kanban-order-v2'

const localColumns = ref([])
const dragging = ref(false)
const movePending = ref(false)
let savedOrder = loadOrder()

function loadOrder() {
  try {
    const order = JSON.parse(localStorage.getItem(STORAGE_KEY))
    return order && typeof order === 'object' && !Array.isArray(order) ? order : {}
  } catch {
    return {}
  }
}

function savedStageOrder(stageName) {
  const order = savedOrder[stageName]
  return Array.isArray(order) ? order : []
}

function rebuildColumns() {
  localColumns.value = props.stages.map((stage) => {
    const deals = props.deals
      .filter((deal) => deal.stage === stage.name)

    const order = savedStageOrder(stage.name)

    deals.sort((a, b) => {
      const ai = order.indexOf(a.name)
      const bi = order.indexOf(b.name)

      if (ai === -1 && bi === -1) return 0
      if (ai === -1) return 1
      if (bi === -1) return -1

      return ai - bi
    })

    return {
      name: stage.name,
      label: stage.stage_name || stage.name,
      stageType: stage.stage_type,
      color: stage.color,
      deals,
    }
  })
}

watch(
  () => [props.stages, props.deals],
  () => {
    if (!dragging.value && !movePending.value) rebuildColumns()
  },
  {
    immediate: true,
    deep: true,
  },
)

function getColumnAmount(column) {
  return column.deals.reduce((sum, deal) => sum + Number(deal.amount || 0), 0)
}

function saveOrder(from, to, dealName) {
  const order = { ...savedOrder }
  for (const column of localColumns.value) {
    if (column.name !== from && column.name !== to) continue

    const visibleNames = column.deals.map((deal) => deal.name)
    const visibleSet = new Set(visibleNames)
    const previous = new Set(savedStageOrder(column.name))
    if (from !== to && column.name === from) previous.delete(dealName)

    // Preserve the saved positions of cards hidden by a filter.
    let index = 0
    order[column.name] = Array.from(previous, (name) => {
      return visibleSet.has(name) ? visibleNames[index++] : name
    }).concat(visibleNames.slice(index))
  }

  savedOrder = order
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(savedOrder))
  } catch {
    // The current board still has its in-memory order.
  }
}

function onDragStart() {
  dragging.value = true
}

function onDragEnd(event) {
  const fromStage = event.from?.dataset?.stage
  const toStage = event.to?.dataset?.stage
  const dealName = event.item?.dataset?.name

  requestAnimationFrame(() => {
    dragging.value = false
    if (!movePending.value) rebuildColumns()
  })

  if (!dealName || !fromStage || !toStage) return

  if (fromStage === toStage) {
    if (event.oldDraggableIndex !== event.newDraggableIndex) {
      saveOrder(fromStage, toStage, dealName)
    }
    return
  }

  movePending.value = true
  emit('move', {
    item: dealName,
    to: toStage,
    async settle(confirmed) {
      if (confirmed) {
        saveOrder(fromStage, toStage, dealName)
        // Let the parent pass down the accepted stage and current filters.
        await nextTick()
      }
      movePending.value = false
      rebuildColumns()
    },
  })
}

function openDeal(deal) {
  if (dragging.value || movePending.value) return

  router.push({
    name: 'DealDetail',
    params: {
      dealId: deal.name,
    },
    query: {
      view: 'kanban',
    },
  })
}

function formatAmount(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value || 0))
}

function stageColor(column) {
  const type =
    String(column.stageType || '').toUpperCase()

  if (type === 'WON') return 'bg-green-500'
  if (type === 'LOST') return 'bg-red-500'

  return 'bg-blue-500'
}
</script>

<style scoped>
.deal-ghost {
  opacity: 0.22;
}

.deal-chosen {
  border-color: var(--outline-gray-4);
}

.deal-dragging {
  cursor: grabbing !important;
  opacity: 0.92;
  box-shadow: 0 8px 20px rgb(0 0 0 / 12%);
}
</style>
