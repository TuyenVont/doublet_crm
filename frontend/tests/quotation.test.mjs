import assert from 'node:assert/strict'
import test from 'node:test'
import { computed, isReactive, reactive } from 'vue'

import {
  appendCatalogSelections,
  contactsForCustomer,
  createQuotationItem,
  customerFromDeal,
  dealsForCustomer,
  lineAmounts,
  productOptionsForItem,
  shouldRepriceItem,
} from '../src/utils/quotation.js'

const deals = [
  { name: 'DEAL-P1', deal_type: 'PERSONAL', contact: 'CONTACT-1', company: '' },
  { name: 'DEAL-P2', deal_type: 'PERSONAL', contact: 'CONTACT-2', company: '' },
  { name: 'DEAL-C1', deal_type: 'COMPANY', contact: 'CONTACT-1', company: 'COMPANY-1' },
  { name: 'DEAL-C2', deal_type: 'COMPANY', contact: 'CONTACT-2', company: 'COMPANY-1' },
]

test('Personal customer exposes only Deals for the required Contact', () => {
  const result = dealsForCustomer(deals, { customer_type: 'PERSONAL', contact: 'CONTACT-1' })
  assert.deepEqual(result.map(row => row.name), ['DEAL-P1'])
  assert.deepEqual(dealsForCustomer(deals, { customer_type: 'PERSONAL', contact: '' }), [])
})

test('Company Contact choices and Deals stay inside the selected Company', () => {
  const contacts = [
    { name: 'CONTACT-1', company: 'COMPANY-1' },
    { name: 'CONTACT-OTHER', company: 'COMPANY-2' },
  ]
  assert.deepEqual(
    contactsForCustomer(contacts, { customer_type: 'COMPANY', company: 'COMPANY-1' }).map(row => row.name),
    ['CONTACT-1'],
  )
  assert.deepEqual(
    dealsForCustomer(deals, { customer_type: 'COMPANY', company: 'COMPANY-1', contact: 'CONTACT-OTHER' }),
    [],
  )
})

test('changing customer makes the previously linked Deal ineligible', () => {
  const changedCustomer = { customer_type: 'PERSONAL', contact: 'CONTACT-2' }
  assert.equal(dealsForCustomer(deals, changedCustomer).some(row => row.name === 'DEAL-P1'), false)
})

test('Deal-first creation derives the complete customer context', () => {
  assert.deepEqual(customerFromDeal(deals[2]), {
    customer_type: 'COMPANY',
    contact: 'CONTACT-1',
    company: 'COMPANY-1',
  })
})

test('Price List changes reprice only new automatic lines', () => {
  assert.equal(shouldRepriceItem({ product: 'PRODUCT-1', unit_price: '10.00' }, { auto: true, manual: false }), true)
  assert.equal(shouldRepriceItem({ product: 'PRODUCT-1', unit_price: '10.00' }, { auto: false, manual: true }), false)
  assert.equal(shouldRepriceItem({ name: 'ROW-1', product: 'PRODUCT-1', unit_price: '10.00' }, { auto: true, manual: false }), false)
})

test('catalog adds a Variant at quantity 2 through the current Price List pricing callback', async () => {
  const items = []
  const pricingContext = { price_list: 'RETAIL-USD' }
  const calls = []
  await appendCatalogSelections(items, [{
    product: { name: 'VARIANT-BLUE', product_name: 'Variant Blue', sku: 'VAR-BLUE' },
    quantity: 2,
  }], async item => {
    calls.push({ product: item.product, price_list: pricingContext.price_list })
    item.unit_price = '19.99'
  })

  assert.deepEqual(calls, [{ product: 'VARIANT-BLUE', price_list: 'RETAIL-USD' }])
  assert.equal(items[0].quantity, 2)
  assert.equal(items[0].unit_price, '19.99')
})

test('selected Product options stay visible outside the current search page without duplicates', () => {
  const currentSearch = [{ name: 'DV-MKT-001', product_name: 'Dịch vụ quảng cáo TikTok', sku: 'DV-MKT-001' }]
  const addItemRow = createQuotationItem()
  Object.assign(addItemRow, { product: '098', product_name: 'Tăng tương tác', sku: '098' })
  const catalogRow = createQuotationItem({ name: 'PRD-00016', product_name: 'Ổi', sku: 'PRD-00016' }, 2)

  assert.deepEqual(productOptionsForItem(currentSearch, addItemRow).map(product => product.name), ['098', 'DV-MKT-001'])
  assert.deepEqual(productOptionsForItem(currentSearch, catalogRow).map(product => product.name), ['PRD-00016', 'DV-MKT-001'])
  assert.strictEqual(productOptionsForItem(currentSearch, { product: 'DV-MKT-001' }), currentSearch)
})

test('catalog async pricing updates totals after totals were read with pending prices', async () => {
  const items = reactive([{
    product: '098',
    product_name: 'Tăng tương tác',
    sku: '098',
    quantity: 1,
    unit_price: '123.45',
    discount_type: 'Amount',
    discount_amount: '7.89',
    discount_percent: 0,
  }])
  const totals = computed(() => items.reduce((sum, item) => {
    const amounts = lineAmounts(item)
    sum.gross += amounts.gross
    sum.discount += amounts.discount
    sum.total += amounts.total
    return sum
  }, { gross: 0, discount: 0, total: 0 }))
  const releases = {}

  const pricing = appendCatalogSelections(items, [
    { product: { name: 'PRD-00016', product_name: 'Ổi', sku: 'PRD-00016' }, quantity: 2 },
    { product: { name: 'DV-MKT-001', product_name: 'Dịch vụ quảng cáo TikTok', sku: 'DV-MKT-001' }, quantity: 1 },
  ], async item => {
    assert.equal(isReactive(item), true)
    await new Promise(resolve => { releases[item.product] = resolve })
    item.unit_price = item.product === 'PRD-00016' ? '500' : '56000'
  })

  assert.deepEqual(totals.value, { gross: 123.45, discount: 7.89, total: 115.56 })
  releases['PRD-00016']()
  releases['DV-MKT-001']()
  await pricing
  assert.deepEqual(totals.value, { gross: 57123.45, discount: 7.89, total: 57115.56 })
})

test('catalog multi-add preserves every field on existing saved and manual lines', async () => {
  const saved = { name: 'ROW-1', product: 'OLD-1', quantity: 3, unit_price: '7.50', discount_percent: 12 }
  const manual = { product: 'OLD-2', quantity: 4, unit_price: '8.25', discount_type: 'Amount', discount_amount: 2 }
  const before = structuredClone([saved, manual])
  const items = [saved, manual]

  await appendCatalogSelections(items, [
    { product: { name: 'NEW-1', product_name: 'New One', sku: 'NEW-1' }, quantity: 1 },
    { product: { name: 'NEW-2', product_name: 'New Two', sku: 'NEW-2' }, quantity: 5 },
  ], async item => { item.unit_price = '10.00' })

  assert.strictEqual(items[0], saved)
  assert.strictEqual(items[1], manual)
  assert.deepEqual(items.slice(0, 2), before)
  assert.deepEqual(items.slice(2).map(item => [item.product, item.quantity]), [['NEW-1', 1], ['NEW-2', 5]])
})
