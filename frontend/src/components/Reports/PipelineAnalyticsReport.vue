<template>
  <div class="space-y-5">
    <ReportsFilters
      v-model:start-date="filters.startDate" v-model:end-date="filters.endDate"
      v-model:salesperson="filters.salesperson" v-model:compare-previous="filters.comparePrevious"
      :salesperson-options="salespeople" :salesperson-supported="true"
      :team-unsupported-reason="teamUnsupportedReason" :loading="loading"
      report-key="pipeline-analytics"
      :export-filters="appliedFilters || {}" :export-enabled="Boolean(appliedFilters)"
      @apply="loadReport" @reset="resetFilters" @restore="restoreFilters"
    />

    <div v-if="permissionDenied" class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center" role="alert">
      <h2 class="font-semibold text-ink-gray-9">{{ __('Permission required') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ __('You do not have permission to view pipeline analytics from Deals.') }}</p>
    </div>
    <div v-else-if="errorMessage" class="rounded-xl border border-outline-gray-2 bg-surface-gray-1 p-6 text-center" role="alert">
      <h2 class="font-semibold text-ink-gray-9">{{ __('Unable to load pipeline analytics') }}</h2>
      <p class="mt-1 text-sm text-ink-gray-5">{{ errorMessage }}</p>
      <Button class="mt-4" :label="__('Try again')" :loading="loading" @click="loadReport" />
    </div>

    <template v-else-if="data">
      <p class="rounded-lg bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6">{{ data.business_definition }}</p>
      <p v-if="data.comparison" class="text-sm text-ink-gray-6" role="status">{{ data.comparison.definition }} {{ displayDate(data.comparison.start_date) }}–{{ displayDate(data.comparison.end_date) }}.</p>
      <div v-if="data.permissions?.stages === false" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6" role="status">
        {{ __('Stage metadata is restricted. Lifecycle is derived from each readable Deal’s Won On and Lost On fields.') }}
      </div>

      <section class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" :aria-label="__('Pipeline summary')">
        <MetricCard label="Deals Created (Creation)" :value="integer(data.deal_count)" :note="`${money(data.total_deal_value)} ${__('total Deal value')}`" :change="comparisonChange('deal_count')" />
        <MetricCard label="Open Pipeline Value (created in range)" :value="money(data.open_pipeline_value)" :note="`${integer(data.lifecycle.OPEN.deal_count)} ${__('Open Deals')}`" :change="comparisonChange('open_pipeline_value', 'money')" />
        <MetricCard label="Lost Deals (Lost On)" :value="integer(data.lost_reason_count)" :note="`${money(data.lost_reason_value)} ${__('recorded Deal value')}`" :change="comparisonChange('lost_reason_deal_count')" />
        <MetricCard label="Overdue Open Deals (Expected Close Date in range)" :value="integer(data.overdue_open_count)" :note="`${money(data.overdue_open_value)} · ${__('before')} ${displayDate(data.as_of_date)}`" :change="comparisonChange('overdue_open_count')" />
        <MetricCard label="Stale Open Deals (30 days)" :value="integer(data.stale_open_count)" :note="`${money(data.stale_open_value)} · ${__('not modified since')} ${displayDate(data.stale_cutoff)}`" :change="comparisonChange('stale_open_count')" />
      </section>

      <section v-if="data.forecast?.available" class="space-y-4" :aria-label="__('Sales forecast')">
        <div>
          <h2 class="font-semibold text-ink-gray-9">{{ __('Monthly Sales Forecast') }}</h2>
          <p class="mt-1 text-sm text-ink-gray-5">{{ data.forecast.definition }}</p>
        </div>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Total Open Pipeline (unweighted)" :value="money(data.forecast.total_unweighted_pipeline_value)" :note="`${integer(data.forecast.open_deal_count)} ${__('readable Open Deals')}`" />
          <MetricCard label="Forecast in selected period (unweighted)" :value="money(data.forecast.unweighted_forecast_value)" :note="`${integer(data.forecast.forecast_deal_count)} ${__('Deals with forecast close dates')}`" />
          <MetricCard label="Weighted forecast" :value="data.forecast.weighted_available ? money(data.forecast.weighted_forecast_value) : __('Unavailable')" :note="data.forecast.weighted_available ? `${integer(data.forecast.missing_probability_count)} ${__('Deals missing probability')}` : data.forecast.weighted_reason" />
          <MetricCard label="Incomplete or overdue forecast" :value="integer(data.forecast.missing_close_date_count + data.forecast.overdue_count)" :note="`${integer(data.forecast.missing_close_date_count)} ${__('missing close date')} · ${integer(data.forecast.overdue_count)} ${__('overdue')}`" />
        </div>
        <section v-if="forecastMonths.length" class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5">
          <h3 class="font-semibold text-ink-gray-9">{{ __('Forecast by expected close month') }}</h3>
          <p class="mt-1 text-sm text-ink-gray-5">{{ __('These values are forecast revenue and are not actual booked sales.') }}</p>
          <div class="mt-5 space-y-4" role="img" :aria-label="__('Monthly unweighted sales forecast')">
            <div v-for="month in forecastMonths" :key="month.month" class="rounded-lg p-2">
              <div class="flex flex-wrap items-center justify-between gap-2 text-sm"><span class="font-medium text-ink-gray-8">{{ monthLabel(month.month) }}</span><span class="text-ink-gray-6">{{ integer(month.deal_count) }} {{ __('Deals') }} · {{ money(month.unweighted_value) }}</span></div>
              <div class="mt-2 h-3 overflow-hidden rounded-full bg-surface-gray-2"><div class="h-full rounded-full bg-violet-500" :style="{ width: forecastBarWidth(month.unweighted_value) }" /></div>
            </div>
          </div>
        </section>
        <ReportTable v-if="forecastDeals.length" title="Forecast Deal drill-down" description="Every readable Open Deal contributing to a selected forecast month.">
          <template #head><tr><Th>Forecast Month</Th><Th>Deal</Th><Th>Deal Owner</Th><Th>Expected Close</Th><Th right>Deal Value</Th><Th right>Probability</Th><Th right>Weighted Value</Th></tr></template>
          <tr v-for="deal in forecastDeals" :key="`${deal.forecast_month}-${deal.name}`" class="border-t border-outline-gray-1"><Td>{{ monthLabel(deal.forecast_month) }}</Td><Td><RouterLink :to="{ name: 'DealDetail', params: { dealId: deal.name } }" class="font-medium text-[#1D4ED8] hover:underline">{{ deal.deal_title || deal.name }}</RouterLink></Td><Td>{{ deal.deal_owner || __('Unassigned') }}</Td><Td>{{ displayDate(deal.expected_close_date) }}</Td><Td right>{{ money(deal.amount) }}</Td><Td right>{{ deal.probability == null ? __('Missing') : percent(deal.probability) }}</Td><Td right>{{ deal.weighted_value == null ? '—' : money(deal.weighted_value) }}</Td></tr>
        </ReportTable>
      </section>
      <div v-else-if="data.forecast" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6" role="status">
        {{ data.forecast.reason }}
      </div>

      <section v-if="data.stage_aging?.available" class="space-y-4" :aria-label="__('Stage Aging')">
        <div><h2 class="font-semibold text-ink-gray-9">{{ __('Stage Aging') }}</h2><p class="mt-1 text-sm text-ink-gray-5">{{ data.stage_aging.definition }}</p></div>
        <div v-if="data.stage_aging.reason" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6" role="status">{{ data.stage_aging.reason }}</div>
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <MetricCard label="Average days in current stage" :value="data.stage_aging.average_days_in_stage == null ? __('Unknown') : decimal(data.stage_aging.average_days_in_stage)" :note="`${integer(data.stage_aging.known_count)} ${__('Deals with known history')}`" />
          <MetricCard v-for="bucket in data.stage_aging.buckets" :key="bucket.key" :label="bucket.label" :value="integer(bucket.deal_count)" :note="__('Open Deals')" />
        </div>
        <ReportTable v-if="data.stage_aging.by_stage.length" title="Current-stage aging coverage" description="Deal counts reconcile to the readable Open Deal population; averages exclude Unknown history.">
          <template #head><tr><Th>Current Stage</Th><Th right>Deals</Th><Th right>Known</Th><Th right>Unknown</Th><Th right>Average Days</Th></tr></template>
          <tr v-for="stage in data.stage_aging.by_stage" :key="stage.stage || stage.stage_label" class="border-t border-outline-gray-1"><Td>{{ stage.stage_label }}</Td><Td right>{{ integer(stage.deal_count) }}</Td><Td right>{{ integer(stage.known_count) }}</Td><Td right>{{ integer(stage.unknown_count) }}</Td><Td right>{{ stage.average_days_in_stage == null ? __('Unknown') : decimal(stage.average_days_in_stage) }}</Td></tr>
        </ReportTable>
        <ReportTable v-if="data.stage_aging.rows.length" title="Stage Aging drill-down" description="Unknown means readable stage-transition evidence was unavailable or incomplete; unrelated edits never reset this duration.">
          <template #head><tr><Th>Deal</Th><Th>Current Stage</Th><Th>Deal Owner</Th><Th>Stage Entry</Th><Th right>Days in Stage</Th></tr></template>
          <tr v-for="deal in data.stage_aging.rows" :key="deal.name" class="border-t border-outline-gray-1"><Td><RouterLink :to="{ name: 'DealDetail', params: { dealId: deal.name } }" class="font-medium text-[#1D4ED8] hover:underline">{{ deal.deal_title || deal.name }}</RouterLink></Td><Td>{{ deal.stage_label }}</Td><Td>{{ deal.deal_owner || __('Unassigned') }}</Td><Td>{{ deal.stage_entry_date ? displayDate(deal.stage_entry_date) : __('Unknown') }}<span v-if="deal.unknown_reason" class="block max-w-xs whitespace-normal text-xs text-ink-gray-5">{{ deal.unknown_reason }}</span></Td><Td right>{{ deal.days_in_stage == null ? __('Unknown') : integer(deal.days_in_stage) }}</Td></tr>
        </ReportTable>
      </section>
      <div v-else-if="data.stage_aging" class="rounded-lg border border-outline-gray-2 bg-surface-gray-1 px-4 py-3 text-sm text-ink-gray-6" role="status">{{ data.stage_aging.reason }}</div>

      <div v-if="!hasResults" class="rounded-xl border border-dashed border-outline-gray-3 bg-surface-gray-1 px-5 py-12 text-center">
        <h2 class="font-semibold text-ink-gray-9">{{ __('No pipeline activity found') }}</h2>
        <p class="mt-1 text-sm text-ink-gray-5">{{ __('Try another date range or Deal Owner.') }}</p>
      </div>

      <template v-else>
        <section v-if="data.by_stage.length" class="rounded-xl border border-outline-gray-2 bg-surface-white p-4 sm:p-5">
          <h2 class="font-semibold text-ink-gray-9">{{ __('Deal value by current stage') }}</h2>
          <p class="mt-1 text-sm text-ink-gray-5">{{ __('Deals created in the selected range. Select a stage to open the existing filtered Deals view; hover bars for exact values.') }}</p>
          <div class="mt-5 space-y-4" role="img" :aria-label="__('Current Deal value by stage')">
            <RouterLink v-for="stage in data.by_stage" :key="stage.name || stage.label" :to="stageRoute(stage)" class="group block rounded-lg p-2 transition hover:bg-surface-gray-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-outline-gray-3" :title="`${stage.label}: ${integer(stage.deal_count)} Deals; ${money(stage.deal_value)}`">
              <div class="flex flex-wrap items-center justify-between gap-2 text-sm">
                <div class="flex min-w-0 items-center gap-2"><span class="size-2.5 shrink-0 rounded-full" :class="stageColor(stage.stage_type)" /><span class="truncate font-medium text-ink-gray-8">{{ stage.label }}</span><span class="rounded bg-surface-gray-2 px-1.5 py-0.5 text-xs">{{ stage.stage_type }}</span></div>
                <span class="text-ink-gray-6">{{ integer(stage.deal_count) }} {{ __('Deals') }} · {{ money(stage.deal_value) }}</span>
              </div>
              <div class="mt-2 h-3 overflow-hidden rounded-full bg-surface-gray-2"><div class="h-full rounded-full" :class="stageColor(stage.stage_type)" :style="{ width: barWidth(stage.deal_value) }" /></div>
            </RouterLink>
          </div>
        </section>

        <ReportTable v-if="data.lost_reasons.length" title="Lost Reasons" :description="data.rounding_definition">
          <template #head><tr><Th>Reason</Th><Th right>Lost Deals</Th><Th right>Count Share</Th><Th right>Deal Value</Th><Th right>Value Share</Th></tr></template>
          <template v-for="reason in data.lost_reasons" :key="reason.reason">
            <tr class="border-t border-outline-gray-1 font-medium text-ink-gray-8"><Td>{{ reason.reason }}</Td><Td right>{{ integer(reason.deal_count) }}</Td><Td right>{{ percent(reason.count_percentage) }}</Td><Td right>{{ money(reason.deal_value) }}</Td><Td right>{{ percent(reason.value_percentage) }}</Td></tr>
            <tr v-for="deal in reason.deals" :key="deal.name" class="border-t border-outline-gray-1 bg-surface-gray-1 text-xs">
              <Td><RouterLink :to="{ name: 'DealDetail', params: { dealId: deal.name } }" class="text-[#1D4ED8] hover:underline">↳ {{ deal.deal_title || deal.name }}</RouterLink></Td><Td>{{ displayDate(deal.event_date) }}</Td><Td>{{ deal.deal_owner || __('Unassigned') }}</Td><Td right>{{ money(deal.amount) }}</Td><Td />
            </tr>
          </template>
        </ReportTable>

        <RiskTable v-if="data.overdue_deals.length" title="Overdue Open Deal drill-down" :rows="data.overdue_deals" date-label="Expected Close Date" date-field="expected_close_date" />
        <RiskTable v-if="data.stale_deals.length" title="Stale Open Deal drill-down" :rows="data.stale_deals" date-label="Last Modified" date-field="modified" />

        <ReportTable v-if="data.recent_deals.length" title="Recently created Deals" description="Latest 20 readable Deals in the applied Creation range.">
          <template #head><tr><Th>Deal</Th><Th>Stage</Th><Th>Deal Owner</Th><Th>Created</Th><Th right>Deal Value</Th></tr></template>
          <tr v-for="deal in data.recent_deals" :key="deal.name" class="border-t border-outline-gray-1"><Td><RouterLink :to="{ name: 'DealDetail', params: { dealId: deal.name } }" class="font-medium text-[#1D4ED8] hover:underline">{{ deal.deal_title || deal.name }}</RouterLink></Td><Td>{{ deal.stage_label }}</Td><Td>{{ deal.deal_owner || __('Unassigned') }}</Td><Td>{{ displayDate(deal.creation) }}</Td><Td right>{{ money(deal.amount) }}</Td></tr>
        </ReportTable>
      </template>
    </template>

    <div v-else class="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4" aria-live="polite"><div v-for="index in 5" :key="index" class="h-28 animate-pulse rounded-xl bg-surface-gray-2" /></div>
  </div>
</template>

<script setup>
import { computed, defineComponent, h, onMounted, reactive, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { call } from 'frappe-ui'
import ReportsFilters from '@/components/Reports/ReportsFilters.vue'
import { isPermissionError, reportDatePreset } from '@/utils/reportFilters'
import { message, money } from '@/utils/quotation'

const cell = (tag, right, slots) => h(tag, { class: ['whitespace-nowrap px-4 py-3', right ? 'text-right' : 'text-left'] }, slots.default?.())
const Th = defineComponent({ props: { right: Boolean }, setup: (props, { slots }) => () => cell('th', props.right, slots) })
const Td = defineComponent({ props: { right: Boolean }, setup: (props, { slots }) => () => cell('td', props.right, slots) })
const MetricCard = defineComponent({ props: { label: String, value: String, note: String, change: String }, setup: (props) => () => h('article', { class: 'rounded-xl border border-outline-gray-2 bg-surface-white p-4' }, [h('p', { class: 'text-sm text-ink-gray-5' }, props.label), h('p', { class: 'mt-2 text-2xl font-semibold text-ink-gray-9' }, props.value), props.note ? h('p', { class: 'mt-1 text-xs text-ink-gray-5' }, props.note) : null, props.change ? h('p', { class: 'mt-1 text-xs text-ink-gray-6' }, props.change) : null]) })
const ReportTable = defineComponent({ props: { title: String, description: String }, setup: (props, { slots }) => () => h('section', { class: 'overflow-hidden rounded-xl border border-outline-gray-2 bg-surface-white' }, [h('div', { class: 'p-4 sm:p-5' }, [h('h2', { class: 'font-semibold text-ink-gray-9' }, props.title), h('p', { class: 'mt-1 text-sm text-ink-gray-5' }, props.description)]), h('div', { class: 'overflow-x-auto' }, [h('table', { class: 'min-w-full text-left text-sm' }, [h('thead', { class: 'border-y border-outline-gray-2 bg-surface-gray-1 text-ink-gray-5' }, slots.head?.()), h('tbody', { class: 'text-ink-gray-7' }, slots.default?.())])])]) })
const RiskTable = defineComponent({ props: { title: String, rows: Array, dateLabel: String, dateField: String }, setup: (props) => () => h(ReportTable, { title: props.title, description: 'Every readable Open Deal included in this risk aggregate.' }, { head: () => h('tr', [h(Th, 'Deal'), h(Th, 'Stage'), h(Th, 'Deal Owner'), h(Th, props.dateLabel), h(Th, { right: true }, () => 'Deal Value')]), default: () => props.rows.map(deal => h('tr', { class: 'border-t border-outline-gray-1', key: deal.name }, [h(Td, () => h(RouterLink, { to: { name: 'DealDetail', params: { dealId: deal.name } }, class: 'font-medium text-[#1D4ED8] hover:underline' }, () => deal.deal_title || deal.name)), h(Td, deal.stage_label), h(Td, deal.deal_owner || 'Unassigned'), h(Td, displayDate(deal[props.dateField])), h(Td, { right: true }, () => money(deal.amount))])) }) })

const initialRange = reportDatePreset('30-days')
const filters = reactive({ ...initialRange, salesperson: '', comparePrevious: false })
const data = ref(null), loading = ref(false), errorMessage = ref(''), permissionDenied = ref(false)
const appliedFilters = ref(null)
const salespeople = computed(() => data.value?.salespeople || [])
const teamUnsupportedReason = computed(() => data.value?.capabilities?.team_filter?.reason || 'Team filtering is unavailable because DoubleT Deal has no team field.')
const hasResults = computed(() => Boolean(data.value?.deal_count || data.value?.lost_reason_count || data.value?.overdue_open_count || data.value?.stale_open_count || data.value?.forecast?.open_deal_count || data.value?.stage_aging?.rows?.length))
const maxStageValue = computed(() => Math.max(...(data.value?.by_stage || []).map(stage => Number(stage.deal_value) || 0), 0))
const forecastMonths = computed(() => data.value?.forecast?.months || [])
const forecastDeals = computed(() => forecastMonths.value.flatMap(month => (month.deals || []).map(deal => ({ ...deal, forecast_month: month.month }))))
const maxForecastValue = computed(() => Math.max(...forecastMonths.value.map(month => Number(month.unweighted_value) || 0), 0))
const integer = value => new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(Number(value) || 0)
const decimal = value => new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(Number(value) || 0)
const percent = value => `${decimal(value)}%`
const displayDate = value => value ? new Intl.DateTimeFormat('en-US', { dateStyle: 'medium', timeZone: 'UTC' }).format(new Date(`${String(value).slice(0, 10)}T00:00:00Z`)) : ''
const monthLabel = value => value ? new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${value}-01T00:00:00Z`)) : ''
const stageRoute = stage => ({
  name: 'Deals',
  query: {
    ...(stage.name ? { stage: stage.name } : {}),
    creation_start: data.value.filters.start_date,
    creation_end: data.value.filters.end_date,
    ...(data.value.filters.salesperson ? { deal_owner: data.value.filters.salesperson } : {}),
  },
})
const barWidth = value => !maxStageValue.value ? '2%' : `${Math.max((Number(value) / maxStageValue.value) * 100, 2)}%`
const forecastBarWidth = value => !maxForecastValue.value ? '2%' : `${Math.max((Number(value) / maxForecastValue.value) * 100, 2)}%`
const stageColor = type => type === 'WON' ? 'bg-green-500' : type === 'LOST' ? 'bg-red-500' : 'bg-blue-500'
function comparisonChange(metric, format = 'number') {
  const item = data.value?.comparison?.metrics?.[metric]
  if (!item || item.change == null) return ''
  const value = format === 'money' ? money(Math.abs(item.change)) : integer(Math.abs(item.change))
  return `${item.change >= 0 ? '+' : '−'}${value} vs previous period`
}
async function loadReport() {
  loading.value = true; errorMessage.value = ''; permissionDenied.value = false
  try { const request = { start_date: filters.startDate, end_date: filters.endDate, salesperson: filters.salesperson || null, compare_previous: filters.comparePrevious ? 1 : 0 }; data.value = await call('doublet_crm.reports.get_pipeline_analytics', request); appliedFilters.value = request }
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
