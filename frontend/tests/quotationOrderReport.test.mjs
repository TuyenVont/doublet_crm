import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

import {
  isPermissionError,
  previousReportPeriod,
  reportDateError,
  reportDatePreset,
} from '../src/utils/reportFilters.js'

const reportPageSource = readFileSync(
  new URL('../src/pages/ReportsPage.vue', import.meta.url),
  'utf8',
)
const qoReportSource = readFileSync(
  new URL('../src/components/Reports/QuotationOrderReport.vue', import.meta.url),
  'utf8',
)
const filtersSource = readFileSync(
  new URL('../src/components/Reports/ReportsFilters.vue', import.meta.url),
  'utf8',
)

test('Quotation & Order report uses correct API and detail routes', () => {
  assert.match(reportPageSource, /quotation-order/)
  assert.match(reportPageSource, /<QuotationOrderReport/)
  assert.match(qoReportSource, /doublet_crm\.reports\.get_quotation_order/)
  assert.match(qoReportSource, /name: 'QuotationDetail'/)
  assert.match(qoReportSource, /name: 'OrderDetail'/)
  assert.match(qoReportSource, /name: 'DealDetail'/)
  assert.match(qoReportSource, /Quotations/)
  assert.match(qoReportSource, /Quotation Value/)
  assert.match(qoReportSource, /Acceptance Rate/)
  assert.match(qoReportSource, /Booked Sales/)
  assert.match(qoReportSource, /Quotation→Order Rate/)
  assert.match(qoReportSource, /Accepted→Booked Rate/)
  assert.match(qoReportSource, /accepted_conversion_drilldown/)
  assert.match(qoReportSource, /Booked includes Confirmed\/Completed/)
  assert.match(qoReportSource, /compare_previous/)
})

test('Quotation & Order shows status breakdown tables', () => {
  assert.match(qoReportSource, /Quotation status chart/)
  assert.match(qoReportSource, /Order status chart/)
  assert.match(qoReportSource, /statusWidth/)
  assert.match(qoReportSource, /Quotations by Status/)
  assert.match(qoReportSource, /Orders by Status/)
  assert.match(qoReportSource, /Quotation drill-down/)
  assert.match(qoReportSource, /Order drill-down/)
})

test('Quotation & Order distinguishes booked from total values', () => {
  assert.match(qoReportSource, /booked_value/)
  assert.match(qoReportSource, /total_value/)
  assert.match(qoReportSource, /is_booked/)
  assert.match(qoReportSource, /booked_sales/)
  assert.match(qoReportSource, /booked_order_count/)
})

test('Quotation & Order handles permission differences for Deal links', () => {
  assert.match(qoReportSource, /row\.deal_restricted/)
  assert.match(qoReportSource, /percentage\(conversion\?\.quotation_to_order_rate\)/)
  assert.match(qoReportSource, /value == null \? __\('Unavailable'\)/)
})

test('Quotation & Order binds nested summaries and keeps Order-only results visible', () => {
  assert.match(qoReportSource, /data\.value\?\.quotation_summary/)
  assert.match(qoReportSource, /data\.value\?\.order_summary/)
  assert.match(qoReportSource, /quotationSummary\.value\?\.quotation_count \|\| orderSummary\.value\?\.order_count/)
})

test('Quotation & Order reuses shared filters from ReportsFilters', () => {
  assert.match(qoReportSource, /ReportsFilters/)
  assert.match(qoReportSource, /v-model:start-date/)
  assert.match(qoReportSource, /v-model:end-date/)
  assert.match(qoReportSource, /v-model:salesperson/)
  assert.match(qoReportSource, /v-model:compare-previous/)
  assert.match(qoReportSource, /@apply="loadReport"/)
  assert.match(qoReportSource, /@reset="resetFilters"/)
})

test('Quotation & Order uses existing permission error detection', () => {
  assert.match(qoReportSource, /isPermissionError/)
  assert.match(qoReportSource, /permissionDenied/)
})
