import assert from 'node:assert/strict'
import test from 'node:test'

import {
  buildProductListRequest,
  buildSellableProductListRequest,
  groupVariantAttributes,
  hasProductWritePermission,
  productDetailLocation,
  resolveProductImage,
} from '../src/utils/productCatalog.js'

const templates = [
  { name: 'TEMPLATE-1', image: '/files/template.jpg' },
]

test('Product image resolution prefers own image over Template image and placeholder', () => {
  assert.deepEqual(
    resolveProductImage({ product_kind: 'Variant', variant_of: 'TEMPLATE-1', image: '/files/variant.jpg' }, templates),
    { url: '/files/variant.jpg', source: 'product' },
  )
  assert.deepEqual(
    resolveProductImage({ product_kind: 'Variant', variant_of: 'TEMPLATE-1' }, templates),
    { url: '/files/template.jpg', source: 'template' },
  )
  assert.deepEqual(
    resolveProductImage({ product_kind: 'Standard' }, templates),
    { url: '', source: 'placeholder' },
  )
})

test('secondary category filter is applied by the server before later-page pagination', () => {
  const request = buildProductListRequest({
    fields: ['name', 'image'],
    search: 'desk',
    category: 'SECONDARY-CATEGORY',
    status: 'active',
    start: 20,
    pageLength: 20,
  })

  assert.deepEqual(request.filters, [
    ['DoubleT Product Category Assignment', 'category', '=', 'SECONDARY-CATEGORY'],
    ['DoubleT Product', 'is_active', '=', 1],
  ])
  assert.equal(request.limit_start, 20)
  assert.equal(request.limit_page_length, 20)
  assert.equal(request.order_by, '`tabDoubleT Product`.`modified` desc')
  assert.deepEqual(request.or_filters, [
    ['DoubleT Product', 'product_name', 'like', '%desk%'],
    ['DoubleT Product', 'sku', 'like', '%desk%'],
  ])
})

test('sellable catalog combines Category and search before first-page pagination', () => {
  const request = buildSellableProductListRequest({
    fields: ['name', 'product_name', 'sku'],
    search: 'PRD-00016',
    category: 'Vận hành',
    start: 0,
    pageLength: 20,
  })

  assert.deepEqual(request.filters, [
    ['DoubleT Product Category Assignment', 'category', '=', 'Vận hành'],
    ['DoubleT Product', 'is_active', '=', 1],
    ['DoubleT Product', 'product_kind', 'in', ['Standard', 'Variant']],
  ])
  assert.deepEqual(request.or_filters, [
    ['DoubleT Product', 'product_name', 'like', '%PRD-00016%'],
    ['DoubleT Product', 'sku', 'like', '%PRD-00016%'],
  ])
  assert.equal(request.limit_start, 0)
  assert.equal(request.limit_page_length, 20)
  assert.equal(request.order_by, 'product_name asc')
})

test('Product rows and Variant rows target the direct detail route', () => {
  assert.deepEqual(productDetailLocation('PRD-00016'), {
    name: 'ProductDetail',
    params: { productId: 'PRD-00016' },
  })
})

test('Variant attributes are grouped from one child-table response', () => {
  assert.deepEqual(groupVariantAttributes([
    { parent: 'VARIANT-1', attribute_name: 'Color', attribute_value: 'Red' },
    { parent: 'VARIANT-1', attribute_name: 'Size', attribute_value: 'Large' },
    { parent: 'VARIANT-2', attribute_name: 'Color', attribute_value: 'Blue' },
    { parent: '', attribute_name: 'Ignored', attribute_value: 'Row' },
  ]), {
    'VARIANT-1': [
      { name: 'Color', value: 'Red' },
      { name: 'Size', value: 'Large' },
    ],
    'VARIANT-2': [
      { name: 'Color', value: 'Blue' },
    ],
  })
})

test('read-only Product permissions keep detail readable without exposing Edit', () => {
  assert.equal(hasProductWritePermission({ permissions: { read: true, write: false } }), false)
  assert.equal(hasProductWritePermission({ permissions: { read: true, write: true } }), true)
  assert.equal(hasProductWritePermission(null), false)
})
