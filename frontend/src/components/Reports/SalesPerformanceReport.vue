<template>
  <div class="space-y-5">
    <ReportsFilters
      v-model:start-date="filters.startDate" v-model:end-date="filters.endDate"
      v-model:salesperson="filters.salesperson" v-model:compare-previous="filters.comparePrevious"
      :salesperson-options="salespeople" :salesperson-supported="salespersonSupported"
      :team-unsupported-reason="teamUnsupportedReason" :loading="loading"
      report-key="sales-performance"
      :export-filters="appliedFilters || {}" :export-enabled="Boolean(appliedFilters)"
      @apply="loadReport" @reset="resetFilters" @restore="restoreFilters"
    />

    <div v-if="permissionDenied" class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center" role="alert">
      <h2 class="font-semibold text-ink-gray-9">{{ __('Permission required') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ __('You do not have permission to view sales performance from Orders.') }}</p>
    </div>
    <div v-else-if="errorMessage" class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center" role="alert">
      <h2 class="font-semibold text-ink-gray-9">{{ __('Unable to load sales performance') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ errorMessage }}</p>
      <Button class="mt-4" :label="__('Try again')" :loading="loading" @click="loadReport" />
    </div>

    <template v-else-if="data">
      <p class="rounded-lg bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6">{{ data.business_definition }}</p>
      <p v-if="data.comparison" class="text-sm text-ink-gray-6" role="status">
        {{ data.comparison.definition }} {{ displayDate(data.comparison.start_date) }}–{{ displayDate(data.comparison.end_date) }}.
      </p>
      <div v-if="!dealMetricsAvailable" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6" role="status">
        {{ __('Deal outcome metrics and Deal links are unavailable with your current permissions. Order metrics remain available.') }}
      </div>

      <section class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" :aria-label="__('Sales and closed Deal summary')">
        <MetricCard label="Booked Sales (Order Date)" :value="money(data.booked_sales)" :change="comparisonChange('booked_sales', 'money')" />
        <MetricCard label="Order Count (Confirmed / Completed)" :value="integer(data.order_count)" :change="comparisonChange('order_count')" />
        <MetricCard label="Average Order Value" :value="money(data.average_order_value)" :change="comparisonChange('average_order_value', 'money')" />
        <MetricCard label="Won Deal Value (Won On)" :value="dealMetric(data.won_deal_value, money)" :change="comparisonChange('won_deal_value', 'money')" />
        <MetricCard label="Won Deals (Won On)" :value="dealMetric(data.won_count, integer)" :change="comparisonChange('won_count')" />
        <MetricCard label="Lost Deals (Lost On)" :value="dealMetric(data.lost_count, integer)" :change="comparisonChange('lost_count')" />
        <MetricCard label="Win Rate: Won / (Won + Lost)" :value="dealMetric(data.win_rate, percent)" :change="comparisonChange('win_rate', 'points')" />
        <MetricCard
          label="Average Close Duration (valid Won Deals)"
          :value="!dealMetricsAvailable ? __('Unavailable') : data.average_close_duration_days == null ? __('Not available') : `${decimal(data.average_close_duration_days)} ${__('days')}`"
          :note="dealMetricsAvailable ? `${integer(data.close_duration_denominator)} ${__('valid Won records')}` : ''"
          :change="comparisonChange('average_close_duration_days', 'days')"
        />
      </section>

      <div v-if="!hasResults" class="rounded-xl border border-dashed border-outline-gray-3 bg-surface-gray-1 px-5 py-12 text-center">
        <h2 class="font-semibold text-ink-gray-9">{{ __('No sales or closed Deals found') }}</h2>
        <p class="mt-1 text-sm text-ink-gray-5">{{ __('Try another date range or Deal Owner.') }}</p>
      </div>

      <template v-else>
        <section v-if="data.trend.length" class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5">
          <h2 class="font-semibold text-ink-gray-9">{{ __('Booked Sales trend') }}</h2>
          <p class="mt-1 text-sm text-ink-gray-5">{{ __('Grouped by Order Date; hover a bar for the exact USD value.') }}</p>
          <div class="mt-5 overflow-x-auto pb-1">
            <div class="flex min-w-max items-end gap-3" role="img" :aria-label="__('Booked Sales by Order Date')">
              <div v-for="point in data.trend" :key="point.date" class="flex w-16 flex-col items-center gap-2">
                <span class="text-xs font-medium text-ink-gray-7">{{ compactMoney(point.booked_sales) }}</span>
                <div class="flex h-40 w-full items-end justify-center rounded-md bg-surface-gray-1 px-2">
                  <div class="w-full rounded-t bg-surface-gray-7" :style="{ height: trendHeight(point.booked_sales) }" :title="`${displayDate(point.date)}: ${money(point.booked_sales)}; ${integer(point.order_count)} orders`" />
                </div>
                <span class="whitespace-nowrap text-xs text-ink-gray-5">{{ shortDate(point.date) }}</span>
              </div>
            </div>
          </div>
        </section>

        <ReportTable title="Performance by Deal Owner" description="Order and closed-Deal metrics use their respective event dates.">
          <template #head><tr><Th>Deal Owner</Th><Th right>Orders</Th><Th right>Booked Sales</Th><Th right>Won</Th><Th right>Lost</Th><Th right>Won Deal Value</Th><Th right>Win Rate</Th></tr></template>
          <tr v-for="row in data.employee_breakdown" :key="row.label" class="border-t border-outline-gray-1">
            <Td>{{ row.label }}</Td><Td right>{{ integer(row.order_count) }}</Td><Td right>{{ money(row.booked_sales) }}</Td>
            <Td right>{{ dealMetric(row.won_count, integer) }}</Td><Td right>{{ dealMetric(row.lost_count, integer) }}</Td><Td right>{{ dealMetric(row.won_deal_value, money) }}</Td><Td right>{{ dealMetric(row.win_rate, percent) }}</Td>
          </tr>
        </ReportTable>

        <ReportTable v-if="data.won_deals.length || data.lost_deals.length" title="Closed Deal drill-down" description="Every readable Deal included in the Won/Lost aggregates.">
          <template #head><tr><Th>Deal</Th><Th>Outcome</Th><Th>Event Date</Th><Th>Deal Owner</Th><Th right>Deal Amount</Th><Th right>Close Duration</Th></tr></template>
          <tr v-for="deal in closedDeals" :key="`${deal.outcome}-${deal.name}`" class="border-t border-outline-gray-1">
            <Td><RouterLink :to="{ name: 'DealDetail', params: { dealId: deal.name } }" class="font-medium text-[#1D4ED8] hover:underline">{{ deal.deal_title || deal.name }}</RouterLink></Td>
            <Td>{{ deal.outcome }}</Td><Td>{{ displayDateTime(deal.event_date) }}</Td><Td>{{ deal.deal_owner || __('Unassigned') }}</Td><Td right>{{ money(deal.amount) }}</Td>
            <Td right>{{ deal.close_duration_days == null ? '—' : `${decimal(deal.close_duration_days)} ${__('days')}` }}</Td>
          </tr>
        </ReportTable>

        <ReportTable v-if="data.recent_orders.length" title="Recent booked orders" description="Latest 10 readable Orders in the applied Order Date range.">
          <template #head><tr><Th>Order</Th><Th>Order Date</Th><Th>Status</Th><Th>Deal</Th><Th right>Total</Th></tr></template>
          <tr v-for="order in data.recent_orders" :key="order.name" class="border-t border-outline-gray-1">
            <Td><RouterLink :to="{ name: 'OrderDetail', params: { orderId: order.name } }" class="font-medium text-[#1D4ED8] hover:underline">{{ order.name }}</RouterLink></Td>
            <Td>{{ displayDate(order.order_date) }}</Td><Td>{{ order.status }}</Td>
            <Td><RouterLink v-if="order.deal" :to="{ name: 'DealDetail', params: { dealId: order.deal } }" class="text-[#1D4ED8] hover:underline">{{ order.deal_label || order.deal }}</RouterLink><span v-else>{{ order.deal_restricted ? __('Unavailable') : __('No Deal') }}</span></Td>
            <Td right>{{ money(order.total) }}</Td>
          </tr>
        </ReportTable>
      </template>
    </template>

    <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-live="polite">
      <div v-for="index in 8" :key="index" class="h-28 animate-pulse rounded-xl bg-surface-gray-2" />
    </div>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { call } from 'frappe-ui'
import ReportsFilters from '@/components/Reports/ReportsFilters.vue'
import { isPermissionError, reportDatePreset } from '@/utils/reportFilters'
import { message, money } from '@/utils/quotation'

const cell = (tag, right, slots) => h(tag, { class: ['whitespace-nowrap px-4 py-3', right ? 'text-right' : 'text-left'] }, slots.default?.())
const Th = defineComponent({ props: { right: Boolean }, setup: (props, { slots }) => () => cell('th', props.right, slots) })
const Td = defineComponent({ props: { right: Boolean }, setup: (props, { slots }) => () => cell('td', props.right, slots) })
const MetricCard = defineComponent({ props: { label: String, value: String, note: String, change: String }, setup: (props) => () => h('article', { class: 'rounded-xl border border-outline-gray-2 bg-surface-white p-4' }, [h('p', { class: 'text-sm text-ink-gray-5' }, props.label), h('p', { class: 'mt-2 text-2xl font-semibold text-ink-gray-9' }, props.value), props.note ? h('p', { class: 'mt-1 text-xs text-ink-gray-5' }, props.note) : null, props.change ? h('p', { class: 'mt-1 text-xs text-ink-gray-6' }, props.change) : null]) })
const ReportTable = defineComponent({ props: { title: String, description: String }, setup: (props, { slots }) => () => h('section', { class: 'overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white' }, [h('div', { class: 'p-4 sm:p-5' }, [h('h2', { class: 'font-semibold text-ink-gray-9' }, props.title), h('p', { class: 'mt-1 text-sm text-ink-gray-5' }, props.description)]), h('div', { class: 'overflow-x-auto' }, [h('table', { class: 'min-w-full text-left text-sm' }, [h('thead', { class: 'border-y border-outline-gray-2 bg-surface-gray-1 text-ink-gray-5' }, slots.head?.()), h('tbody', { class: 'text-ink-gray-7' }, slots.default?.())])])]) })

const initialRange = reportDatePreset('30-days')
const filters = reactive({ ...initialRange, salesperson: '', comparePrevious: false })
const data = ref(null), loading = ref(false), errorMessage = ref(''), permissionDenied = ref(false)
const appliedFilters = ref(null)
const salespeople = computed(() => data.value?.salespeople || [])
const salespersonSupported = computed(() => data.value?.permissions?.deals !== false)
const dealMetricsAvailable = computed(() => data.value?.permissions?.deals !== false)
const teamUnsupportedReason = computed(() => data.value?.capabilities?.team_filter?.reason || 'Team filtering is unavailable because DoubleT Deal has no team field.')
const hasResults = computed(() => Boolean(data.value?.order_count || data.value?.closed_count))
const closedDeals = computed(() => [...(data.value?.won_deals || []).map(row => ({ ...row, outcome: 'Won' })), ...(data.value?.lost_deals || []).map(row => ({ ...row, outcome: 'Lost' }))])
const maxTrendValue = computed(() => Math.max(...(data.value?.trend || []).map(row => Number(row.booked_sales) || 0), 0))
const integer = value => new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(value) || 0)
const decimal = value => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(Number(value) || 0)
const percent = value => `${decimal(value)}%`
const displayDate = value => value ? new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${String(value).slice(0, 10)}T00:00:00Z`)) : ''
const displayDateTime = value => displayDate(value)
const shortDate = value => value ? new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}T00:00:00Z`)) : ''
const compactMoney = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1 }).format(Number(value) || 0)
const trendHeight = value => !maxTrendValue.value ? '0%' : `${Math.max((Number(value) / maxTrendValue.value) * 100, 3)}%`
const dealMetric = (value, formatter) => !dealMetricsAvailable.value || value == null ? __('Unavailable') : formatter(value)
function comparisonChange(metric, format = 'number') {
  const item = data.value?.comparison?.metrics?.[metric]
  if (!item || item.change == null) return ''
  const value = format === 'money' ? money(Math.abs(item.change)) : format === 'points' ? `${decimal(Math.abs(item.change))} pp` : format === 'days' ? `${decimal(Math.abs(item.change))} days` : integer(Math.abs(item.change))
  return `${item.change >= 0 ? '+' : '−'}${value} vs previous period`
}
async function loadReport() {
  loading.value = true; errorMessage.value = ''; permissionDenied.value = false
  try { const request = { start_date: filters.startDate, end_date: filters.endDate, salesperson: filters.salesperson || null, compare_previous: filters.comparePrevious ? 1 : 0 }; data.value = await call('doublet_crm.reports.get_sales_performance', request); appliedFilters.value = request }
  catch (error) { data.value = null; permissionDenied.value = isPermissionError(error); if (!permissionDenied.value) errorMessage.value = message(error) }
  finally { loading.value = false }
}
function resetFilters() { Object.assign(filters, reportDatePreset('30-days'), { salesperson: '', comparePrevious: false }); loadReport() }
function restoreFilters(saved) {
  Object.assign(filters, {
    startDate: saved.start_date || filters.startDate, endDate: saved.end_date || filters.endDate,
    salesperson: saved.salesperson || '', comparePrevious: Boolean(Number(saved.compare_previous || 0)),
  })
  loadReport()
}
onMounted(loadReport)
</script>
