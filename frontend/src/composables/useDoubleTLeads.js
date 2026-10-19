import { computed } from 'vue'
import { createListResource } from 'frappe-ui'
import { formatDate, timeAgo } from '@/utils'

export function useDoubleTLeads() {
  const leadsResource = createListResource({
    doctype: 'DoubleT Lead',
    fields: [
      'name',
      'first_name',
      'last_name',
      'phone',
      'email',
      'company_name',
      'source',
      'status',
      'lead_owner',
      'converted_on',
      'converted_contact',
      'converted_company',
      'converted_deal',
      'modified',
      'creation',
      'owner',
    ],
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

  function getStatusColor(status) {
    switch (status) {
      case 'NEW':
        return 'text-blue-500'
      case 'CONTACTED':
        return 'text-cyan-600'
      case 'NURTURE':
        return 'text-orange-500'
      case 'QUALIFIED':
        return 'text-green-600'
      case 'CONVERTED':
        return 'text-green-700'
      case 'UNQUALIFIED':
        return 'text-gray-500'
      case 'JUNK':
        return 'text-red-500'
      default:
        return 'text-ink-gray-5'
    }
  }

  const columns = [
    { label: 'Full Name', key: 'full_name', width: '200px' },
    { label: 'Email', key: 'email', width: '220px' },
    { label: 'Company', key: 'company_name', width: '180px' },
    { label: 'Status', key: 'status', width: '140px' },
    { label: 'Source', key: 'source', width: '150px' },
    { label: 'Phone', key: 'phone', width: '150px' },
    { label: 'Owner', key: 'lead_owner', width: '160px' },
    { label: 'Last Modified', key: 'modified', width: '140px' },
  ]

  const rows = computed(() => {
    if (!leadsResource.data) return []

    return leadsResource.data.map((lead) => {
      const fullName =
        [lead.first_name, lead.last_name]
          .filter(Boolean)
          .join(' ') || lead.name

      return {
        name: lead.name,

        full_name: fullName,

        email: lead.email || '-',

        company_name: lead.company_name || '-',

        status: {
          label: lead.status || 'NEW',
          color: getStatusColor(lead.status),
        },

        source: lead.source || '-',

        phone: lead.phone || '-',

        lead_owner: {
          label: lead.lead_owner || lead.owner || 'Unassigned',
          full_name: lead.lead_owner || lead.owner || 'Unassigned',
        },

        modified: {
          label: formatDate(lead.modified),
          timeAgo: timeAgo(lead.modified),
        },
      }
    })
  })

  const totalCount = computed(() => {
    return leadsResource.data?.length || 0
  })

  return {
    leadsResource,
    columns,
    rows,
    totalCount,
    reload: () => leadsResource.reload(),
    loadMore: () => leadsResource.next(),
  }
}
