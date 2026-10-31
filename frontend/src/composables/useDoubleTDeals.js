import {
  ref,
  computed,
  watch,
} from 'vue'

import {
  call,
  createListResource,
} from 'frappe-ui'

import {
  formatDate,
  timeAgo,
  formatCurrency,
} from '@/utils'

export function useDoubleTDeals() {
  const stages = ref([])
  const contactLabels = ref({})
  const companyLabels = ref({})

  const stagesMap = computed(() => {
    const map = {}
    stages.value.forEach((s) => {
      map[s.name] = s
    })
    return map
  })

  async function fetchStages() {
    try {
      const res = await call('frappe.client.get_list', {
        doctype: 'DoubleT Deal Stage',
        fields: [
          'name',
          'stage_name',
          'stage_type',
          'color',
          'sort_order',
          'enabled',
        ],
        filters: {
          enabled: 1,
        },
        order_by: 'sort_order asc',
        limit_page_length: 50,
      })
      stages.value = res || []
    } catch (e) {
      console.warn('Failed to fetch stages', e)
    }
  }
  fetchStages()

  function getStageColor(stageName) {
    const s = stagesMap.value[stageName]
    if (!s) return 'text-ink-gray-5'
    if (s.stage_type === 'WON') return 'text-green-600'
    if (s.stage_type === 'LOST') return 'text-red-600'
    return 'text-blue-500'
  }

  const dealsResource = createListResource({
    doctype: 'DoubleT Deal',
    fields: [
      'name',
      'deal_title',
      'amount',
      'deal_owner',
      'deal_type',
      'contact',
      'company',
      'source_lead',
      'expected_close_date',
      'stage',
      'won_on',
      'lost_on',
      'lost_reason',
      'modified',
      'creation',
      'owner',
    ],
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

  async function loadRelatedLabels(deals) {
    const contactNames = [
      ...new Set(
        deals.map((d) => d.contact).filter(Boolean)
      ),
    ]
    const companyNames = [
      ...new Set(
        deals.map((d) => d.company).filter(Boolean)
      ),
    ]

    const nextContactLabels = {}
    const nextCompanyLabels = {}

    try {
      const [contacts, companies] = await Promise.all([
        contactNames.length
          ? call('frappe.client.get_list', {
              doctype: 'DoubleT Contact',
              fields: ['name', 'first_name', 'last_name'],
              filters: { name: ['in', contactNames] },
              limit_page_length: Math.max(contactNames.length, 20),
            })
          : Promise.resolve([]),
        companyNames.length
          ? call('frappe.client.get_list', {
              doctype: 'DoubleT Company',
              fields: ['name', 'company_name'],
              filters: { name: ['in', companyNames] },
              limit_page_length: Math.max(companyNames.length, 20),
            })
          : Promise.resolve([]),
      ])

      ;(contacts || []).forEach((c) => {
        nextContactLabels[c.name] =
          [c.first_name, c.last_name].filter(Boolean).join(' ') || c.name
      })

      ;(companies || []).forEach((c) => {
        nextCompanyLabels[c.name] = c.company_name || c.name
      })
    } catch (e) {
      console.warn('Failed to load Deal related labels', e)
    }

    contactLabels.value = nextContactLabels
    companyLabels.value = nextCompanyLabels

    deals.forEach((deal) => {
      deal.contact_label = deal.contact
        ? nextContactLabels[deal.contact] || deal.contact
        : ''
      deal.company_label = deal.company
        ? nextCompanyLabels[deal.company] || deal.company
        : ''
    })
  }

  watch(
    () => dealsResource.data,
    (deals) => {
      loadRelatedLabels(Array.isArray(deals) ? deals : [])
    },
    {
      immediate: true,
      deep: true,
    }
  )

  const columns = [
    { label: 'Deal Title', key: 'deal_title', width: '220px' },
    { label: 'Stage', key: 'stage', width: '150px' },
    { label: 'Amount', key: 'amount', width: '130px', align: 'right' },
    { label: 'Contact', key: 'contact', width: '160px' },
    { label: 'Company', key: 'company', width: '160px' },
    { label: 'Owner', key: 'deal_owner', width: '150px' },
    { label: 'Close Date', key: 'expected_close_date', width: '130px' },
    { label: 'Last Modified', key: 'modified', width: '130px' },
  ]

  const rows = computed(() => {
    if (!dealsResource.data) return []
    return dealsResource.data.map((deal) => ({
      name: deal.name,
      deal_title: deal.deal_title || deal.name,
      stage: {
        label:
          stagesMap.value[deal.stage]?.stage_name ||
          deal.stage ||
          'No Stage',
        color: getStageColor(deal.stage),
      },
      amount: formatCurrency(deal.amount),
      contact:
        deal.contact_label || deal.contact || '-',
      company:
        deal.company_label || deal.company || '-',
      deal_owner: {
        label: deal.deal_owner || deal.owner || 'Unassigned',
        full_name: deal.deal_owner || deal.owner || 'Unassigned',
      },
      expected_close_date: deal.expected_close_date || '-',
      modified: {
        label: formatDate(deal.modified),
        timeAgo: timeAgo(deal.modified),
      },
    }))
  })

  const totalCount = computed(() => {
    return dealsResource.data?.length || 0
  })

  return {
    stages,
    dealsResource,
    columns,
    rows,
    totalCount,
    reload: () => dealsResource.reload(),
    loadMore: () => dealsResource.next(),
  }
}
