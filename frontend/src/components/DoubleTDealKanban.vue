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
            {{ formatAmount(column.totalAmount) }}
          </div>
        </div>

        <Draggable
          :list="column.deals"
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
import { ref, watch } from 'vue'
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

function loadOrder() {
  try {
    return JSON.parse(
      localStorage.getItem(STORAGE_KEY) || '{}',
    )
  } catch {
    return {}
  }
}

function rebuildColumns() {
  const orderMap = loadOrder()

  localColumns.value = props.stages.map((stage) => {
    let deals = props.deals
      .filter((deal) => deal.stage === stage.name)
      .map((deal) => ({ ...deal }))

    const savedOrder = orderMap[stage.name] || []

    deals.sort((a, b) => {
      const ai = savedOrder.indexOf(a.name)
      const bi = savedOrder.indexOf(b.name)

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
      totalAmount: deals.reduce(
        (sum, deal) => sum + Number(deal.amount || 0),
        0,
      ),
    }
  })
}

watch(
  () => [props.stages, props.deals],
  rebuildColumns,
  {
    immediate: true,
    deep: true,
  },
)

function saveOrder() {
  const result = {}

  localColumns.value.forEach((column) => {
    result[column.name] =
      column.deals.map((deal) => deal.name)
  })

  localStorage.setItem(
    STORAGE_KEY,
    JSON.stringify(result),
  )
}

function onDragStart() {
  dragging.value = true
}

function onDragEnd(event) {
  const fromStage = event.from?.dataset?.stage
  const toStage = event.to?.dataset?.stage
  const dealName = event.item?.dataset?.name

  saveOrder()

  if (
    dealName &&
    fromStage &&
    toStage &&
    fromStage !== toStage
  ) {
    emit('move', {
      item: dealName,
      from: fromStage,
      to: toStage,
      oldIndex: event.oldIndex,
      newIndex: event.newIndex,
    })
  }

  requestAnimationFrame(() => {
    dragging.value = false
  })
}

function openDeal(deal) {
  if (dragging.value) return

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
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
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