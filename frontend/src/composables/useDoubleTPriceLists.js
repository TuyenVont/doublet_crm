import { reactive } from 'vue'
import { call } from 'frappe-ui'

export function useDoubleTPriceLists() {
  const pageLength = 20
  const priceListsResource = reactive({
    data: [],
    loading: false,
    error: null,
    hasNextPage: true,
  })
  let filters = { search: '', status: '' }
  let requestVersion = 0

  function queryFilters() {
    if (filters.status === 'active') return { is_active: 1 }
    if (filters.status === 'inactive') return { is_active: 0 }
    return {}
  }

  async function fetchPriceLists({ append = false } = {}) {
    if (append && (priceListsResource.loading || !priceListsResource.hasNextPage)) return

    const version = ++requestVersion
    const start = append ? priceListsResource.data.length : 0
    if (!append) {
      priceListsResource.data = []
      priceListsResource.hasNextPage = true
    }
    priceListsResource.loading = true
    priceListsResource.error = null

    try {
      const search = filters.search.trim()
      const data = await call('frappe.client.get_list', {
        doctype: 'DoubleT Price List',
        fields: ['name', 'price_list_name', 'is_active', 'is_default', 'modified'],
        filters: queryFilters(),
        or_filters: search
          ? [['price_list_name', 'like', `%${search}%`]]
          : undefined,
        order_by: 'modified desc',
        limit_start: start,
        limit_page_length: pageLength,
      })
      if (version !== requestVersion) return

      const page = Array.isArray(data) ? data : []
      const byName = new Map((append ? priceListsResource.data : []).map((item) => [item.name, item]))
      page.forEach((item) => byName.set(item.name, item))
      priceListsResource.data = [...byName.values()]
      priceListsResource.hasNextPage = page.length === pageLength
    } catch (error) {
      if (version === requestVersion) priceListsResource.error = error
    } finally {
      if (version === requestVersion) priceListsResource.loading = false
    }
  }

  function setFilters(nextFilters) {
    filters = {
      search: nextFilters.search || '',
      status: nextFilters.status || '',
    }
    return fetchPriceLists()
  }

  setFilters(filters)

  return {
    priceListsResource,
    setFilters,
    reload: () => fetchPriceLists(),
    loadMore: () => fetchPriceLists({ append: true }),
  }
}
