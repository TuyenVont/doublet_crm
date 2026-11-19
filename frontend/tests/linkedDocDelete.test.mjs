import assert from 'node:assert/strict'
import test from 'node:test'

import { linkedDocLookupState } from '../src/utils/linkedDocDelete.js'

test('linked document lookup remains locked while loading', () => {
  assert.deepEqual(linkedDocLookupState({ loading: true }), {
    status: 'loading',
    docs: [],
    message: '',
  })
})

test('linked document lookup remains locked after an API error', () => {
  assert.deepEqual(linkedDocLookupState({ error: new Error('Lookup failed') }), {
    status: 'error',
    docs: [],
    message: 'Lookup failed',
  })
})

test('linked documents are returned only after a complete lookup', () => {
  const docs = [{ reference_doctype: 'DoubleT Deal', reference_docname: 'DEAL-001' }]
  assert.deepEqual(linkedDocLookupState({ data: { complete: true, docs } }), {
    status: 'success',
    docs,
    message: '',
  })
})

test('an empty list permits delete only after a complete lookup', () => {
  assert.deepEqual(linkedDocLookupState({ data: { complete: true, docs: [] } }), {
    status: 'success',
    docs: [],
    message: '',
  })
  assert.equal(linkedDocLookupState({ data: { complete: false, docs: [] } }).status, 'error')
})
