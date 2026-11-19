import assert from 'node:assert/strict'
import test from 'node:test'

import {
  getCreatePermission,
  getDocumentMutationPermissions,
} from '../src/utils/permissions.js'

test('read-only Contact keeps write and delete actions disabled', async () => {
  const request = async (method) =>
    method === 'frappe.client.has_permission'
      ? { has_permission: false }
      : { permissions: { read: true, create: false, write: false, delete: false } }

  const create = await getCreatePermission(request, 'DoubleT Contact')
  const result = await getDocumentMutationPermissions(
    request,
    'DoubleT Contact',
    'CONTACT-READ-ONLY',
  )

  assert.equal(create.allowed, false)
  assert.deepEqual(result, { write: false, delete: false, error: null })
})

test('writable Contact enables write and delete actions from server permissions', async () => {
  const request = async (method) =>
    method === 'frappe.client.has_permission'
      ? { has_permission: true }
      : { permissions: { read: true, create: true, write: true, delete: true } }

  const create = await getCreatePermission(request, 'DoubleT Contact')
  const result = await getDocumentMutationPermissions(
    request,
    'DoubleT Contact',
    'CONTACT-WRITABLE',
  )

  assert.equal(create.allowed, true)
  assert.deepEqual(result, { write: true, delete: true, error: null })
})

test('permission API errors fail closed for create, write, and delete', async () => {
  const apiError = new Error('Permission API unavailable')
  const request = async () => {
    throw apiError
  }

  const create = await getCreatePermission(request, 'DoubleT Contact')
  const document = await getDocumentMutationPermissions(
    request,
    'DoubleT Contact',
    'CONTACT-ERROR',
  )

  assert.equal(create.allowed, false)
  assert.equal(create.error, apiError)
  assert.equal(document.write, false)
  assert.equal(document.delete, false)
  assert.equal(document.error, apiError)
})
