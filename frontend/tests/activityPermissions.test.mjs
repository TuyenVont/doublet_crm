import assert from 'node:assert/strict'
import test from 'node:test'

import {
  getActivityCreatePermissions,
  runCreateAction,
} from '../src/utils/activityPermissions.js'

function permissionRequest(permissions) {
  return async (_method, { doctype }) => ({
    has_permission: Boolean(permissions[doctype]),
  })
}

test('Sales User without create permission cannot open Task or Note forms', async () => {
  const permissions = await getActivityCreatePermissions(
    permissionRequest({ 'DoubleT Task': false, 'DoubleT Note': false }),
  )
  let opened = 0

  assert.deepEqual(permissions, { canCreateTask: false, canCreateNote: false })
  assert.equal(runCreateAction(permissions.canCreateTask, () => opened++), false)
  assert.equal(runCreateAction(permissions.canCreateNote, () => opened++), false)
  assert.equal(opened, 0)
})

test('Sales Manager with create permission can open Task and Note forms', async () => {
  const permissions = await getActivityCreatePermissions(
    permissionRequest({ 'DoubleT Task': true, 'DoubleT Note': true }),
  )
  let opened = 0

  assert.deepEqual(permissions, { canCreateTask: true, canCreateNote: true })
  assert.equal(runCreateAction(permissions.canCreateTask, () => opened++), true)
  assert.equal(runCreateAction(permissions.canCreateNote, () => opened++), true)
  assert.equal(opened, 2)
})

test('permission API errors keep both create actions hidden', async () => {
  const permissions = await getActivityCreatePermissions(async () => {
    throw new Error('Permission lookup failed')
  })

  assert.deepEqual(permissions, { canCreateTask: false, canCreateNote: false })
})
