import { computed, onUnmounted, reactive, ref, watch } from 'vue'
import { call } from 'frappe-ui'
import { formatDate, timeAgo } from '@/utils'

const PAGE_SIZE = 20

export function useDoubleTCompanies() {
  const companiesResource = reactive({
    data: [],
    loading: false,
    error: null,
    hasNextPage: false,
  })

  const searchQuery = ref('')
  const selectedIndustry = ref('')
  const industryOptions = ref([])
  const totalCount = ref(0)
  const offset = ref(0)

  let searchTimer = null
  let activeRequest = 0

  const fields = [
    'name',
    'company_name',
    'tax_id',
    'phone',
    'email',
    'website',
    'address',
    'industry',
    'size',
    'company_owner',
    'modified',
    'creation',
    'owner',
  ]

  const columns = [
    { label: 'Company Name', key: 'company_name', width: '220px' },
    { label: 'Industry', key: 'industry', width: '170px' },
    { label: 'Size', key: 'size', width: '120px' },
    { label: 'Email', key: 'email', width: '210px' },
    { label: 'Phone', key: 'phone', width: '150px' },
    { label: 'Website', key: 'website', width: '200px' },
    { label: 'Owner', key: 'company_owner', width: '160px' },
    { label: 'Last Modified', key: 'modified', width: '140px' },
  ]

  const rows = computed(() =>
    companiesResource.data.map((company) => ({
      name: company.name,

      company_name:
        company.company_name || company.name,

      industry:
        company.industry || '-',

      size:
        company.size || '-',

      email:
        company.email || '-',

      phone:
        company.phone || '-',

      website:
        company.website || '-',

      company_owner: {
        label: company.company_owner || 'Unassigned',
        full_name: company.company_owner || 'Unassigned',
      },

      modified: {
        label: formatDate(company.modified),
        timeAgo: timeAgo(company.modified),
      },
    }))
  )

  function getFilters() {
    return selectedIndustry.value
      ? [['industry', '=', selectedIndustry.value]]
      : []
  }

  function getSearchFilters() {
    const query = searchQuery.value.trim()

    if (!query) return []

    const like = `%${query}%`

    return [
      ['company_name', 'like', like],
      ['industry', 'like', like],
      ['email', 'like', like],
      ['phone', 'like', like],
    ]
  }

  async function fetchIndustryOptions() {
    try {
      const data = await call('frappe.client.get_list', {
        doctype: 'DoubleT Company',
        fields: ['industry'],
        filters: [['industry', 'is', 'set']],
        group_by: 'industry',
        order_by: 'industry asc',
        limit_page_length: 0,
      })

      industryOptions.value = (data || [])
        .map((item) => item.industry)
        .filter(Boolean)
    } catch (error) {
      console.warn('Failed to load company industries', error)
    }
  }

  async function fetchCount(filters, orFilters) {
    const args = {
      doctype: 'DoubleT Company',
      fields: ['count(name) as total'],
      filters,
      limit_page_length: 1,
    }

    if (orFilters.length) {
      args.or_filters = orFilters
    }

    const data = await call('frappe.client.get_list', args)

    return Number(data?.[0]?.total || 0)
  }

  async function fetchCompanies({ reset = true } = {}) {
    if (!reset && (companiesResource.loading || !companiesResource.hasNextPage)) {
      return
    }

    const requestId = ++activeRequest
    const filters = getFilters()
    const orFilters = getSearchFilters()
    const start = reset ? 0 : offset.value

    if (reset) {
      companiesResource.data = []
      companiesResource.hasNextPage = false
      totalCount.value = 0
      offset.value = 0
    }

    companiesResource.loading = true
    companiesResource.error = null

    const args = {
      doctype: 'DoubleT Company',
      fields,
      filters,
      order_by: 'modified desc',
      limit_start: start,
      limit_page_length: PAGE_SIZE,
    }

    if (orFilters.length) {
      args.or_filters = orFilters
    }

    try {
      const [data, count] = await Promise.all([
        call('frappe.client.get_list', args),
        reset
          ? fetchCount(filters, orFilters)
          : Promise.resolve(totalCount.value),
      ])

      if (requestId !== activeRequest) return

      const records = Array.isArray(data) ? data : []

      companiesResource.data = reset
        ? records
        : companiesResource.data.concat(records)

      offset.value = companiesResource.data.length
      totalCount.value = count
      companiesResource.hasNextPage = offset.value < count
    } catch (error) {
      if (requestId === activeRequest) {
        companiesResource.error = error
        console.error('Failed to load companies', error)
      }
    } finally {
      if (requestId === activeRequest) {
        companiesResource.loading = false
      }
    }
  }

  function reload() {
    return Promise.all([
      fetchIndustryOptions(),
      fetchCompanies({ reset: true }),
    ])
  }

  function loadMore() {
    return fetchCompanies({ reset: false })
  }

  watch(searchQuery, () => {
    clearTimeout(searchTimer)

    searchTimer = setTimeout(
      () => fetchCompanies({ reset: true }),
      350
    )
  })

  watch(selectedIndustry, () => {
    fetchCompanies({ reset: true })
  })

  onUnmounted(() => clearTimeout(searchTimer))

  reload()

  return {
    companiesResource,
    searchQuery,
    selectedIndustry,
    industryOptions,
    columns,
    rows,
    totalCount,
    reload,
    loadMore,
  }
}
