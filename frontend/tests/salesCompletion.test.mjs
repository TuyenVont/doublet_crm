import assert from 'node:assert/strict'
import test from 'node:test'

import { appendInterestedProductSelections } from '../src/utils/dealProducts.js'
import { quotationDraftFromContext } from '../src/utils/quotation.js'

test('Deal catalog adds Standard and Variant once without changing unrelated Deal values', () => {
  const rows = []
  const deal = { amount: 750000, stage: 'Qualified' }
  appendInterestedProductSelections(rows, [
    { product: { name: 'STD-1', product_name: 'Standard', sku: 'SKU-1', variant_attributes: [] }, quantity: 2 },
    { product: { name: 'VAR-1', product_name: 'Variant', sku: 'SKU-2', variant_attributes: ['Color: Blue'] }, quantity: 3 },
    { product: { name: 'VAR-DUP', product_name: 'Duplicate SKU', sku: 'SKU-2', variant_attributes: [] }, quantity: 1 },
  ])
  assert.deepEqual(rows.map(row => [row.product, row.quantity]), [['STD-1', 2], ['VAR-1', 3]])
  assert.equal(rows[1].variant_attributes, 'Color: Blue')
  assert.deepEqual(deal, { amount: 750000, stage: 'Qualified' })
})

test('Deal catalog preserves an invalid zero quantity for backend rejection instead of silently changing it', () => {
  const rows = []
  appendInterestedProductSelections(rows, [
    { product: { name: 'STD-1', product_name: 'Standard', sku: 'SKU-1' }, quantity: 0 },
  ])
  assert.equal(rows[0].quantity, 0)
})

test('Quotation draft copies current priced Deal suggestions into editable item fields only', () => {
  const draft = quotationDraftFromContext({
    deal: 'DEAL-1', customer_type: 'COMPANY', contact: 'CONTACT-1', company: 'COMPANY-1', price_list: 'RETAIL',
    source_lead: 'LEAD-1',
    items: [{
      product: 'VAR-1', product_name: 'Variant', sku: 'SKU-2', quantity: '2', unit_price: '125.00',
      pricing_source: 'price_list', pricing_price_list: 'RETAIL',
    }],
  })
  assert.equal(draft.deal, 'DEAL-1')
  assert.equal(draft.items[0].unit_price, '125.00')
  assert.equal(draft.items[0].discount_type, 'Percentage')
  assert.equal('pricing_source' in draft.items[0], false)
  assert.equal('source_lead' in draft, false)
})
