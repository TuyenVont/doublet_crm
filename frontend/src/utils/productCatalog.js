export function resolveProductImage(product, templates = []) {
  const ownImage = String(product?.image || '').trim()
  if (ownImage) return { url: ownImage, source: 'product' }

  if (product?.product_kind === 'Variant' && product.variant_of) {
    const template = Array.isArray(templates)
      ? templates.find((row) => row.name === product.variant_of)
      : templates[product.variant_of]
    const templateImage = String(template?.image || '').trim()
    if (templateImage) return { url: templateImage, source: 'template' }
  }

  return { url: '', source: 'placeholder' }
}

export function productDetailLocation(productName) {
  return { name: 'ProductDetail', params: { productId: productName } }
}

export function hasProductWritePermission(response) {
  return Boolean(response?.permissions?.write)
}

export function groupVariantAttributes(rows) {
  const grouped = {}
  for (const row of Array.isArray(rows) ? rows : []) {
    if (!row?.parent || !row.attribute_name || !row.attribute_value) continue
    const attributes = grouped[row.parent] || (grouped[row.parent] = [])
    attributes.push({
      name: row.attribute_name,
      value: row.attribute_value,
    })
  }
  return grouped
}

export function buildProductListRequest({ fields, search = '', category = '', status = '', start = 0, pageLength = 20 }) {
  const filters = []
  if (category) {
    filters.push(['DoubleT Product Category Assignment', 'category', '=', category])
  }
  if (status === 'active') filters.push(['DoubleT Product', 'is_active', '=', 1])
  if (status === 'inactive') filters.push(['DoubleT Product', 'is_active', '=', 0])

  const query = search.trim()
  return {
    doctype: 'DoubleT Product',
    fields,
    filters,
    or_filters: query
      ? [
          ['DoubleT Product', 'product_name', 'like', `%${query}%`],
          ['DoubleT Product', 'sku', 'like', `%${query}%`],
        ]
      : undefined,
    order_by: '`tabDoubleT Product`.`modified` desc',
    limit_start: start,
    limit_page_length: pageLength,
  }
}

export function buildSellableProductListRequest({ fields, search = '', category = '', start = 0, pageLength = 20 }) {
  const request = buildProductListRequest({
    fields,
    search,
    category,
    status: 'active',
    start,
    pageLength,
  })
  request.filters.push(['DoubleT Product', 'product_kind', 'in', ['Standard', 'Variant']])
  request.order_by = 'product_name asc'
  return request
}
