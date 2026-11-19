import assert from 'node:assert/strict'
import test from 'node:test'

import {
  currentUserDisplayName,
  normalizeSessionUser,
} from '../src/utils/userDisplay.js'

const profiles = {
  Administrator: { name: 'Administrator', full_name: 'Administrator' },
  'salesuser@gmail.com': {
    name: 'salesuser@gmail.com',
    full_name: 'Sales User A',
  },
  'salesmanager@gmail.com': {
    name: 'salesmanager@gmail.com',
    full_name: 'Sales Manager',
  },
}

const getUser = (userId) => profiles[userId]

test('shows the resolved full name for Administrator and sales accounts', () => {
  assert.equal(
    currentUserDisplayName('Administrator', getUser, 'Not signed in'),
    'Administrator',
  )
  assert.equal(
    currentUserDisplayName('salesuser@gmail.com', getUser, 'Not signed in'),
    'Sales User A',
  )
  assert.equal(
    currentUserDisplayName('salesmanager@gmail.com', getUser, 'Not signed in'),
    'Sales Manager',
  )
})

test('shows the exact user ID while the profile is temporary, missing, or errors', () => {
  const temporary = () => ({
    name: 'salesuser@gmail.com',
    full_name: 'salesuser',
    __isTemporaryProfile: true,
  })
  const failing = () => {
    throw new Error('Profile lookup failed')
  }

  assert.equal(
    currentUserDisplayName('salesuser@gmail.com', temporary, 'Not signed in'),
    'salesuser@gmail.com',
  )
  assert.equal(
    currentUserDisplayName('salesuser@gmail.com', () => null, 'Not signed in'),
    'salesuser@gmail.com',
  )
  assert.equal(
    currentUserDisplayName('salesuser@gmail.com', failing, 'Not signed in'),
    'salesuser@gmail.com',
  )
})

test('shows a neutral label without an authenticated identity', () => {
  assert.equal(normalizeSessionUser(null), '')
  assert.equal(normalizeSessionUser(''), '')
  assert.equal(normalizeSessionUser('Guest'), '')
  assert.equal(currentUserDisplayName(null, getUser, 'Not signed in'), 'Not signed in')
  assert.equal(currentUserDisplayName('Guest', getUser, 'Not signed in'), 'Not signed in')
})

test('a late old profile cannot replace the current session name', async () => {
  let currentUserId = 'salesuser@gmail.com'
  const loadedProfiles = {
    'salesmanager@gmail.com': profiles['salesmanager@gmail.com'],
  }
  const lookup = (userId) => loadedProfiles[userId]

  let resolveOldProfile
  const oldProfileRequest = new Promise((resolve) => {
    resolveOldProfile = resolve
  }).then((profile) => {
    loadedProfiles['salesuser@gmail.com'] = profile
  })

  assert.equal(
    currentUserDisplayName(currentUserId, lookup, 'Not signed in'),
    'salesuser@gmail.com',
  )

  currentUserId = 'salesmanager@gmail.com'
  assert.equal(
    currentUserDisplayName(currentUserId, lookup, 'Not signed in'),
    'Sales Manager',
  )

  resolveOldProfile(profiles['salesuser@gmail.com'])
  await oldProfileRequest

  assert.equal(
    currentUserDisplayName(currentUserId, lookup, 'Not signed in'),
    'Sales Manager',
  )
})
