
import { computed, reactive } from 'vue'
import { call } from 'frappe-ui'
import { formatCurrency } from '@/utils'
import { buildProductListRequest } from '@/utils/productCatalog'

export function useDoubleTProducts() {
  const pageLength = 20
  const productFields = [
    'name',
    'product_name',
    'sku',
    'product_kind',
    'variant_of',
    'category',
    'image',
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
  const templatesResource = reactive({
    data: [],
    loading: false,
    error: null,
  })
  const categoryAssignmentsResource = reactive({
    data: {},
    loading: false,
    error: null,
  })
  let currentFilters = { search: '', category: '', status: '' }
  let productRequestVersion = 0
  let categoryRequestVersion = 0
  let templateRequestVersion = 0
  let assignmentRequestVersion = 0

  const columns = [
    { label: 'Product Name', key: 'product_name', width: '240px' },
    { label: 'SKU', key: 'sku', width: '150px' },
    { label: 'Kind', key: 'product_kind', width: '130px' },
    { label: 'Category', key: 'category', width: '180px' },
    { label: 'Price', key: 'price', width: '150px', align: 'right' },
    { label: 'Status', key: 'status', width: '130px' },
  ]

  const rows = computed(() => {
    return (productsResource.data || []).map((product) => ({
      name: product.name,
      product_name: product.product_name || product.name,
      sku: product.sku || '-',
      product_kind: product.product_kind || 'Standard',
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
      const data = await call('frappe.client.get_list', buildProductListRequest({
        fields: productFields,
        search,
        category: currentFilters.category,
        status: currentFilters.status,
        start,
        pageLength,
      }))
      if (requestVersion !== productRequestVersion) return

      const page = Array.isArray(data) ? data : []
      productsResource.data = append ? productsResource.data.concat(page) : page
      productsResource.hasNextPage = page.length === pageLength
      await reloadCategoryAssignments(productsResource.data, requestVersion)
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

  async function reloadTemplates() {
    const requestVersion = ++templateRequestVersion
    templatesResource.loading = true
    templatesResource.error = null
    try {
      const data = await call('frappe.client.get_list', {
        doctype: 'DoubleT Product',
        fields: ['name', 'product_name', 'sku', 'image', 'is_active'],
        filters: { product_kind: 'Template' },
        order_by: 'product_name asc',
        limit_page_length: 500,
      })
      if (requestVersion === templateRequestVersion) {
        templatesResource.data = Array.isArray(data) ? data : []
      }
    } catch (error) {
      if (requestVersion === templateRequestVersion) templatesResource.error = error
    } finally {
      if (requestVersion === templateRequestVersion) templatesResource.loading = false
    }
  }

  async function reloadCategoryAssignments(products, productVersion) {
    const requestVersion = ++assignmentRequestVersion
    const names = [...new Set(products.map((product) => product.name).filter(Boolean))]
    if (!names.length) {
      categoryAssignmentsResource.data = {}
      return
    }

    categoryAssignmentsResource.loading = true
    categoryAssignmentsResource.error = null
    try {
      const data = await call('frappe.client.get_list', {
        doctype: 'DoubleT Product Category Assignment',
        parent: 'DoubleT Product',
        fields: ['parent', 'category'],
        filters: [
          ['parent', 'in', names],
          ['parenttype', '=', 'DoubleT Product'],
          ['parentfield', '=', 'categories'],
        ],
        limit_page_length: 5000,
      })
      if (requestVersion !== assignmentRequestVersion || productVersion !== productRequestVersion) return

      const assignments = {}
      for (const row of Array.isArray(data) ? data : []) {
        if (!row.parent || !row.category) continue
        const categories = assignments[row.parent] || (assignments[row.parent] = [])
        if (!categories.includes(row.category)) categories.push(row.category)
      }
      categoryAssignmentsResource.data = assignments
    } catch (error) {
      if (requestVersion === assignmentRequestVersion && productVersion === productRequestVersion) {
        categoryAssignmentsResource.error = error
      }
    } finally {
      if (requestVersion === assignmentRequestVersion) categoryAssignmentsResource.loading = false
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
  reloadTemplates()
  setFilters(currentFilters)

  return {
    productsResource,
    categoriesResource,
    templatesResource,
    categoryAssignmentsResource,
    columns,
    rows,
    totalCount,
    setFilters,
    reload: () => fetchProducts(),
    loadMore: () => fetchProducts({ append: true }),
    reloadTemplates,
  }
}
