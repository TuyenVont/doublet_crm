export function appendInterestedProductSelections(rows, selections) {
  const existingProducts = new Set(rows.map(row => row.product))
  const existingSkus = new Set(rows.map(row => row.sku).filter(Boolean))
  for (const { product, quantity } of selections) {
    if (!product?.name || existingProducts.has(product.name) || (product.sku && existingSkus.has(product.sku))) continue
    rows.push({
      product: product.name,
      product_name: product.product_name,
      sku: product.sku,
      variant_attributes: (product.variant_attributes || []).join(', '),
      quantity: quantity ?? 1,
      reference_price: '',
    })
    existingProducts.add(product.name)
    if (product.sku) existingSkus.add(product.sku)
  }
  return rows
}
