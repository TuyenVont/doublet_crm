
import { computed, reactive } from 'vue'
import { call } from 'frappe-ui'
import { formatCurrency } from '@/utils'

export function useDoubleTProducts() {
  const pageLength = 20
  const productFields = [
    'name',
    'product_name',
    'sku',
    'category',
    'price',
    'description',
    'is_active',
    'modified',
  ]
  const productsResource = reactive({
    data: [],
    loading: false,
    error: null,
    hasNextPage: true,
  })
  const categoriesResource = reactive({
    data: [],
    loading: false,
    error: null,
  })
  let currentFilters = { search: '', category: '', status: '' }
  let productRequestVersion = 0
  let categoryRequestVersion = 0

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

  function getQueryFilters() {
    const filters = {}
    if (currentFilters.category) filters.category = currentFilters.category
    if (currentFilters.status === 'active') filters.is_active = 1
    if (currentFilters.status === 'inactive') filters.is_active = 0
    return filters
  }

  async function fetchProducts({ append = false } = {}) {
    if (append && (productsResource.loading || !productsResource.hasNextPage)) return

    const requestVersion = ++productRequestVersion
    const start = append ? productsResource.data.length : 0
    if (!append) {
      productsResource.data = []
      productsResource.hasNextPage = true
    }
    productsResource.loading = true
    productsResource.error = null

    const search = currentFilters.search.trim()
    try {
      const data = await call('frappe.client.get_list', {
        doctype: 'DoubleT Product',
        fields: productFields,
        filters: getQueryFilters(),
        or_filters: search
          ? [
              ['product_name', 'like', `%${search}%`],
              ['sku', 'like', `%${search}%`],
            ]
          : undefined,
        order_by: 'modified desc',
        limit_start: start,
        limit_page_length: pageLength,
      })
      if (requestVersion !== productRequestVersion) return

      const page = Array.isArray(data) ? data : []
      productsResource.data = append ? productsResource.data.concat(page) : page
      productsResource.hasNextPage = page.length === pageLength
    } catch (error) {
      if (requestVersion !== productRequestVersion) return
      productsResource.error = error
    } finally {
      if (requestVersion === productRequestVersion) {
        productsResource.loading = false
      }
    }
  }

  async function reloadCategories() {
    const requestVersion = ++categoryRequestVersion
    categoriesResource.loading = true
    categoriesResource.error = null
    try {
      const data = await call('frappe.client.get_list', {
        doctype: 'DoubleT Product Category',
        fields: ['name', 'category_name'],
        order_by: 'category_name asc',
        limit_page_length: 500,
      })
      if (requestVersion === categoryRequestVersion) {
        categoriesResource.data = Array.isArray(data) ? data : []
      }
    } catch (error) {
      if (requestVersion === categoryRequestVersion) categoriesResource.error = error
    } finally {
      if (requestVersion === categoryRequestVersion) categoriesResource.loading = false
    }
  }

  function setFilters(filters) {
    currentFilters = {
      search: filters.search || '',
      category: filters.category || '',
      status: filters.status || '',
    }
    return fetchProducts()
  }

  // Product and category lists are independent server-side queries so filters
  // remain complete even when only one product page is loaded.
  reloadCategories()
  setFilters(currentFilters)

  return {
    productsResource,
    categoriesResource,
    columns,
    rows,
    totalCount,
    setFilters,
    reload: () => fetchProducts(),
    loadMore: () => fetchProducts({ append: true }),
  }
}
