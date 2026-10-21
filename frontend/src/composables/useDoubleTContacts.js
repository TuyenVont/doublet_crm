import { computed, ref, watch } from 'vue'
import { call } from 'frappe-ui'
import { formatDate, timeAgo } from '@/utils'

const PAGE_SIZE = 20

export function useDoubleTContacts() {
  const contacts = ref([])
  const loading = ref(false)

  const searchQuery = ref('')
  const selectedSource = ref('')

  const totalCount = ref(0)
  const offset = ref(0)
  const hasMore = ref(false)

  const companyMap = ref({})
  const sourceOptions = ref([])

  let searchTimer = null
  let activeRequest = 0

  const columns = [
    { label: 'Full Name', key: 'full_name', width: '200px' },
    { label: 'Company', key: 'company', width: '180px' },
    { label: 'Job Title', key: 'job_title', width: '160px' },
    { label: 'Email', key: 'email', width: '220px' },
    { label: 'Phone', key: 'phone', width: '150px' },
    { label: 'Source', key: 'source', width: '140px' },
    { label: 'Owner', key: 'contact_owner', width: '160px' },
    { label: 'Last Modified', key: 'modified', width: '140px' },
  ]

  const rows = computed(() =>
    contacts.value.map((contact) => {
      const fullName =
        [contact.first_name, contact.last_name]
          .filter(Boolean)
          .join(' ') || contact.name

      return {
        name: contact.name,

        full_name: fullName,

        company: contact.company
          ? companyMap.value[contact.company] || contact.company
          : '-',

        job_title: contact.job_title || '-',
        email: contact.email || '-',
        phone: contact.phone || '-',
        source: contact.source || '-',

        contact_owner: {
          label: contact.contact_owner || 'Unassigned',
          full_name: contact.contact_owner || 'Unassigned',
        },

        modified: {
          label: formatDate(contact.modified),
          timeAgo: timeAgo(contact.modified),
        },
      }
    })
  )

  async function fetchSourceOptions() {
    try {
      const data = await call('frappe.client.get_list', {
        doctype: 'DoubleT Lead Source',

        fields: [
          'name',
          'source_name',
        ],

        filters: [
          ['is_active', '=', 1],
        ],

        order_by: 'source_name asc',

        limit_page_length: 500,
      })

      sourceOptions.value = (data || []).map(
        (item) => item.source_name || item.name
      )
    } catch (error) {
      console.warn(
        'Failed to load contact sources',
        error
      )
    }
  }

  async function findMatchingCompanyIds(q) {
    if (!q) return []

    try {
      const data = await call(
        'frappe.client.get_list',
        {
          doctype: 'DoubleT Company',

          fields: ['name'],

          filters: [
            [
              'company_name',
              'like',
              `%${q}%`,
            ],
          ],

          limit_page_length: 100,
        }
      )

      return (data || []).map(
        (item) => item.name
      )
    } catch (error) {
      console.warn(
        'Failed to search companies',
        error
      )

      return []
    }
  }

  async function loadCompanyNames(records) {
    const ids = [
      ...new Set(
        (records || [])
          .map((item) => item.company)
          .filter(Boolean)
      ),
    ].filter(
      (id) => !companyMap.value[id]
    )

    if (!ids.length) return

    try {
      const data = await call(
        'frappe.client.get_list',
        {
          doctype: 'DoubleT Company',

          fields: [
            'name',
            'company_name',
          ],

          filters: [
            ['name', 'in', ids],
          ],

          limit_page_length: ids.length,
        }
      )

      const nextMap = {
        ...companyMap.value,
      }

      for (const company of data || []) {
        nextMap[company.name] =
          company.company_name ||
          company.name
      }

      companyMap.value = nextMap
    } catch (error) {
      console.warn(
        'Failed to resolve company names',
        error
      )
    }
  }

  async function fetchCount(
    filters,
    orFilters
  ) {
    try {
      const args = {
        doctype: 'DoubleT Contact',

        fields: [
          'count(name) as total',
        ],

        filters,

        limit_page_length: 1,
      }

      if (orFilters.length) {
        args.or_filters = orFilters
      }

      const data = await call(
        'frappe.client.get_list',
        args
      )

      return Number(
        data?.[0]?.total || 0
      )
    } catch (error) {
      console.warn(
        'Contact count query failed',
        error
      )

      return null
    }
  }

  async function fetchContacts({
    reset = true,
  } = {}) {
    const requestId = ++activeRequest

    loading.value = true

    try {
      const q =
        searchQuery.value.trim()

      const filters = []

      if (selectedSource.value) {
        filters.push([
          'source',
          '=',
          selectedSource.value,
        ])
      }

      const companyIds = q
        ? await findMatchingCompanyIds(q)
        : []

      const orFilters = []

      if (q) {
        const like = `%${q}%`

        orFilters.push(
          [
            'first_name',
            'like',
            like,
          ],
          [
            'last_name',
            'like',
            like,
          ],
          [
            'phone',
            'like',
            like,
          ],
          [
            'email',
            'like',
            like,
          ],
          [
            'job_title',
            'like',
            like,
          ]
        )

        if (companyIds.length) {
          orFilters.push([
            'company',
            'in',
            companyIds,
          ])
        }
      }

      const start = reset
        ? 0
        : offset.value

      const args = {
        doctype: 'DoubleT Contact',

        fields: [
          'name',
          'first_name',
          'last_name',
          'phone',
          'email',
          'birthday',
          'address',
          'source',
          'contact_owner',
          'company',
          'job_title',
          'modified',
          'creation',
        ],

        filters,

        order_by:
          'modified desc',

        limit_start: start,

        limit_page_length:
          PAGE_SIZE,
      }

      if (orFilters.length) {
        args.or_filters =
          orFilters
      }

      const [
        data,
        count,
      ] = await Promise.all([
        call(
          'frappe.client.get_list',
          args
        ),

        reset
          ? fetchCount(
              filters,
              orFilters
            )
          : Promise.resolve(
              totalCount.value
            ),
      ])

      // Bỏ kết quả request cũ
      // nếu user gõ tiếp quá nhanh.
      if (
        requestId !== activeRequest
      ) {
        return
      }

      const records =
        data || []

      await loadCompanyNames(
        records
      )

      if (reset) {
        contacts.value = records
        offset.value =
          records.length
      } else {
        contacts.value = [
          ...contacts.value,
          ...records,
        ]

        offset.value +=
          records.length
      }

      /*
       * Bình thường count query sẽ
       * trả số chính xác.
       *
       * Nếu Frappe version hiện tại
       * không support aggregate này,
       * dùng fallback Load More.
       */
      if (count === null) {
        hasMore.value =
          records.length ===
          PAGE_SIZE

        totalCount.value =
          hasMore.value
            ? contacts.value.length + 1
            : contacts.value.length
      } else {
        totalCount.value =
          count

        hasMore.value =
          contacts.value.length <
          count
      }
    } catch (error) {
      console.error(
        'Failed to load contacts',
        error
      )
    } finally {
      if (
        requestId === activeRequest
      ) {
        loading.value = false
      }
    }
  }

  function reload() {
    return fetchContacts({
      reset: true,
    })
  }

  function loadMore() {
    if (
      loading.value ||
      !hasMore.value
    ) {
      return
    }

    return fetchContacts({
      reset: false,
    })
  }

  /*
   * Debounce 350 ms:
   * không request mỗi lần gõ 1 ký tự.
   */
  watch(searchQuery, () => {
    clearTimeout(searchTimer)

    searchTimer =
      setTimeout(
        () => reload(),
        350
      )
  })

  watch(
    selectedSource,
    () => reload()
  )

  fetchSourceOptions()
  reload()

  return {
    loading,

    searchQuery,
    selectedSource,
    sourceOptions,

    columns,
    rows,

    totalCount,
    hasMore,

    reload,
    loadMore,
  }
}
