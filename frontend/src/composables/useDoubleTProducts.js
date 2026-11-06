
import { computed } from 'vue'
import { createListResource } from 'frappe-ui'
import { formatCurrency } from '@/utils'

export function useDoubleTProducts() {
  const productsResource = createListResource({
    doctype: 'DoubleT Product',
    fields: [
      'name',
      'product_name',
      'sku',
      'category',
      'price',
      'description',
      'is_active',
      'modified',
    ],
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

  const columns = [
    { label: 'Product Name', key: 'product_name', width: '240px' },
    { label: 'SKU', key: 'sku', width: '150px' },
    { label: 'Category', key: 'category', width: '180px' },
    { label: 'Price', key: 'price', width: '150px', align: 'right' },
    { label: 'Status', key: 'status', width: '130px' },
  ]

  const rows = computed(() => {
    return (productsResource.data || []).map((product) => ({
      name: product.name,
      product_name: product.product_name || product.name,
      sku: product.sku || '-',
      category: product.category || '-',
      price: formatCurrency(product.price || 0),
      status: {
        label: product.is_active ? 'Active' : 'Inactive',
        color: product.is_active
          ? 'text-green-600'
          : 'text-ink-gray-5',
      },
    }))
  })

  const totalCount = computed(() => productsResource.data?.length || 0)

  return {
    productsResource,
    columns,
    rows,
    totalCount,
    reload: () => productsResource.reload(),
    loadMore: () => productsResource.next(),
  }
}
