import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import test from 'node:test'

const source = readFileSync(
  new URL('../src/components/Reports/ActivityContactCenterReport.vue', import.meta.url),
  'utf8',
)

test('Activity report keeps permission-aware metrics and drill-down routes', () => {
  assert.match(source, /value == null \? __\('Unavailable'\)/)
  assert.match(source, /name: 'CallHistoryDetail'/)
  assert.match(source, /name: 'Tasks'/)
  assert.match(source, /v-if="item\.conversation"/)
  assert.match(source, /name: 'Inbox'/)
})

test('Activity report keeps employee selection and unsupported source labels', () => {
  assert.match(source, /v-model:salesperson="filters\.employee"/)
  assert.match(source, /sources\.email\.unsupported_filter_reason/)
  assert.match(source, /sources\.zalo\.unsupported_filter_reason/)
  assert.match(source, /filters\.employee \|\| null/)
})

test('Activity report exposes channel applicability without inventing Email or Zalo ownership', () => {
  assert.match(source, /All channels/)
  assert.match(source, /filters\.channel/)
  assert.match(source, /Call Agent and Task Assignee only/)
  assert.match(source, /Email and Zalo attribution is unavailable/)
  assert.match(source, /sources\.calls\.selected/)
})
