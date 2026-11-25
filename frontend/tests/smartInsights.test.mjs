import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const page = readFileSync(new URL('../src/pages/ReportsPage.vue', import.meta.url), 'utf8')
const router = readFileSync(new URL('../src/router.js', import.meta.url), 'utf8')
const report = readFileSync(new URL('../src/components/Reports/SmartInsightsReport.vue', import.meta.url), 'utf8')
const dashboard = readFileSync(new URL('../src/pages/Dashboard.vue', import.meta.url), 'utf8')
const actions = readFileSync(new URL('../src/components/Reports/ReportActions.vue', import.meta.url), 'utf8')

test('Smart Insights is a live report with current alert and health UI', () => {
  assert.match(router, /path: 'smart-insights'/)
  assert.match(page, /'smart-insights': SmartInsightsReport/)
  assert.match(report, /doublet_crm\.smart_insights\.get_smart_insights/)
  assert.match(report, /Current alerts/)
  assert.match(report, /Deal Health Score/)
  assert.match(report, /coverage\.known_factors/)
  assert.match(report, /Reading this report never creates Tasks/)
})

test('follow-up is explicit and Dashboard reuses the shared summary routes', () => {
  assert.match(report, /create_follow_up_task/)
  assert.match(report, /Create follow-up/)
  assert.match(report, /!alert\.follow_up\?\.available/)
  assert.match(dashboard, /data\.needs_attention/)
  assert.match(dashboard, /data\.insights_error/)
  assert.match(dashboard, /Existing Dashboard metrics are still available/)
  assert.match(dashboard, /name: 'SmartInsightsReport'/)
  assert.match(dashboard, /router\.push\(alert\.route\)/)
})

test('live reports expose backend export and personal saved filters', () => {
  assert.match(actions, /doublet_crm\.report_tools\.export_report/)
  assert.match(actions, /doublet_crm\.report_tools\.get_saved_filters/)
  assert.match(actions, /doublet_crm\.report_tools\.save_filter/)
  assert.match(actions, /doublet_crm\.report_tools\.delete_filter/)
  assert.match(actions, /new Blob/)
  assert.match(actions, /:disabled="!enabled"/)
  assert.match(actions, /if \(!props\.enabled\) return/)
  assert.match(report, /appliedFilters/)
})

test('Smart Insights buttons stay visually stable and guard duplicate loading requests', () => {
  assert.doesNotMatch(report, /:disabled="loading" class="w-24/)
  assert.match(report, /:aria-disabled="loading"/)
  assert.match(report, /async function load\(\) \{\s*if \(loading\.value\) return/)
  assert.match(report, /function reset\(\) \{ if \(loading\.value\) return;/)
})
