<template>
  <section class="rounded-xl border border-outline-gray-2 bg-surface-white p-4" :aria-label="__('Report filters')">
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_1.2fr_auto] lg:items-end">
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
        <span class="mb-1.5 block text-sm font-medium text-ink-gray-7">{{ __('Salesperson (Deal Owner)') }}</span>
        <select
          :value="salesperson"
          class="h-9 w-full rounded border border-outline-gray-2 bg-surface-white px-3 text-sm text-ink-gray-9"
          :disabled="loading || !salespersonSupported"
          @change="$emit('update:salesperson', $event.target.value)"
        >
          <option value="">{{ __('All salespeople') }}</option>
          <option v-for="option in salespersonOptions" :key="option.value" :value="option.value">
            {{ option.label }}
          </option>
        </select>
        <span v-if="!salespersonSupported" class="mt-1 block text-xs text-ink-gray-5">
          {{ __('Deal ownership is unavailable with your permissions.') }}
        </span>
      </label>
      <div class="flex flex-wrap gap-2">
        <Button variant="solid" :label="__('Apply')" :loading="loading" :disabled="Boolean(validationError)" @click="$emit('apply')" />
        <Button :label="__('Reset')" :disabled="loading" @click="$emit('reset')" />
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
    <p v-if="validationError" class="mt-2 text-sm text-ink-red-3">{{ __(validationError) }}</p>
  </section>
</template>

<script setup>
import { computed } from 'vue'

import { reportDateError, reportDatePreset } from '@/utils/reportFilters'

const props = defineProps({
  startDate: { type: String, required: true },
  endDate: { type: String, required: true },
  salesperson: { type: String, default: '' },
  salespersonOptions: { type: Array, default: () => [] },
  salespersonSupported: { type: Boolean, default: true },
  loading: { type: Boolean, default: false },
})
const emit = defineEmits([
  'update:startDate',
  'update:endDate',
  'update:salesperson',
  'apply',
  'reset',
])

const presets = [
  { value: '7-days', label: '7 days' },
  { value: '30-days', label: '30 days' },
  { value: 'this-month', label: 'This month' },
]

const validationError = computed(() => reportDateError(props.startDate, props.endDate))

function setPreset(preset) {
  const range = reportDatePreset(preset)
  emit('update:startDate', range.startDate)
  emit('update:endDate', range.endDate)
}
</script>
