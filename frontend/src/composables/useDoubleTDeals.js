import {
  ref,
  computed,
  toValue,
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
import { buildDealListFilters } from '@/utils/dealFilters'

export function useDoubleTDeals(options = {}) {
  const stages = ref([])
  const stagesLoaded = ref(false)
  const contactLabels = ref({})
  const companyLabels = ref({})

  const stagesMap = computed(() => {
    const map = {}
    stages.value.forEach((s) => {
      map[s.name] = s
    })
    return map
  })

  const filters = computed(() => {
    const selected = toValue(options)
    const filters = buildDealListFilters(selected)
    if (selected.lifecycle) {
      const stageNames = stages.value
        .filter((stage) => stage.stage_type === selected.lifecycle)
        .map((stage) => stage.name)
      if (!selected.stage || !stageNames.includes(selected.stage)) {
        filters.stage = ['in', selected.stage ? [] : stageNames]
      }
    }
    return filters
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

    } catch (error) {
      console.warn('Failed to fetch stages', error)
    } finally {
      stagesLoaded.value = true
    }
  }

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
    filters: filters.value,
    orderBy: 'modified desc',
    pageLength: 20,
    auto: false,
  })

  let reloadRequest

  function reload() {
    if (stagesLoaded.value && !dealsResource.list.loading) reloadRequest = dealsResource.reload()
    return reloadRequest
  }

  watch([filters, stagesLoaded], async ([selected, ready], _, onCleanup) => {
    if (!ready) return
    let stale = false
    onCleanup(() => { stale = true })
    await reloadRequest?.catch(() => {})
    if (dealsResource.list.loading) {
      await dealsResource.list.promise.catch(() => {})
    }
    if (stale) return
    dealsResource.update({ filters: selected, start: 0 })
    return dealsResource.list.fetch()
  })

  fetchStages()

  function watchRelatedLabels(field, doctype, labelFields, labels, getLabel) {
    watch(
      () => {
        const names = (dealsResource.data || []).map((deal) => deal[field]).filter(Boolean)
        return JSON.stringify([...new Set(names)].sort())
      },
      async (key, _, onCleanup) => {
        let stale = false
        onCleanup(() => { stale = true })

        const names = JSON.parse(key)
        if (!names.length) {
          labels.value = {}
          return
        }

        try {
          const records = await call('frappe.client.get_list', {
            doctype,
            fields: ['name', ...labelFields],
            filters: { name: ['in', names] },
            limit_page_length: Math.max(names.length, 20),
          })
          if (!stale) {
            labels.value = Object.fromEntries(
              (records || []).map((record) => [record.name, getLabel(record) || record.name]),
            )
          }
        } catch (error) {
          if (!stale) console.warn(`Failed to load Deal labels for ${doctype}`, error)
        }
      },
      { immediate: true },
    )
  }

  watchRelatedLabels(
    'contact', 'DoubleT Contact', ['first_name', 'last_name'], contactLabels,
    (contact) => [contact.first_name, contact.last_name].filter(Boolean).join(' '),
  )
  watchRelatedLabels(
    'company', 'DoubleT Company', ['company_name'], companyLabels,
    (company) => company.company_name,
  )

  const dealsWithLabels = computed(() =>
    (dealsResource.data || []).map((deal) => ({
      ...deal,
      contact_label: contactLabels.value[deal.contact] || deal.contact || '',
      company_label: companyLabels.value[deal.company] || deal.company || '',
    })),
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
    return dealsWithLabels.value.map((deal) => ({
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
    dealsWithLabels,
    columns,
    rows,
    totalCount,
    reload,
    loadMore() {
      if (!dealsResource.list.loading && dealsResource.hasNextPage && dealsResource.data?.length) {
        dealsResource.update({ start: dealsResource.data.length - dealsResource.pageLength })
        dealsResource.next()
      }
    },
  }
}
