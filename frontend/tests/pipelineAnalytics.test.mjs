import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

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
  assert.match(reportsPageSource, /report\?\.key === 'pipeline-analytics'/)
  assert.match(reportsPageSource, /<PipelineAnalyticsReport/)
  assert.match(reportsPageSource, /<SalesPerformanceReport v-if=/)
  assert.match(reportsPageSource, /v-else-if="report"/)
  assert.match(reportsPageSource, /'sales-performance', 'pipeline-analytics'/)
})

test('Pipeline Analytics reuses common filters and the focused API', () => {
  assert.match(pipelineSource, /<ReportsFilters/)
  assert.match(pipelineSource, /doublet_crm\.reports\.get_pipeline_analytics/)
  assert.match(pipelineSource, /v-model:start-date/)
  assert.match(pipelineSource, /v-model:salesperson/)
  assert.match(pipelineSource, /Open pipeline value/)
  assert.match(pipelineSource, /data\.business_definition/)
})

test('stage chart and Deal rows use existing SPA routes', () => {
  assert.match(pipelineSource, /name: 'Deals', query: \{ stage: stage\.name \}/)
  assert.match(pipelineSource, /name: 'DealDetail'/)
  assert.match(dealsViewSource, /stage: route\.query\.stage/)
  assert.match(dealsViewSource, /selectedStage = ref\(String\(route\.query\.stage \|\| ''\)\)/)
  assert.match(dealsComposableSource, /dealsResource\.params\.filters = \{\s*stage: options\.stage/)
})

test('pipeline backend remains permission scoped and uses real Deal fields', () => {
  const start = backendSource.indexOf('def get_pipeline_analytics')
  assert.notEqual(start, -1)
  const pipelineApi = backendSource.slice(start)
  assert.match(pipelineApi, /frappe\.has_permission\("DoubleT Deal", "read", throw=True\)/)
  assert.match(pipelineApi, /frappe\.get_list\(\s*"DoubleT Deal"/)
  assert.match(pipelineApi, /\["creation", ">="/)
  assert.match(pipelineApi, /"deal_owner"/)
  assert.match(pipelineApi, /"won_on"/)
  assert.match(pipelineApi, /"lost_on"/)
  assert.match(pipelineApi, /not realized or paid revenue/)
  assert.doesNotMatch(pipelineApi, /ignore_permissions|frappe\.db\.sql/)
})
