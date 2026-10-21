<template>
  <ListView
    class="h-full overflow-hidden"
    :columns="columns"
    :rows="rows"
    :options="{
      selectable: options.selectable,
      showTooltip: options.showTooltip,
      resizeColumn: options.resizeColumn,
    }"
    row-key="name"
    @update:selections="(selections) => emit('selectionsChanged', selections)"
  >
    <ListHeader
      class="sm:mx-5 mx-3"
      @columnWidthUpdated="emit('columnWidthUpdated')"
    >
      <ListHeaderItem
        v-for="column in columns"
        :key="column.key"
        :item="column"
        @columnWidthUpdated="emit('columnWidthUpdated', column)"
      />
    </ListHeader>
    <ListRows
      v-slot="{ idx, column, item, row }"
      :rows="rows"
      :doctype="doctype"
    >
      <ListRowItem :item="item" :align="column.align" class="overflow-hidden">
        <template #prefix>
          <div v-if="column.key === 'stage'">
            <IndicatorIcon :class="item.color" />
          </div>
          <div v-else-if="column.key === 'deal_owner'">
            <Avatar
              v-if="item.full_name"
              class="flex items-center"
              :label="item.full_name"
              size="sm"
            />
          </div>
        </template>
        <template #default="{ label }">
          <div
            v-if="column.key === 'modified'"
            class="truncate text-base"
          >
            <Tooltip :text="item.label">
              <div>{{ item.timeAgo }}</div>
            </Tooltip>
          </div>
          <button
            v-else-if="label && column.key === columns[0]?.key && detailRoute"
            type="button"
            class="truncate text-left text-base hover:underline"
            @click.stop="openDetail(row.name)"
          >{{ label }}</button>
          <div v-else-if="label" class="truncate text-base">{{ label }}</div>
        </template>
      </ListRowItem>
    </ListRows>
    <ListSelectBanner>
      <template #actions="{ selections, unselectAll }">
        <Button
          variant="subtle"
          :label="__('Clear Selection')"
          @click="unselectAll"
        />
      </template>
    </ListSelectBanner>
  </ListView>
  <ListFooter
    v-if="rowCount"
    class="border-t sm:px-5 px-3 py-2"
    :options="{
      rowCount: rowCount,
      totalCount: totalCount,
    }"
    @loadMore="emit('loadMore')"
  />
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
function openDetail(name) {
  if (props.detailRoute && name) router.push({ name: props.detailRoute, params: { [props.detailParam]: name } })
}

import IndicatorIcon from '@/components/Icons/IndicatorIcon.vue'
import ListRows from '@/components/ListViews/ListRows.vue'
import {
  Avatar,
  ListView,
  ListHeader,
  ListHeaderItem,
  ListRowItem,
  ListSelectBanner,
  ListFooter,
  Tooltip,
  Button,
} from 'frappe-ui'

const props = defineProps({
  doctype: { type: String, default: 'DoubleT Deal' },
  detailRoute: { type: String, default: '' },
  detailParam: { type: String, default: 'id' },
  rows: { type: Array, required: true },
  columns: { type: Array, required: true },
  rowCount: { type: Number, default: 0 },
  totalCount: { type: Number, default: 0 },
  options: {
    type: Object,
    default: () => ({
      selectable: true,
      showTooltip: true,
      resizeColumn: false,
    }),
  },
})

const emit = defineEmits([
  'loadMore',
  'columnWidthUpdated',
  'selectionsChanged',
])
</script>
