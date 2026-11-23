<template>
  <div class="space-y-5">
    <ReportsFilters
      v-model:start-date="filters.startDate"
      v-model:end-date="filters.endDate"
      v-model:salesperson="filters.salesperson"
      :salesperson-options="salespeople"
      :salesperson-supported="salespersonSupported"
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
        {{ __('You do not have permission to view sales performance from Orders.') }}
      </p>
    </div>

    <div
      v-else-if="errorMessage"
      class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center"
      role="alert"
    >
      <h2 class="font-semibold text-ink-gray-9">{{ __('Unable to load sales performance') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ errorMessage }}</p>
      <Button class="mt-4" :label="__('Try again')" :loading="loading" @click="loadReport" />
    </div>

    <template v-else-if="data">
      <p class="rounded-lg bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6">
        {{ data.business_definition }}
      </p>

      <section class="grid grid-cols-1 gap-3 sm:grid-cols-3" :aria-label="__('Sales summary')">
        <article class="rounded-xl border border-outline-gray-2 bg-surface-white p-4">
          <p class="text-sm text-ink-gray-5">{{ __('Booked sales') }}</p>
          <p class="mt-2 text-2xl font-semibold text-ink-gray-9">{{ money(data.booked_sales) }}</p>
        </article>
        <article class="rounded-xl border border-outline-gray-2 bg-surface-white p-4">
          <p class="text-sm text-ink-gray-5">{{ __('Confirmed / Completed orders') }}</p>
          <p class="mt-2 text-2xl font-semibold text-ink-gray-9">{{ integer(data.order_count) }}</p>
        </article>
        <article class="rounded-xl border border-outline-gray-2 bg-surface-white p-4">
          <p class="text-sm text-ink-gray-5">{{ __('Average order value') }}</p>
          <p class="mt-2 text-2xl font-semibold text-ink-gray-9">{{ money(data.average_order_value) }}</p>
        </article>
      </section>

      <div
        v-if="!data.order_count"
        class="rounded-xl border border-dashed border-outline-gray-3 bg-surface-gray-1 px-5 py-12 text-center"
      >
        <h2 class="font-semibold text-ink-gray-9">{{ __('No booked orders found') }}</h2>
        <p class="mt-1 text-sm text-ink-gray-5">
          {{ __('Try another date range or Deal Owner.') }}
        </p>
      </div>

      <template v-else>
        <section class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5">
          <div class="mb-5">
            <h2 class="font-semibold text-ink-gray-9">{{ __('Booked sales trend') }}</h2>
            <p class="mt-1 text-sm text-ink-gray-5">{{ __('Grouped by Order Date') }}</p>
          </div>
          <div class="overflow-x-auto pb-1">
            <div class="flex min-w-max items-end gap-3" role="img" :aria-label="__('Booked sales by Order Date')">
              <div
                v-for="point in data.trend"
                :key="point.date"
                class="flex w-16 flex-col items-center gap-2"
              >
                <span class="text-xs font-medium text-ink-gray-7">{{ compactMoney(point.booked_sales) }}</span>
                <div class="flex h-40 w-full items-end justify-center rounded-md bg-surface-gray-1 px-2">
                  <div
                    class="w-full rounded-t bg-surface-gray-7"
                    :style="{ height: trendHeight(point.booked_sales) }"
                    :title="`${displayDate(point.date)}: ${money(point.booked_sales)}`"
                  />
                </div>
                <span class="whitespace-nowrap text-xs text-ink-gray-5">{{ shortDate(point.date) }}</span>
              </div>
            </div>
          </div>
        </section>

        <section class="overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white">
          <div class="p-4 sm:p-5">
            <h2 class="font-semibold text-ink-gray-9">{{ __('Performance by Deal Owner') }}</h2>
            <p class="mt-1 text-sm text-ink-gray-5">
              {{ __('Orders without a readable owned Deal are kept separate; ownership is never inferred.') }}
            </p>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="border-y border-outline-gray-2 bg-surface-gray-1 text-ink-gray-5">
                <tr>
                  <th class="px-4 py-3 font-medium sm:px-5">{{ __('Deal Owner') }}</th>
                  <th class="px-4 py-3 text-right font-medium">{{ __('Orders') }}</th>
                  <th class="px-4 py-3 text-right font-medium">{{ __('Booked sales') }}</th>
                  <th class="px-4 py-3 text-right font-medium sm:px-5">{{ __('Average order') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-outline-gray-1">
                <tr v-for="row in data.by_salesperson" :key="`${row.assignment_state}-${row.label}`">
                  <td class="whitespace-nowrap px-4 py-3 text-ink-gray-8 sm:px-5">{{ row.label }}</td>
                  <td class="whitespace-nowrap px-4 py-3 text-right text-ink-gray-7">{{ integer(row.order_count) }}</td>
                  <td class="whitespace-nowrap px-4 py-3 text-right text-ink-gray-7">{{ money(row.booked_sales) }}</td>
                  <td class="whitespace-nowrap px-4 py-3 text-right text-ink-gray-7 sm:px-5">{{ money(row.average_order_value) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <section class="overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white">
          <div class="p-4 sm:p-5">
            <h2 class="font-semibold text-ink-gray-9">{{ __('Recent booked orders') }}</h2>
            <p class="mt-1 text-sm text-ink-gray-5">{{ __('Latest 10 orders in the applied filters') }}</p>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-left text-sm">
              <thead class="border-y border-outline-gray-2 bg-surface-gray-1 text-ink-gray-5">
                <tr>
                  <th class="px-4 py-3 font-medium sm:px-5">{{ __('Order') }}</th>
                  <th class="px-4 py-3 font-medium">{{ __('Order Date') }}</th>
                  <th class="px-4 py-3 font-medium">{{ __('Status') }}</th>
                  <th class="px-4 py-3 font-medium">{{ __('Deal') }}</th>
                  <th class="px-4 py-3 text-right font-medium sm:px-5">{{ __('Total') }}</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-outline-gray-1">
                <tr v-for="order in data.recent_orders" :key="order.name">
                  <td class="whitespace-nowrap px-4 py-3 sm:px-5">
                    <RouterLink
                      :to="{ name: 'OrderDetail', params: { orderId: order.name } }"
                      class="font-medium text-ink-blue-3 hover:underline"
                    >
                      {{ order.name }}
                    </RouterLink>
                  </td>
                  <td class="whitespace-nowrap px-4 py-3 text-ink-gray-7">{{ displayDate(order.order_date) }}</td>
                  <td class="whitespace-nowrap px-4 py-3 text-ink-gray-7">{{ order.status }}</td>
                  <td class="whitespace-nowrap px-4 py-3 text-ink-gray-7">
                    <RouterLink
                      v-if="order.deal"
                      :to="{ name: 'DealDetail', params: { dealId: order.deal } }"
                      class="text-ink-blue-3 hover:underline"
                    >
                      {{ order.deal_label || order.deal }}
                    </RouterLink>
                    <span v-else-if="order.deal_restricted">{{ __('Unavailable') }}</span>
                    <span v-else>{{ __('No Deal') }}</span>
                  </td>
                  <td class="whitespace-nowrap px-4 py-3 text-right font-medium text-ink-gray-8 sm:px-5">
                    {{ money(order.total) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </template>
    </template>

    <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-3" aria-live="polite">
      <div v-for="index in 3" :key="index" class="h-28 animate-pulse rounded-xl bg-surface-gray-2" />
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
const salespersonSupported = computed(() => data.value?.permissions?.deals !== false)
const maxTrendValue = computed(() => Math.max(...(data.value?.trend || []).map(row => Number(row.booked_sales) || 0), 0))

function integer(value) {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(value) || 0)
}

function displayDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`))
}

function shortDate(value) {
  if (!value) return ''
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`))
}

function compactMoney(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1,
  }).format(Number(value) || 0)
}

function trendHeight(value) {
  if (!maxTrendValue.value) return '0%'
  return `${Math.max((Number(value) / maxTrendValue.value) * 100, 3)}%`
}

async function loadReport() {
  loading.value = true
  errorMessage.value = ''
  permissionDenied.value = false
  try {
    data.value = await call('doublet_crm.reports.get_sales_performance', {
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
