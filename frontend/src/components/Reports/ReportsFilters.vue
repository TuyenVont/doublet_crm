<template>
  <section class="rounded-xl border border-outline-gray-2 bg-surface-white p-4" :aria-label="__('Report filters')">
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1.2fr)_11rem] lg:items-end">
      <label class="block">
        <span class="mb-1.5 block text-sm font-medium text-ink-gray-7">{{ __('Start Date') }}</span>
        <input
          :value="startDate"
          type="date"
          class="h-9 w-full rounded border border-outline-gray-2 bg-surface-white px-3 text-sm text-ink-gray-9"
          :disabled="loading"
          @input="$emit('update:startDate', $event.target.value)"
        />
      </label>
      <label class="block">
        <span class="mb-1.5 block text-sm font-medium text-ink-gray-7">{{ __('End Date') }}</span>
        <input
          :value="endDate"
          type="date"
          class="h-9 w-full rounded border border-outline-gray-2 bg-surface-white px-3 text-sm text-ink-gray-9"
          :disabled="loading"
          @input="$emit('update:endDate', $event.target.value)"
        />
      </label>
      <label class="block">
        <span class="mb-1.5 block text-sm font-medium text-ink-gray-7">{{ __(personLabel) }}</span>
        <select
          :value="salesperson"
          class="h-9 w-full rounded border border-outline-gray-2 bg-surface-white px-3 text-sm text-ink-gray-9"
          :disabled="loading || !salespersonSupported"
          @change="$emit('update:salesperson', $event.target.value)"
        >
          <option value="">{{ __(allPeopleLabel) }}</option>
          <option v-for="option in salespersonOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <span v-if="!salespersonSupported && personUnsupportedText" class="mt-1 block text-xs text-ink-gray-5">
          {{ __(personUnsupportedText) }}
        </span>
      </label>
      <div class="flex flex-nowrap gap-2">
        <Button class="w-24 shrink-0" variant="solid" :label="__('Apply')" :aria-busy="loading" :aria-disabled="loading || Boolean(validationError)" :disabled="Boolean(validationError)" @click="apply" />
        <Button class="w-16 shrink-0" :label="__('Reset')" :aria-disabled="loading" @click="reset" />
      </div>
    </div>

    <div class="mt-3 flex flex-wrap items-center gap-2">
      <span class="text-xs font-medium text-ink-gray-5">{{ __('Presets') }}:</span>
      <button
        v-for="preset in presets"
        :key="preset.value"
        type="button"
        class="rounded-md bg-surface-gray-2 px-2.5 py-1 text-xs font-medium text-ink-gray-7 hover:bg-surface-gray-3 disabled:cursor-not-allowed disabled:opacity-50"
        :disabled="loading"
        @click="setPreset(preset.value)"
      >
        {{ __(preset.label) }}
      </button>
    </div>
    <div v-if="showCompare || teamUnsupportedReason" class="mt-3 flex flex-wrap items-center justify-between gap-3 border-t border-outline-gray-1 pt-3">
      <label v-if="showCompare" class="inline-flex items-center gap-2 text-sm text-ink-gray-7">
        <input
          :checked="comparePrevious"
          type="checkbox"
          class="size-4 rounded border-outline-gray-3"
          :disabled="loading"
          @change="$emit('update:comparePrevious', $event.target.checked)"
        />
        {{ __('Compare with immediately preceding equal-length period') }}
      </label>
      <span v-if="teamUnsupportedReason" class="text-xs text-ink-gray-5" role="status">
        {{ teamUnsupportedReason }}
      </span>
    </div>
    <p v-if="validationError" class="mt-2 text-sm text-ink-red-3">{{ __(validationError) }}</p>
    <ReportActions
      v-if="reportKey"
      class="mt-3"
      :report-key="reportKey"
      :filters="exportFilters"
      :enabled="exportEnabled"
      @restore="$emit('restore', $event)"
    />
  </section>
</template>

<script setup>
import { computed } from 'vue'

import ReportActions from '@/components/Reports/ReportActions.vue'
import { reportDateError, reportDatePreset } from '@/utils/reportFilters'

const props = defineProps({
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  salesperson: { type: String, default: '' },
  salespersonOptions: { type: Array, default: () => [] },
  salespersonSupported: { type: Boolean, default: true },
  personLabel: { type: String, default: 'Salesperson (Deal Owner)' },
  allPeopleLabel: { type: String, default: 'All salespeople' },
  personUnsupportedText: { type: String, default: 'Deal ownership is unavailable with your permissions.' },
  showCompare: { type: Boolean, default: true },
  comparePrevious: { type: Boolean, default: false },
  teamUnsupportedReason: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  reportKey: { type: String, default: '' },
  exportFilters: { type: Object, default: () => ({}) },
  exportEnabled: { type: Boolean, default: false },
})
const emit = defineEmits([
  'update:startDate',
  'update:endDate',
  'update:salesperson',
  'update:comparePrevious',
  'apply',
  'reset',
  'restore',
])

const presets = [
  { value: '7-days', label: '7 days' },
  { value: '30-days', label: '30 days' },
  { value: 'this-month', label: 'This month' },
  { value: 'previous-month', label: 'Previous month' },
  { value: 'this-quarter', label: 'This quarter' },
  { value: 'previous-quarter', label: 'Previous quarter' },
]

const validationError = computed(() => reportDateError(props.startDate, props.endDate))

function setPreset(preset) {
  const range = reportDatePreset(preset)
  emit('update:startDate', range.startDate)
  emit('update:endDate', range.endDate)
}

function apply() {
  if (props.loading || validationError.value) return
  emit('apply')
}

function reset() {
  if (props.loading) return
  emit('reset')
}
</script>
