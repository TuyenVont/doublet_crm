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
const journeyReportSource = readFileSync(
  new URL('../src/components/Reports/CustomerJourneyReport.vue', import.meta.url),
  'utf8',
)
const filtersSource = readFileSync(
  new URL('../src/components/Reports/ReportsFilters.vue', import.meta.url),
  'utf8',
)

test('Customer Journey report uses correct API and detail routes', () => {
  assert.match(reportPageSource, /customer-journey/)
  assert.match(reportPageSource, /<CustomerJourneyReport/)
  assert.match(journeyReportSource, /doublet_crm\.reports\.get_customer_journey/)
  assert.match(journeyReportSource, /name: 'LeadDetail'/)
  assert.match(journeyReportSource, /name: 'DealDetail'/)
  assert.match(journeyReportSource, /Lead to Deal Rate/)
  assert.match(journeyReportSource, /Deal to Order Rate/)
  assert.match(journeyReportSource, /Conversion funnel/)
  assert.match(journeyReportSource, /Lead journey drill-down/)
  assert.match(journeyReportSource, /compare_previous/)
})

test('Customer Journey shows funnel stages (Lead, Deal, Quotation, Order)', () => {
  assert.match(journeyReportSource, /v-for="\(stage, index\) in data\.funnel"/)
  assert.match(journeyReportSource, /stage\.stage/)
  assert.match(journeyReportSource, /'Lead': 'text-ink-gray-5'/)
  assert.match(journeyReportSource, /'Order': 'text-ink-green-6 font-medium'/)
})

test('Customer Journey handles permission differences for linked records', () => {
  assert.match(journeyReportSource, /metric\(data\.deal_count\)/)
  assert.match(journeyReportSource, /percentage\(data\.deal_to_order_rate\)/)
  assert.match(journeyReportSource, /value == null \? __\('Unavailable'\)/)
})

test('Customer Journey separates entity totals and scales funnel from data', () => {
  assert.match(journeyReportSource, /data\.entity_totals\.deals/)
  assert.match(journeyReportSource, /Unique cohort Leads reaching each stage/)
  assert.match(journeyReportSource, /maxFunnelCount/)
  assert.match(journeyReportSource, /Number\(count\) \/ maxFunnelCount\.value/)
})

test('Customer Journey reuses shared filters from ReportsFilters', () => {
  assert.match(journeyReportSource, /ReportsFilters/)
  assert.match(journeyReportSource, /v-model:start-date/)
  assert.match(journeyReportSource, /v-model:end-date/)
  assert.match(journeyReportSource, /v-model:salesperson/)
  assert.match(journeyReportSource, /v-model:compare-previous/)
  assert.match(journeyReportSource, /@apply="loadReport"/)
  assert.match(journeyReportSource, /@reset="resetFilters"/)
})

test('Customer Journey uses existing permission error detection', () => {
  assert.match(journeyReportSource, /isPermissionError/)
  assert.match(journeyReportSource, /permissionDenied/)
})
