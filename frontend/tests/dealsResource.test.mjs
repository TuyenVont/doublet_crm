import assert from 'node:assert/strict'
import { mkdtemp, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { test } from 'node:test'
import { createServer } from 'vite'
import { effectScope, ref } from 'vue'

const root = fileURLToPath(new URL('..', import.meta.url))
const frappeSource = new URL('.', import.meta.resolve('frappe-ui'))

test('Deals sends filters through the frappe-ui list resource and preserves them across pages and reload', { timeout: 10000 }, async (t) => {
  const cacheDir = await mkdtemp(join(tmpdir(), 'doublet-deals-test-'))
  t.after(() => rm(cacheDir, { recursive: true, force: true }))
  const vite = await createServer({
    cacheDir,
    optimizeDeps: { noDiscovery: true, include: [] },
    root,
    configFile: false,
    server: { middlewareMode: true, watch: null, ws: false },
    resolve: {
      alias: [
        { find: /^@\/utils$/, replacement: 'virtual:deal-formatters' },
        { find: '@', replacement: fileURLToPath(new URL('../src', import.meta.url)) },
        { find: 'frappe-ui', replacement: 'virtual:frappe-ui-resource' },
      ],
    },
    plugins: [{
      name: 'frappe-ui-resource-for-test',
      resolveId(id) {
        if (id.startsWith('virtual:')) return '\0' + id
      },
      load(id) {
        if (id === '\0virtual:deal-formatters') {
          return 'export const formatDate = String, timeAgo = String, formatCurrency = String'
        }
        if (id !== '\0virtual:frappe-ui-resource') return
        const source = (path) => JSON.stringify(fileURLToPath(new URL(path, frappeSource)))
        return [
          `export { createListResource } from ${source('resources/listResource.js')}`,
          `export { default as call } from ${source('utils/call.js')}`,
          `export { setConfig, getConfig } from ${source('utils/config.ts')}`,
        ].join('\n')
      },
    }],
  })
  const scope = effectScope()
  t.after(async () => {
    scope.stop()
    await vite.close()
  })

  const listRequests = []
  const stages = [
    { name: 'qualified', stage_type: 'OPEN' },
    { name: 'proposal', stage_type: 'OPEN' },
    { name: 'won', stage_type: 'WON' },
  ]
  let nextRequest
  let failNextRequest = false
  const waitForList = () => new Promise((resolve) => { nextRequest = resolve })
  t.mock.method(globalThis, 'fetch', async (url, { body }) => {
    assert.equal(url, '/api/method/frappe.client.get_list')
    assert.equal(JSON.parse(body).doctype, 'DoubleT Deal Stage')
    return Response.json({ message: stages })
  })
  globalThis.window = { location: { hostname: 'localhost' } }
  t.after(() => { delete globalThis.window })

  const { setConfig } = await vite.ssrLoadModule('virtual:frappe-ui-resource')
  setConfig('resourceFetcher', async ({ url, params }) => {
    assert.equal(url, 'frappe.client.get_list')
    assert.equal(params.doctype, 'DoubleT Deal')
    if (failNextRequest) {
      failNextRequest = false
      throw new Error('Connection lost')
    }
    listRequests.push(JSON.parse(JSON.stringify(params)))
    const remaining = params.filters.stage === 'won' ? 1 : 25 - params.limit_start
    const rows = Array.from({ length: Math.min(params.limit_page_length, remaining) }, (_, index) => ({
      name: `deal-${params.limit_start + index}`,
    }))
    nextRequest?.()
    return rows
  })

  const { useDoubleTDeals } = await vite.ssrLoadModule('/src/composables/useDoubleTDeals.js')
  const ownerAndDate = {
    dealOwner: 'qa@example.com',
    creationStart: '2026-11-01',
    creationEnd: '2026-11-28',
  }
  const filters = {
    deal_owner: ownerAndDate.dealOwner,
    creation: ['between', ['2026-11-01 00:00:00', '2026-11-28 23:59:59.999999']],
  }
  const options = ref({ lifecycle: 'OPEN', ...ownerAndDate })
  const initial = waitForList()
  const { dealsResource, loadMore, reload } = scope.run(() => useDoubleTDeals(() => options.value))
  await initial
  await dealsResource.list.promise
  const openFilters = { ...filters, stage: ['in', ['qualified', 'proposal']] }
  assert.deepEqual(listRequests[0].filters, openFilters)
  assert.equal(listRequests[0].limit_start, 0)
  assert.equal(dealsResource.data.length, 20)

  loadMore()
  await dealsResource.list.promise
  assert.equal(listRequests[1].limit_start, 20)
  assert.deepEqual(listRequests[1].filters, openFilters)
  assert.equal(dealsResource.data.length, 25)
  assert.equal(dealsResource.hasNextPage, false)

  await reload()
  assert.equal(listRequests[2].limit_start, 0)
  assert.equal(listRequests[2].limit_page_length, 25)
  assert.deepEqual(listRequests[2].filters, openFilters)
  assert.equal(dealsResource.data.length, 25)

  failNextRequest = true
  await assert.rejects(reload(), /Connection lost/)

  const stageChange = waitForList()
  options.value = { stage: 'won', ...ownerAndDate }
  await stageChange
  await dealsResource.list.promise
  assert.equal(listRequests[3].limit_start, 0)
  assert.deepEqual(listRequests[3].filters, { ...filters, stage: 'won' })
  assert.equal(dealsResource.data.length, 1)

  const clear = waitForList()
  options.value = {}
  await clear
  await dealsResource.list.promise
  assert.equal(listRequests[4].limit_start, 0)
  assert.deepEqual(listRequests[4].filters, {})
})
