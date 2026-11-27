<template>
  <div class="space-y-5">
    <ReportsFilters
      v-model:start-date="filters.startDate" v-model:end-date="filters.endDate"
      v-model:salesperson="filters.salesperson" v-model:compare-previous="filters.comparePrevious"
      :salesperson-options="salespeople" :salesperson-supported="salespersonSupported"
      :team-unsupported-reason="teamUnsupportedReason" :loading="loading"
      report-key="quotation-order"
      :export-filters="appliedFilters || {}" :export-enabled="Boolean(appliedFilters)"
      @apply="loadReport" @reset="resetFilters" @restore="restoreFilters"
    />

    <div v-if="permissionDenied" class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center" role="alert">
      <h2 class="font-semibold text-ink-gray-9">{{ __('Permission required') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ __('You do not have permission to view Quotations or Orders.') }}</p>
    </div>
    <div v-else-if="errorMessage" class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center" role="alert">
      <h2 class="font-semibold text-ink-gray-9">{{ __('Unable to load quotation & order data') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ errorMessage }}</p>
      <Button class="mt-4" :label="__('Try again')" :loading="loading" @click="loadReport" />
    </div>

    <template v-else-if="data">
      <p class="rounded-lg bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6">{{ data.business_definition }}</p>
      <p v-if="data.comparison" class="text-sm text-ink-gray-6" role="status">
        {{ data.comparison.definition }} {{ displayDate(data.comparison.start_date) }}–{{ displayDate(data.comparison.end_date) }}.
      </p>

      <section class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" :aria-label="__('Quotation summary')">
        <MetricCard label="Quotations" :value="metric(quotationSummary?.quotation_count)" :change="comparisonChange('quotation_count')" />
        <MetricCard label="Quotation Value" :value="moneyMetric(quotationSummary?.quotation_value)" :change="comparisonChange('quotation_value', 'money')" />
        <MetricCard label="Accepted" :value="metric(quotationSummary?.accepted_count)" :change="comparisonChange('accepted_count')" />
        <MetricCard label="Acceptance Rate" :value="percentage(quotationSummary?.acceptance_rate)" :change="comparisonChange('acceptance_rate', 'points')" />
        <MetricCard label="Expired Quotations" :value="metric(quotationSummary?.expired_count)" />
      </section>

      <section v-if="quotationSummary?.approval_statuses?.length" class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5">
        <h2 class="font-semibold text-ink-gray-9">{{ __('Discount Approval Status') }}</h2>
        <div class="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3"><div v-for="row in quotationSummary.approval_statuses" :key="row.status" class="flex items-center justify-between rounded bg-surface-gray-1 px-3 py-2 text-sm"><span>{{ __(row.status) }}</span><strong>{{ metric(row.count) }}</strong></div></div>
      </section>

      <section class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" :aria-label="__('Order summary')">
        <MetricCard label="Orders (All)" :value="metric(orderSummary?.order_count)" :change="comparisonChange('order_count')" />
        <MetricCard label="Booked Orders" :value="metric(orderSummary?.booked_order_count)" :change="comparisonChange('booked_order_count')" />
        <MetricCard label="Booked Sales" :value="moneyMetric(orderSummary?.booked_sales)" :change="comparisonChange('booked_sales', 'money')" />
        <MetricCard label="Quotation→Order Rate" :value="percentage(conversion?.quotation_to_order_rate)" :change="comparisonChange('quotation_to_order_rate', 'points')" />
      </section>

      <section class="grid grid-cols-1 gap-3 sm:grid-cols-3" :aria-label="__('Accepted quotation conversion')">
        <MetricCard label="Accepted denominator" :value="metric(conversion?.accepted_quotation_count)" :change="comparisonChange('accepted_quotation_count')" />
        <MetricCard label="Accepted with Booked Order" :value="metric(conversion?.accepted_quotations_with_orders)" :change="comparisonChange('accepted_quotations_with_orders')" />
        <MetricCard label="Accepted→Booked Rate" :value="percentage(conversion?.accepted_to_booked_order_rate)" :change="comparisonChange('accepted_to_booked_order_rate', 'points')" />
      </section>

      <div v-if="!hasResults" class="rounded-xl border border-dashed border-outline-gray-3 bg-surface-gray-1 px-5 py-12 text-center">
        <h2 class="font-semibold text-ink-gray-9">{{ __('No quotations or orders found in the selected period') }}</h2>
        <p class="mt-1 text-sm text-ink-gray-5">{{ __('Try another date range or Deal Owner. Unavailable sources are not treated as zero.') }}</p>
      </div>

      <template v-else>
        <section v-if="quotationSummary?.by_status?.length" class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5">
          <h2 class="font-semibold text-ink-gray-9">{{ __('Quotation status chart') }}</h2>
          <div class="mt-4 space-y-3">
            <div v-for="row in quotationSummary.by_status" :key="row.status">
              <div class="flex justify-between text-sm"><span>{{ row.status }}</span><span>{{ metric(row.count) }}</span></div>
              <div class="mt-1 h-3 rounded-full bg-surface-gray-2"><div class="h-full rounded-full bg-blue-500" :style="{ width: statusWidth(row.count, quotationSummary.quotation_count) }" /></div>
            </div>
          </div>
        </section>

        <section v-if="orderSummary?.by_status?.length" class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5">
          <h2 class="font-semibold text-ink-gray-9">{{ __('Order status chart') }}</h2>
          <div class="mt-4 space-y-3">
            <div v-for="row in orderSummary.by_status" :key="row.status">
              <div class="flex justify-between text-sm"><span>{{ row.status }}</span><span>{{ metric(row.count) }}</span></div>
              <div class="mt-1 h-3 rounded-full bg-surface-gray-2"><div class="h-full rounded-full bg-green-500" :style="{ width: statusWidth(row.count, orderSummary.order_count) }" /></div>
            </div>
          </div>
        </section>

        <ReportTable v-if="quotationSummary?.by_status?.length" title="Quotations by Status" description="Count, value and percentage by quotation status.">
          <template #head><tr><Th>Status</Th><Th right>Count</Th><Th right>Value</Th><Th right>Count %</Th><Th right>Value %</Th></tr></template>
          <tr v-for="row in quotationSummary.by_status" :key="row.status" class="border-t border-outline-gray-1">
            <Td><span :class="statusClass(row.status, 'Quotation')">{{ row.status }}</span></Td>
            <Td right>{{ integer(row.count) }}</Td>
            <Td right>{{ money(row.value) }}</Td>
            <Td right>{{ percent(row.count_percentage) }}</Td>
            <Td right>{{ percent(row.value_percentage) }}</Td>
          </tr>
        </ReportTable>

        <ReportTable v-if="orderSummary?.by_status?.length" title="Orders by Status" description="Count, booked value and total value by order status. Booked includes Confirmed/Completed only.">
          <template #head><tr><Th>Status</Th><Th right>Count</Th><Th right>Booked Value</Th><Th right>Total Value</Th></tr></template>
          <tr v-for="row in orderSummary.by_status" :key="row.status" class="border-t border-outline-gray-1">
            <Td><span :class="statusClass(row.status, 'Order')">{{ row.status }}</span></Td>
            <Td right>{{ integer(row.count) }}</Td>
            <Td right>{{ money(row.booked_value) }}</Td>
            <Td right>{{ money(row.total_value) }}</Td>
          </tr>
        </ReportTable>

        <ReportTable v-if="data.quotation_drilldown && data.quotation_drilldown.length" title="Quotation drill-down" :description="__('All {0} readable Quotations behind the status aggregate.'.replace('{0}', String(data.quotation_drilldown.length)))">
          <template #head><tr><Th>Quotation</Th><Th>Status</Th><Th>Date</Th><Th>Deal</Th><Th right>Value</Th></tr></template>
          <tr v-for="row in data.quotation_drilldown" :key="row.name" class="border-t border-outline-gray-1">
            <Td><RouterLink :to="{ name: 'QuotationDetail', params: { quotationId: row.name } }" class="font-medium text-[#1D4ED8] hover:underline">{{ row.name }}</RouterLink></Td>
            <Td><span :class="statusClass(row.status, 'Quotation')">{{ row.status }}</span></Td>
            <Td>{{ displayDate(row.quotation_date) }}</Td>
            <Td><RouterLink v-if="row.deal" :to="{ name: 'DealDetail', params: { dealId: row.deal } }" class="text-[#1D4ED8] hover:underline">{{ row.deal_title || row.deal }}</RouterLink><span v-else class="text-ink-gray-5">{{ row.deal_restricted ? __('Unavailable') : '—' }}</span></Td>
            <Td right>{{ money(row.grand_total) }}</Td>
          </tr>
        </ReportTable>

        <ReportTable v-if="data.order_drilldown && data.order_drilldown.length" title="Order drill-down" :description="__('All {0} readable Orders behind the status aggregate.'.replace('{0}', String(data.order_drilldown.length)))">
          <template #head><tr><Th>Order</Th><Th>Status</Th><Th>Date</Th><Th>Deal</Th><Th right>Total</Th><Th>Booked</Th></tr></template>
          <tr v-for="row in data.order_drilldown" :key="row.name" class="border-t border-outline-gray-1">
            <Td><RouterLink :to="{ name: 'OrderDetail', params: { orderId: row.name } }" class="font-medium text-[#1D4ED8] hover:underline">{{ row.name }}</RouterLink></Td>
            <Td><span :class="statusClass(row.status, 'Order')">{{ row.status }}</span></Td>
            <Td>{{ displayDate(row.order_date) }}</Td>
            <Td><RouterLink v-if="row.deal" :to="{ name: 'DealDetail', params: { dealId: row.deal } }" class="text-[#1D4ED8] hover:underline">{{ row.deal_title || row.deal }}</RouterLink><span v-else class="text-ink-gray-5">{{ row.deal_restricted ? __('Unavailable') : '—' }}</span></Td>
            <Td right>{{ money(row.total) }}</Td>
            <Td>{{ row.is_booked ? __('Yes') : __('No') }}</Td>
          </tr>
        </ReportTable>

        <ReportTable v-if="conversion?.accepted_conversion_drilldown?.length" title="Accepted Quotation → Booked Order drill-down" description="Current Accepted Quotations dated in the selected range; linked Confirmed/Completed Orders are deduplicated and may have any Order Date.">
          <template #head><tr><Th>Quotation</Th><Th>Date</Th><Th>Converted</Th><Th>Booked Orders</Th><Th right>Quotation Value</Th></tr></template>
          <tr v-for="row in conversion.accepted_conversion_drilldown" :key="row.name" class="border-t border-outline-gray-1">
            <Td><RouterLink :to="{ name: 'QuotationDetail', params: { quotationId: row.name } }" class="font-medium text-[#1D4ED8] hover:underline">{{ row.name }}</RouterLink></Td>
            <Td>{{ displayDate(row.quotation_date) }}</Td><Td>{{ row.converted ? __('Yes') : __('No') }}</Td>
            <Td><span v-if="!row.orders.length">—</span><RouterLink v-for="order in row.orders" :key="order.name" :to="{ name: 'OrderDetail', params: { orderId: order.name } }" class="mr-2 text-[#1D4ED8] hover:underline">{{ order.name }}</RouterLink></Td>
            <Td right>{{ money(row.grand_total) }}</Td>
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
const quotationSummary = computed(() => data.value?.quotation_summary || null)
const orderSummary = computed(() => data.value?.order_summary || null)
const conversion = computed(() => data.value?.conversion || null)
const teamUnsupportedReason = computed(() => data.value?.capabilities?.team_filter?.reason || 'Team filtering is unavailable because DoubleT Deal has no team field.')
const hasResults = computed(() => Boolean(quotationSummary.value?.quotation_count || orderSummary.value?.order_count))
const integer = value => new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(value) || 0)
const decimal = value => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(Number(value) || 0)
const percent = value => `${decimal(value)}%`
const metric = value => value == null ? __('Unavailable') : integer(value)
const percentage = value => value == null ? __('Unavailable') : percent(value)
const moneyMetric = value => value == null ? __('Unavailable') : money(value)
const statusWidth = (count, total) => !total ? '0%' : `${Number(count) * 100 / Number(total)}%`
const displayDate = value => value ? new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${String(value).slice(0, 10)}T00:00:00Z`)) : ''
const statusClass = (status, type) => {
  if (type === 'Quotation') {
    const classes = { 'Draft': 'text-ink-gray-5', 'Sent': 'text-ink-blue-4', 'Accepted': 'text-ink-green-5', 'Rejected': 'text-ink-red-4' }
    return classes[status] || 'text-ink-gray-5'
  }
  const classes = { 'Draft': 'text-ink-gray-5', 'Confirmed': 'text-ink-yellow-6', 'Completed': 'text-ink-green-5', 'Cancelled': 'text-ink-red-4' }
  return classes[status] || 'text-ink-gray-5'
}
function comparisonChange(metric, format = 'number') {
  const item = data.value?.comparison?.metrics?.[metric]
  if (!item || item.change == null) return ''
  const value = format === 'money' ? money(Math.abs(item.change)) : format === 'points' ? `${decimal(Math.abs(item.change))} pp` : integer(Math.abs(item.change))
  return `${item.change >= 0 ? '+' : '−'}${value} vs previous period`
}
async function loadReport() {
  loading.value = true; errorMessage.value = ''; permissionDenied.value = false
  try { const request = { start_date: filters.startDate, end_date: filters.endDate, salesperson: filters.salesperson || null, compare_previous: filters.comparePrevious ? 1 : 0 }; data.value = await call('doublet_crm.reports.get_quotation_order', request); appliedFilters.value = request }
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
