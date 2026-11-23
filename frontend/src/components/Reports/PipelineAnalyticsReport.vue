<template>
  <div class="space-y-5">
    <ReportsFilters
      v-model:start-date="filters.startDate"
      v-model:end-date="filters.endDate"
      v-model:salesperson="filters.salesperson"
      :salesperson-options="salespeople"
      :salesperson-supported="true"
      :loading="loading"
      @apply="loadReport"
      @reset="resetFilters"
    />

    <div
      v-if="permissionDenied"
      class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center"
      role="alert"
    >
      <h2 class="font-semibold text-ink-gray-9">{{ __('Permission required') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">
        {{ __('You do not have permission to view pipeline analytics from Deals.') }}
      </p>
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center"
      role="alert"
    >
      <h2 class="font-semibold text-ink-gray-9">{{ __('Unable to load pipeline analytics') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ errorMessage }}</p>
      <Button class="mt-4" :label="__('Try again')" :loading="loading" @click="loadReport" />
    </div>

    <template v-else-if="data">
      <p class="rounded-lg bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6">
        {{ data.business_definition }}
      </p>

      <div
        v-if="data.permissions?.stages === false"
        class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6"
        role="status"
      >
        {{ __('Stage metadata is restricted. Lifecycle is derived from each readable Deal’s Won On and Lost On fields.') }}
      </div>

      <section class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" :aria-label="__('Pipeline summary')">
        <article class="rounded-xl border border-outline-gray-2 bg-surface-white p-4">
          <p class="text-sm text-ink-gray-5">{{ __('Deals created') }}</p>
          <p class="mt-2 text-2xl font-semibold text-ink-gray-9">{{ integer(data.deal_count) }}</p>
          <p class="mt-1 text-xs text-ink-gray-5">{{ money(data.total_deal_value) }} {{ __('total Deal value') }}</p>
        </article>
        <article class="rounded-xl border border-outline-gray-2 bg-surface-white p-4">
          <p class="text-sm text-ink-gray-5">{{ __('Open pipeline value') }}</p>
          <p class="mt-2 text-2xl font-semibold text-ink-blue-3">{{ money(data.open_pipeline_value) }}</p>
          <p class="mt-1 text-xs text-ink-gray-5">{{ integer(data.lifecycle.OPEN.deal_count) }} {{ __('Open Deals') }}</p>
        </article>
        <article class="rounded-xl border border-outline-gray-2 bg-surface-white p-4">
          <p class="text-sm text-ink-gray-5">{{ __('Won Deals') }}</p>
          <p class="mt-2 text-2xl font-semibold text-green-600">{{ integer(data.lifecycle.WON.deal_count) }}</p>
          <p class="mt-1 text-xs text-ink-gray-5">{{ money(data.lifecycle.WON.deal_value) }} {{ __('Deal value') }}</p>
        </article>
        <article class="rounded-xl border border-outline-gray-2 bg-surface-white p-4">
          <p class="text-sm text-ink-gray-5">{{ __('Lost Deals') }}</p>
          <p class="mt-2 text-2xl font-semibold text-ink-red-5">{{ integer(data.lifecycle.LOST.deal_count) }}</p>
          <p class="mt-1 text-xs text-ink-gray-5">{{ money(data.lifecycle.LOST.deal_value) }} {{ __('Deal value') }}</p>
        </article>
      </section>

      <div
        v-if="!data.deal_count"
        class="rounded-xl border border-dashed border-outline-gray-3 bg-surface-gray-1 px-5 py-12 text-center"
      >
        <h2 class="font-semibold text-ink-gray-9">{{ __('No Deals found') }}</h2>
        <p class="mt-1 text-sm text-ink-gray-5">
          {{ __('Try another Deal creation date range or Deal Owner.') }}
        </p>
      </div>

      <template v-else>
        <section class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5">
          <div class="mb-5">
            <h2 class="font-semibold text-ink-gray-9">{{ __('Deal value by stage') }}</h2>
            <p class="mt-1 text-sm text-ink-gray-5">
              {{ __('Select a stage to open its filtered Deals view.') }}
            </p>
          </div>
          <div class="space-y-4">
            <RouterLink
              v-for="stage in data.by_stage"
              :key="stage.name || stage.label"
              :to="stageRoute(stage)"
              class="group block rounded-lg p-2 transition hover:bg-surface-gray-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3"
            >
              <div class="flex flex-wrap items-center justify-between gap-2 text-sm">
                <div class="flex min-w-0 items-center gap-2">
                  <span class="size-2.5 shrink-0 rounded-full" :class="stageDotClass(stage.stage_type)" />
                  <span class="truncate font-medium text-ink-gray-8">{{ stage.label }}</span>
                  <span class="rounded px-1.5 py-0.5 text-xs font-medium" :class="stageBadgeClass(stage.stage_type)">
                    {{ stage.stage_type }}
                  </span>
                </div>
                <span class="text-ink-gray-6">
                  {{ integer(stage.deal_count) }} {{ __('Deals') }} · {{ money(stage.deal_value) }}
                </span>
              </div>
              <div class="mt-2 h-3 overflow-hidden rounded-full bg-surface-gray-2">
                <div
                  class="h-full rounded-full transition-all group-hover:opacity-80"
                  :class="stageBarClass(stage.stage_type)"
                  :style="{ width: barWidth(stage.deal_value) }"
                />
              </div>
            </RouterLink>
          </div>
        </section>

        <section class="overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white">
          <div class="p-4 sm:p-5">
            <h2 class="font-semibold text-ink-gray-9">{{ __('Recently created Deals') }}</h2>
            <p class="mt-1 text-sm text-ink-gray-5">{{ __('Latest 20 readable Deals in the applied filters') }}</p>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="border-y border-outline-gray-2 bg-surface-gray-1 text-ink-gray-5">
                <tr>
                  <th class="px-4 py-3 font-medium sm:px-5">{{ __('Deal') }}</th>
                  <th class="px-4 py-3 font-medium">{{ __('Stage') }}</th>
                  <th class="px-4 py-3 font-medium">{{ __('Deal Owner') }}</th>
                  <th class="px-4 py-3 font-medium">{{ __('Created') }}</th>
                  <th class="px-4 py-3 text-right font-medium sm:px-5">{{ __('Deal value') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-outline-gray-1">
                <tr v-for="deal in data.recent_deals" :key="deal.name">
                  <td class="max-w-64 px-4 py-3 sm:px-5">
                    <RouterLink
                      :to="{ name: 'DealDetail', params: { dealId: deal.name } }"
                      class="block truncate font-medium text-ink-blue-3 hover:underline"
                    >
                      {{ deal.deal_title || deal.name }}
                    </RouterLink>
                  </td>
                  <td class="whitespace-nowrap px-4 py-3">
                    <span class="inline-flex items-center gap-2 text-ink-gray-7">
                      <span class="size-2 rounded-full" :class="stageDotClass(deal.stage_type)" />
                      {{ deal.stage_label }}
                    </span>
                  </td>
                  <td class="whitespace-nowrap px-4 py-3 text-ink-gray-7">{{ deal.deal_owner || __('Unassigned') }}</td>
                  <td class="whitespace-nowrap px-4 py-3 text-ink-gray-7">{{ displayDate(deal.creation) }}</td>
                  <td class="whitespace-nowrap px-4 py-3 text-right font-medium text-ink-gray-8 sm:px-5">
                    {{ money(deal.amount) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </template>

    <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-live="polite">
      <div v-for="index in 4" :key="index" class="h-28 animate-pulse rounded-xl bg-surface-gray-2" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { call } from 'frappe-ui'

import ReportsFilters from '@/components/Reports/ReportsFilters.vue'
import { isPermissionError, reportDatePreset } from '@/utils/reportFilters'
import { message, money } from '@/utils/quotation'

const initialRange = reportDatePreset('30-days')
const filters = reactive({ ...initialRange, salesperson: '' })
const data = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const permissionDenied = ref(false)

const salespeople = computed(() => data.value?.salespeople || [])
const maxStageValue = computed(() => Math.max(...(data.value?.by_stage || []).map(stage => Number(stage.deal_value) || 0), 0))

function integer(value) {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(value) || 0)
}

function displayDate(value) {
  const date = String(value || '').slice(0, 10)
  if (!date) return ''
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${date}T00:00:00Z`))
}

function stageRoute(stage) {
  return stage.name ? { name: 'Deals', query: { stage: stage.name } } : { name: 'Deals' }
}

function barWidth(value) {
  if (!maxStageValue.value) return '2%'
  return `${Math.max((Number(value) / maxStageValue.value) * 100, 2)}%`
}

function stageDotClass(type) {
  return type === 'WON' ? 'bg-green-500' : type === 'LOST' ? 'bg-red-500' : 'bg-blue-500'
}

function stageBarClass(type) {
  return type === 'WON' ? 'bg-green-500' : type === 'LOST' ? 'bg-red-500' : 'bg-blue-500'
}

function stageBadgeClass(type) {
  return type === 'WON'
    ? 'bg-green-50 text-green-700'
    : type === 'LOST'
      ? 'bg-red-50 text-red-700'
      : 'bg-blue-50 text-blue-700'
}

async function loadReport() {
  loading.value = true
  errorMessage.value = ''
  permissionDenied.value = false
  try {
    data.value = await call('doublet_crm.reports.get_pipeline_analytics', {
      start_date: filters.startDate,
      end_date: filters.endDate,
      salesperson: filters.salesperson || null,
    })
  } catch (error) {
    data.value = null
    permissionDenied.value = isPermissionError(error)
    if (!permissionDenied.value) errorMessage.value = message(error)
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  Object.assign(filters, reportDatePreset('30-days'), { salesperson: '' })
  loadReport()
}

onMounted(loadReport)
</script>
