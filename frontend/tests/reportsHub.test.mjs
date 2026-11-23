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
const sidebarLinkSource = readFileSync(
  new URL('../src/components/SidebarLink.vue', import.meta.url),
  'utf8',
)

test('Reports Hub defines exactly five unique analytical sections', () => {
  assert.equal(REPORT_SECTIONS.length, 5)
  assert.equal(new Set(REPORT_SECTIONS.map(({ key }) => key)).size, 5)
  assert.equal(new Set(REPORT_SECTIONS.map(({ name }) => name)).size, 5)
  assert.deepEqual(REPORT_SECTIONS.map(({ title }) => title), [
    'Sales Performance',
    'Pipeline Analytics',
    'Quotation & Order',
    'Customer Journey',
    'Activity & Contact Center',
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
