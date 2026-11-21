const customerRoutes = {
  'DoubleT Lead': ['LeadDetail', 'leadId'],
  'DoubleT Contact': ['ContactDetail', 'contactId'],
}

export function callCustomerRoute(customer) {
  const target = customerRoutes[customer?.doctype]
  if (!target) return null
  const [name, param] = target
  return { name, params: { [param]: customer.name }, hash: '#calls' }
}

export function formatCallTime(value) {
  if (!value) return '—'
  const date = new Date(String(value).replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' })
}

export const caseStatusTheme = {
  Waiting: 'orange',
  'In Progress': 'blue',
  Resolved: 'green',
}

export function callOutcomeTheme(status) {
  if (status === 'Completed') return 'green'
  if (['Missed', 'No Answer', 'Failed'].includes(status)) return 'red'
  if (status === 'Busy') return 'orange'
  return 'gray'
}
