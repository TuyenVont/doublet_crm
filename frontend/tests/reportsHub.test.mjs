import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

import {
  getReportSection,
  REPORT_SECTIONS,
  REPORTS_HOME_ROUTE,
} from '../src/utils/reports.js'

const routerSource = readFileSync(new URL('../src/router.js', import.meta.url), 'utf8')
const sidebarSource = readFileSync(
  new URL('../src/components/Layouts/AppSidebar.vue', import.meta.url),
  'utf8',
)
const reportsPageSource = readFileSync(
  new URL('../src/pages/ReportsPage.vue', import.meta.url),
  'utf8',
)
const reportsLayoutSource = readFileSync(
  new URL('../src/pages/ReportsLayout.vue', import.meta.url),
  'utf8',
)
const sidebarLinkSource = readFileSync(
  new URL('../src/components/SidebarLink.vue', import.meta.url),
  'utf8',
)
const liveReportSources = [
  'SalesPerformanceReport', 'PipelineAnalyticsReport', 'QuotationOrderReport',
  'CustomerJourneyReport', 'ActivityContactCenterReport',
].map(name => readFileSync(new URL(`../src/components/Reports/${name}.vue`, import.meta.url), 'utf8'))

test('Reports Hub defines six unique analytical sections', () => {
  assert.equal(REPORT_SECTIONS.length, 6)
  assert.equal(new Set(REPORT_SECTIONS.map(({ key }) => key)).size, 6)
  assert.equal(new Set(REPORT_SECTIONS.map(({ name }) => name)).size, 6)
  assert.deepEqual(REPORT_SECTIONS.map(({ title }) => title), [
    'Sales Performance',
    'Pipeline Analytics',
    'Quotation & Order',
    'Customer Journey',
    'Activity & Contact Center',
    'Smart Insights',
  ])
})

test('every report section has a direct child route under /reports', () => {
  for (const section of REPORT_SECTIONS) {
    assert.match(routerSource, new RegExp(`path: '${section.key}'`))
    assert.match(routerSource, new RegExp(`name: '${section.name}'`))
    assert.equal(getReportSection(section.key), section)
  }
})

test('Reports sidebar and breadcrumb navigate to the landing child route', () => {
  assert.deepEqual(REPORTS_HOME_ROUTE, { name: 'Reports' })
  assert.equal((sidebarSource.match(/label: 'Reports'/g) || []).length, 1)
  assert.match(sidebarSource, /to: REPORTS_HOME_ROUTE/)
  assert.match(reportsPageSource, /:to="REPORTS_HOME_ROUTE"/)
  assert.match(routerSource, /path: '\/reports',[\s\S]*?name: 'ReportsLayout'/)
  assert.match(routerSource, /path: '', name: 'Reports', component: ReportsPage/)
  assert.match(sidebarLinkSource, /if \(!props\.to\) return false/)
  assert.match(sidebarLinkSource, /router\.resolve\(target\)\.matched/)
  assert.match(sidebarLinkSource, /targetRouteNames\.has\(record\.name\)/)
})

test('report pages disclose placeholder status without data requests', () => {
  assert.match(reportsPageSource, /Analytics not yet implemented/)
  assert.doesNotMatch(reportsPageSource, /createResource|frappeRequest|\bcall\s*\(/)
})

test('exports use the last successfully applied filters', () => {
  for (const source of liveReportSources) {
    assert.match(source, /:export-filters="appliedFilters \|\| \{\}"/)
    assert.match(source, /:export-enabled="Boolean\(appliedFilters\)"/)
    assert.match(source, /appliedFilters\.value = request/)
  }
})

test('Reports uses one stable scroll shell and caches tab contents', () => {
  assert.match(reportsLayoutSource, /h-full min-h-0 min-w-0 overflow-hidden/)
  assert.match(reportsPageSource, /overflow-x-hidden overflow-y-scroll/)
  assert.match(reportsPageSource, /<KeepAlive>/)
  assert.match(reportsPageSource, /<component :is="activeReportComponent" :key="report\.key"/)
  assert.match(reportsPageSource, /min-h-\[36rem\]/)
  assert.doesNotMatch(reportsPageSource, /scrollbar-gutter/)
})
