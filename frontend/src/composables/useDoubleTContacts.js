import { computed } from 'vue'
import { createListResource } from 'frappe-ui'
import { formatDate, timeAgo } from '@/utils'

export function useDoubleTContacts() {
  const contactsResource = createListResource({
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
      'owner',
    ],
    orderBy: 'modified desc',
    pageLength: 20,
    auto: true,
  })

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

  const rows = computed(() => {
    if (!contactsResource.data) return []

    return contactsResource.data.map((contact) => {
      const fullName =
        [contact.first_name, contact.last_name]
          .filter(Boolean)
          .join(' ') || contact.name

      return {
        name: contact.name,
        full_name: fullName,
        company: contact.company || '-',
        job_title: contact.job_title || '-',
        email: contact.email || '-',
        phone: contact.phone || '-',
        source: contact.source || '-',

        contact_owner: {
          label: contact.contact_owner || contact.owner || 'Unassigned',
          full_name: contact.contact_owner || contact.owner || 'Unassigned',
        },

        modified: {
          label: formatDate(contact.modified),
          timeAgo: timeAgo(contact.modified),
        },
      }
    })
  })

  const totalCount = computed(() => {
    return contactsResource.data?.length || 0
  })

  return {
    contactsResource,
    columns,
    rows,
    totalCount,
    reload: () => contactsResource.reload(),
    loadMore: () => contactsResource.next(),
  }
}
