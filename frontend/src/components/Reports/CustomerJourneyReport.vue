<template>
  <div class="space-y-5">
    <ReportsFilters
      v-model:start-date="filters.startDate" v-model:end-date="filters.endDate"
      v-model:salesperson="filters.salesperson" v-model:compare-previous="filters.comparePrevious"
      :salesperson-options="salespeople" :salesperson-supported="salespersonSupported"
      :team-unsupported-reason="teamUnsupportedReason" :loading="loading"
      report-key="customer-journey"
      :export-filters="appliedFilters || {}" :export-enabled="Boolean(appliedFilters)"
      @apply="loadReport" @reset="resetFilters" @restore="restoreFilters"
    />

    <section class="rounded-xl border border-outline-gray-2 bg-surface-white p-4">
      <label class="block max-w-sm">
        <span class="mb-1.5 block text-sm font-medium text-ink-gray-7">{{ __('Lead Source') }}</span>
        <select v-model="filters.source" class="h-9 w-full rounded border border-outline-gray-2 bg-surface-white px-3 text-sm" :disabled="loading">
          <option value="">{{ __('All sources') }}</option>
          <option v-for="item in sources" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
      </label>
    </section>

    <div v-if="permissionDenied" class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center" role="alert">
      <h2 class="font-semibold text-ink-gray-9">{{ __('Permission required') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ __('You do not have permission to view customer journey from Leads.') }}</p>
    </div>
    <div v-else-if="errorMessage" class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center" role="alert">
      <h2 class="font-semibold text-ink-gray-9">{{ __('Unable to load customer journey') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ errorMessage }}</p>
      <Button class="mt-4" :label="__('Try again')" :loading="loading" @click="loadReport" />
    </div>

    <template v-else-if="data">
      <p class="rounded-lg bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6">{{ data.business_definition }}</p>
      <p v-if="data.comparison" class="text-sm text-ink-gray-6" role="status">
        {{ data.comparison.definition }} {{ displayDate(data.comparison.start_date) }}–{{ displayDate(data.comparison.end_date) }}.
      </p>

      <section class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" :aria-label="__('Journey funnel summary')">
        <MetricCard label="Leads (Created)" :value="integer(data.lead_count)" :change="comparisonChange('lead_count')" />
        <MetricCard label="Leads reaching Deal" :value="metric(data.deal_count)" :change="comparisonChange('deal_count')" />
        <MetricCard label="Leads with Won Deal" :value="metric(data.won_lead_count)" :change="comparisonChange('won_lead_count')" />
        <MetricCard label="Lead to Won Rate" :value="percentage(data.lead_to_won_rate)" :change="comparisonChange('lead_to_won_rate', 'points')" />
        <MetricCard label="Leads reaching Quotation" :value="metric(data.quotation_count)" :change="comparisonChange('quotation_count')" />
        <MetricCard label="Leads reaching Booked Order" :value="metric(data.order_count)" :change="comparisonChange('order_count')" />
        <MetricCard label="Lead to Deal Rate" :value="percentage(data.lead_to_deal_rate)" :change="comparisonChange('lead_to_deal_rate', 'points')" />
        <MetricCard label="Deal to Order Rate" :value="percentage(data.deal_to_order_rate)" :change="comparisonChange('deal_to_order_rate', 'points')" />
        <MetricCard label="Cohort Deal Value" :value="moneyMetric(data.deal_value)" :change="comparisonChange('deal_value', 'money')" />
        <MetricCard label="Booked Order Value" :value="moneyMetric(data.order_value)" :change="comparisonChange('order_value', 'money')" />
      </section>

      <section class="grid grid-cols-2 gap-3 rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:grid-cols-4" :aria-label="__('Entity totals for the Lead cohort')">
        <MetricCard label="Lead entities" :value="metric(data.entity_totals.leads)" />
        <MetricCard label="Deal entities" :value="metric(data.entity_totals.deals)" />
        <MetricCard label="Quotation entities" :value="metric(data.entity_totals.quotations)" />
        <MetricCard label="Booked Order entities" :value="metric(data.entity_totals.booked_orders)" />
      </section>

      <div v-if="!hasResults" class="rounded-xl border border-dashed border-outline-gray-3 bg-surface-gray-1 px-5 py-12 text-center">
        <h2 class="font-semibold text-ink-gray-9">{{ __('No leads found in the selected period') }}</h2>
        <p class="mt-1 text-sm text-ink-gray-5">{{ __('Try another date range or Lead Owner.') }}</p>
      </div>

      <template v-else>
        <section v-if="data.funnel.length" class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5">
          <h2 class="font-semibold text-ink-gray-9">{{ __('Conversion funnel') }}</h2>
          <p class="mt-1 text-sm text-ink-gray-5">{{ __('Unique cohort Leads reaching each stage; entity totals are separate above.') }}</p>
          <div class="mt-5 overflow-x-auto pb-1">
            <div class="flex min-w-max items-end justify-between gap-2" role="img" :aria-label="__('Lead to Order funnel')">
              <div v-for="(stage, index) in data.funnel" :key="stage.stage" class="flex flex-1 flex-col items-center gap-2">
                <span class="text-xs font-medium text-ink-gray-7">{{ moneyMetric(stage.value) }}</span>
                <div class="flex h-32 w-full items-end justify-center rounded-md bg-surface-gray-1 px-2">
                  <div class="w-full rounded-t bg-surface-gray-7" :style="{ height: funnelHeight(stage.count) }" :title="`${stage.stage}: ${metric(stage.count)} cohort Leads`" />
                </div>
                <span class="whitespace-nowrap text-sm font-medium text-ink-gray-9">{{ stage.stage }}</span>
                <span class="text-xs text-ink-gray-5">{{ metric(stage.count) }}</span>
              </div>
            </div>
          </div>
        </section>

        <ReportTable v-if="data.by_owner.length" title="Performance by Lead Owner" description="Unique cohort Leads reaching each stage, grouped only by Lead Owner.">
          <template #head><tr><Th>Lead Owner</Th><Th right>Leads</Th><Th right>Deals</Th><Th right>Won Leads</Th><Th right>Quotations</Th><Th right>Orders</Th><Th right>Cohort Deal Value</Th><Th right>Order Value</Th></tr></template>
          <tr v-for="row in data.by_owner" :key="row.label" class="border-t border-outline-gray-1">
            <Td>{{ row.label }}</Td><Td right>{{ metric(row.lead_count) }}</Td><Td right>{{ metric(row.deal_count) }}</Td>
            <Td right>{{ metric(row.won_lead_count) }}</Td><Td right>{{ metric(row.quotation_count) }}</Td><Td right>{{ metric(row.order_count) }}</Td><Td right>{{ moneyMetric(row.deal_value) }}</Td><Td right>{{ moneyMetric(row.order_value) }}</Td>
          </tr>
        </ReportTable>

        <ReportTable v-if="data.journey_rows.length" title="Lead journey drill-down" :description="__('All {0} readable cohort Leads behind the funnel.'.replace('{0}', String(data.journey_rows.length)))">
          <template #head><tr><Th>Lead</Th><Th>Source</Th><Th>Stage</Th><Th>Related records</Th><Th right>Deal Value</Th><Th right>Order Value</Th></tr></template>
          <tr v-for="row in data.journey_rows" :key="row.name" class="border-t border-outline-gray-1">
            <Td><RouterLink :to="{ name: 'LeadDetail', params: { leadId: row.name } }" class="font-medium text-[#1D4ED8] hover:underline">{{ row.lead_name || row.name }}</RouterLink></Td>
            <Td>{{ row.source || '—' }}</Td><Td><span :class="stageClass(row.stage)">{{ row.stage }}</span></Td>
            <Td><div class="flex min-w-64 flex-wrap gap-2"><RouterLink v-for="item in row.deals || []" :key="`d-${item.name}`" :to="{ name: 'DealDetail', params: { dealId: item.name } }" class="text-[#1D4ED8] hover:underline">{{ item.label }}</RouterLink><RouterLink v-for="item in row.quotations || []" :key="`q-${item.name}`" :to="{ name: 'QuotationDetail', params: { quotationId: item.name } }" class="text-[#1D4ED8] hover:underline">{{ item.name }}</RouterLink><RouterLink v-for="item in row.orders || []" :key="`o-${item.name}`" :to="{ name: 'OrderDetail', params: { orderId: item.name } }" class="text-[#1D4ED8] hover:underline">{{ item.name }} ({{ item.link_type }})</RouterLink><span v-if="!(row.deals?.length || row.quotations?.length || row.orders?.length)" class="text-ink-gray-5">—</span></div></Td>
            <Td right>{{ moneyMetric(row.deal_amount) }}</Td><Td right>{{ moneyMetric(row.order_value) }}</Td>
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
const filters = reactive({ ...initialRange, salesperson: '', source: '', comparePrevious: false })
const data = ref(null), loading = ref(false), errorMessage = ref(''), permissionDenied = ref(false)
const appliedFilters = ref(null)
const salespeople = computed(() => data.value?.salespeople || [])
const sources = computed(() => data.value?.sources || [])
const salespersonSupported = computed(() => data.value?.permissions?.leads !== false)
const teamUnsupportedReason = computed(() => data.value?.capabilities?.team_filter?.reason || 'Team filtering is unavailable because DoubleT Deal has no team field.')
const hasResults = computed(() => Boolean(data.value?.lead_count))
const maxFunnelCount = computed(() => Math.max(...(data.value?.funnel || []).map(r => Number(r.count) || 0), 1))
const integer = value => new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(value) || 0)
const decimal = value => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(Number(value) || 0)
const percent = value => `${decimal(value)}%`
const metric = value => value == null ? __('Unavailable') : integer(value)
const percentage = value => value == null ? __('Unavailable') : percent(value)
const moneyMetric = value => value == null ? __('Unavailable') : money(value)
const displayDate = value => value ? new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${String(value).slice(0, 10)}T00:00:00Z`)) : ''
const funnelHeight = count => count == null ? '0%' : `${Math.max((Number(count) / maxFunnelCount.value) * 100, Number(count) ? 4 : 0)}%`
const stageClass = (stage) => {
  const classes = {
    'Lead': 'text-ink-gray-5',
    'Deal': 'text-ink-yellow-6',
    'Quotation': 'text-ink-blue-4',
    'Quotation Sent': 'text-[#1D4ED8]',
    'Quotation Accepted': 'text-ink-green-5',
    'Order': 'text-ink-green-6 font-medium',
  }
  return classes[stage] || 'text-ink-gray-5'
}
function comparisonChange(metric, format = 'number') {
  const item = data.value?.comparison?.metrics?.[metric]
  if (!item || item.change == null) return ''
  const value = format === 'money' ? money(Math.abs(item.change)) : format === 'points' ? `${decimal(Math.abs(item.change))} pp` : integer(Math.abs(item.change))
  return `${item.change >= 0 ? '+' : '−'}${value} vs previous period`
}
async function loadReport() {
  loading.value = true; errorMessage.value = ''; permissionDenied.value = false
  try { const request = { start_date: filters.startDate, end_date: filters.endDate, salesperson: filters.salesperson || null, source: filters.source || null, compare_previous: filters.comparePrevious ? 1 : 0 }; data.value = await call('doublet_crm.reports.get_customer_journey', request); appliedFilters.value = request }
  catch (error) { data.value = null; permissionDenied.value = isPermissionError(error); if (!permissionDenied.value) errorMessage.value = message(error) }
  finally { loading.value = false }
}
function resetFilters() { Object.assign(filters, reportDatePreset('30-days'), { salesperson: '', source: '', comparePrevious: false }); loadReport() }
function restoreFilters(saved) {
  Object.assign(filters, { startDate: saved.start_date || filters.startDate, endDate: saved.end_date || filters.endDate, salesperson: saved.salesperson || '', source: saved.source || '', comparePrevious: Boolean(Number(saved.compare_previous || 0)) })
  loadReport()
}
onMounted(loadReport)
</script>
