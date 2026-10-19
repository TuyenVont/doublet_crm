import { computed } from 'vue'
import { createListResource } from 'frappe-ui'
import { formatDate, timeAgo } from '@/utils'

export function useDoubleTCompanies() {
  const companiesResource = createListResource({
    doctype: 'DoubleT Company',
    fields: [
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
    ],
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

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

  const rows = computed(() => {
    if (!companiesResource.data) return []

    return companiesResource.data.map((company) => ({
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
        label: company.company_owner || company.owner || 'Unassigned',
        full_name: company.company_owner || company.owner || 'Unassigned',
      },

      modified: {
        label: formatDate(company.modified),
        timeAgo: timeAgo(company.modified),
      },
    }))
  })

  const totalCount = computed(() => {
    return companiesResource.data?.length || 0
  })

  return {
    companiesResource,
    columns,
    rows,
    totalCount,
    reload: () => companiesResource.reload(),
    loadMore: () => companiesResource.next(),
  }
}
