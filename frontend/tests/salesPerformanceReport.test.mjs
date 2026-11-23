import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

import {
  isPermissionError,
  reportDateError,
  reportDatePreset,
} from '../src/utils/reportFilters.js'

const reportPageSource = readFileSync(
  new URL('../src/pages/ReportsPage.vue', import.meta.url),
  'utf8',
)
const salesReportSource = readFileSync(
  new URL('../src/components/Reports/SalesPerformanceReport.vue', import.meta.url),
  'utf8',
)
const filtersSource = readFileSync(
  new URL('../src/components/Reports/ReportsFilters.vue', import.meta.url),
  'utf8',
)

test('report presets use inclusive calendar-day ranges', () => {
  const today = new Date(2026, 10, 23, 16, 30)
  assert.deepEqual(reportDatePreset('7-days', today), {
    startDate: '2026-11-17',
    endDate: '2026-11-23',
  })
  assert.deepEqual(reportDatePreset('30-days', today), {
    startDate: '2026-10-25',
    endDate: '2026-11-23',
  })
  assert.deepEqual(reportDatePreset('this-month', today), {
    startDate: '2026-11-01',
    endDate: '2026-11-23',
  })
})

test('report date validation rejects missing and reversed dates', () => {
  assert.equal(reportDateError('', '2026-11-23'), 'Start Date and End Date are required.')
  assert.equal(reportDateError('2026-11-24', '2026-11-23'), 'Start Date cannot be after End Date.')
  assert.equal(reportDateError('2026-11-01', '2026-11-23'), '')
})

test('permission failures are distinguished from general request errors', () => {
  assert.equal(isPermissionError({ httpStatusCode: 403 }), true)
  assert.equal(isPermissionError({ exc_type: 'PermissionError' }), true)
  assert.equal(isPermissionError({ message: 'Not permitted to view this document' }), true)
  assert.equal(isPermissionError({ message: 'Network unavailable' }), false)
})

test('Sales Performance uses the focused API and existing detail routes', () => {
  assert.match(reportPageSource, /report\?\.key === 'sales-performance'/)
  assert.match(reportPageSource, /<SalesPerformanceReport/)
  assert.match(salesReportSource, /doublet_crm\.reports\.get_sales_performance/)
  assert.match(salesReportSource, /name: 'OrderDetail'/)
  assert.match(salesReportSource, /name: 'DealDetail'/)
  assert.match(salesReportSource, /Booked sales/)
  assert.match(salesReportSource, /Confirmed \/ Completed orders/)
})

test('common report filters expose dates, presets, Deal Owner, apply and reset', () => {
  for (const text of ['Start Date', 'End Date', '7 days', '30 days', 'This month', 'Salesperson (Deal Owner)', 'Apply', 'Reset']) {
    assert.match(filtersSource, new RegExp(text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')))
  }
  assert.match(filtersSource, /Deal ownership is unavailable with your permissions/)
})
