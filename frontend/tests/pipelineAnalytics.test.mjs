import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

import { buildDealListFilters } from '../src/utils/dealFilters.js'

const reportsPageSource = readFileSync(
  new URL('../src/pages/ReportsPage.vue', import.meta.url),
  'utf8',
)
const pipelineSource = readFileSync(
  new URL('../src/components/Reports/PipelineAnalyticsReport.vue', import.meta.url),
  'utf8',
)
const dealsViewSource = readFileSync(
  new URL('../src/pages/DealsView.vue', import.meta.url),
  'utf8',
)
const dealsComposableSource = readFileSync(
  new URL('../src/composables/useDoubleTDeals.js', import.meta.url),
  'utf8',
)
const backendSource = readFileSync(
  new URL('../../doublet_crm/reports.py', import.meta.url),
  'utf8',
)

test('Pipeline Analytics replaces only its Reports placeholder', () => {
  assert.match(reportsPageSource, /'pipeline-analytics': PipelineAnalyticsReport/)
  assert.match(reportsPageSource, /<component :is="activeReportComponent"/)
  assert.match(reportsPageSource, /<KeepAlive>/)
  assert.match(reportsPageSource, /v-else-if="report"/)
  assert.match(reportsPageSource, /'sales-performance', 'pipeline-analytics'/)
})

test('Pipeline Analytics reuses common filters and the focused API', () => {
  assert.match(pipelineSource, /<ReportsFilters/)
  assert.match(pipelineSource, /doublet_crm\.reports\.get_pipeline_analytics/)
  assert.match(pipelineSource, /v-model:start-date/)
  assert.match(pipelineSource, /v-model:salesperson/)
  assert.match(pipelineSource, /Open Pipeline Value/)
  assert.match(pipelineSource, /data\.business_definition/)
  assert.match(pipelineSource, /Lost Reasons/)
  assert.match(pipelineSource, /Overdue Open Deal drill-down/)
  assert.match(pipelineSource, /Stale Open Deal drill-down/)
  assert.match(pipelineSource, /Monthly Sales Forecast/)
  assert.match(pipelineSource, /Forecast Deal drill-down/)
  assert.match(pipelineSource, /not actual booked sales/)
  assert.match(pipelineSource, /Stage Aging drill-down/)
  assert.match(pipelineSource, /Average days in current stage/)
  assert.match(pipelineSource, /deal\.unknown_reason/)
  assert.match(pipelineSource, /compare_previous/)
})

test('stage chart and Deal rows use existing SPA routes', () => {
  assert.match(pipelineSource, /creation_start: data\.value\.filters\.start_date/)
  assert.match(pipelineSource, /creation_end: data\.value\.filters\.end_date/)
  assert.match(pipelineSource, /deal_owner: data\.value\.filters\.salesperson/)
  assert.match(pipelineSource, /name: 'DealDetail'/)
  assert.match(dealsViewSource, /creationStart: route\.query\.creation_start/)
  assert.match(dealsViewSource, /creationEnd: route\.query\.creation_end/)
  assert.match(dealsViewSource, /dealOwner: route\.query\.deal_owner/)
  assert.match(dealsViewSource, /selectedStage = ref\(String\(route\.query\.stage \|\| ''\)\)/)
  assert.match(dealsComposableSource, /buildDealListFilters\(options\)/)
})

test('Deal list resource supports the exact Pipeline aggregate filter tuple', () => {
  assert.deepEqual(buildDealListFilters({
    stage: 'Qualified',
    dealOwner: 'owner@example.com',
    creationStart: '2026-11-01',
    creationEnd: '2026-11-30',
  }), {
    stage: 'Qualified',
    deal_owner: 'owner@example.com',
    creation: ['between', ['2026-11-01 00:00:00', '2026-11-30 23:59:59.999999']],
  })
})

test('pipeline backend remains permission scoped and uses real Deal fields', () => {
  const start = backendSource.indexOf('def get_pipeline_analytics')
  assert.notEqual(start, -1)
  const pipelineApi = backendSource.slice(start)
  assert.match(pipelineApi, /frappe\.has_permission\("DoubleT Deal", "read", throw=True\)/)
  assert.match(backendSource, /frappe\.get_list\(\s*"DoubleT Deal"/)
  assert.match(backendSource, /\["creation", ">="/)
  assert.match(backendSource, /"deal_owner"/)
  assert.match(backendSource, /"won_on"/)
  assert.match(backendSource, /"lost_on"/)
  assert.match(pipelineApi, /_summarize_lost_reasons/)
  assert.match(pipelineApi, /STALE_DEAL_DAYS/)
  assert.match(pipelineApi, /not paid revenue/)
  assert.match(pipelineApi, /not historical stage snapshots/)
  assert.match(backendSource, /def _summarize_forecast/)
  assert.match(backendSource, /total_unweighted_pipeline_value/)
  assert.match(backendSource, /Weighted forecast is unavailable/)
  assert.match(backendSource, /_pipeline_stage_aging/)
  assert.doesNotMatch(pipelineApi, /ignore_permissions|frappe\.db\.sql/)
})
