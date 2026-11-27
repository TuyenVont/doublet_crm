export const EXPIRABLE_STATUSES = new Set(['Draft', 'Sent'])
export const BLOCKING_APPROVAL_STATUSES = new Set(['Required', 'Pending', 'Rejected'])

export function isQuotationExpired(quotation, siteToday) {
  if (!quotation?.valid_until || !EXPIRABLE_STATUSES.has(quotation.status)) return false
  const today = siteToday || new Date().toISOString().slice(0, 10)
  return String(quotation.valid_until).slice(0, 10) < String(today).slice(0, 10)
}

export function isApprovalBlockingSend(quotation) {
  return BLOCKING_APPROVAL_STATUSES.has(quotation?.approval_status)
}

export function approvalBadgeClass(status) {
  switch (status) {
    case 'Approved':
      return 'bg-green-100 text-green-800'
    case 'Pending':
      return 'bg-amber-100 text-amber-800'
    case 'Required':
      return 'bg-yellow-100 text-yellow-800'
    case 'Rejected':
      return 'bg-red-100 text-red-800'
    default:
      return 'bg-surface-gray-2 text-ink-gray-6'
  }
}

export function buildQuotationItemsFromTemplate(payload) {
  const rows = Array.isArray(payload?.items) ? payload.items : []
  return rows.map((row) => ({
    ...createQuotationItem(
      { name: row.product, product_name: row.product_name, sku: row.sku },
      row.quantity,
    ),
    unit_price: row.unit_price ?? '',
  }))
}

export function money(value) {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Number(value) || 0)
}

export function message(error) {
  return error?.messages?.[0] || error?.message || __('Unable to complete the request. Please check your permissions and try again.')
}

export function dealsForCustomer(deals, customer) {
  if (!Array.isArray(deals) || !customer) return []
  if (customer.customer_type === 'PERSONAL' && customer.contact) {
    return deals.filter(deal => deal.deal_type === 'PERSONAL' && deal.contact === customer.contact && !deal.company)
  }
  if (customer.customer_type === 'COMPANY' && customer.company) {
    return deals.filter(deal => deal.deal_type === 'COMPANY' && deal.company === customer.company && (!customer.contact || deal.contact === customer.contact))
  }
  return []
}

export function contactsForCustomer(contacts, customer) {
  if (!Array.isArray(contacts)) return []
  if (customer?.customer_type !== 'COMPANY') return contacts
  if (!customer.company) return []
  return contacts.filter(contact => contact.company === customer.company)
}

export function customerFromDeal(deal) {
  return {
    customer_type: deal?.deal_type || '',
    contact: deal?.contact || '',
    company: deal?.company || '',
  }
}

export function shouldRepriceItem(item, pricingState) {
  return Boolean(
    !item?.name
    && item?.product
    && !pricingState?.manual
    && (pricingState?.auto || item.unit_price === '' || item.unit_price === null),
  )
}

export function createQuotationItem(product = {}, quantity = 1) {
  const numericQuantity = Number(quantity)
  return {
    product: product.name || '',
    product_name: product.product_name || '',
    sku: product.sku || '',
    quantity: numericQuantity > 0 ? numericQuantity : 1,
    unit_price: '',
    discount_type: 'Percentage',
    discount_percent: 0,
    discount_amount: 0,
  }
}

export function productOptionsForItem(products, item) {
  const options = Array.isArray(products) ? products : []
  const selected = item?.product
  if (!selected || options.some(product => product.name === selected)) return options
  return [{
    name: selected,
    product_name: item.product_name || '',
    sku: item.sku || '',
  }, ...options]
}

export async function appendCatalogSelections(items, selections, resolvePrice) {
  const start = items.length
  const added = selections.map(({ product, quantity }) => createQuotationItem(product, quantity))
  items.push(...added)
  const reactiveRows = items.slice(start)
  await Promise.allSettled(reactiveRows.map(resolvePrice))
  return reactiveRows
}

// Calculate nonnegative decimal products with integer arithmetic, rounding halves up.
function ratio(value) {
  const text = String(value ?? '').trim()
  if (!/^\d+(\.\d+)?$/.test(text)) return null
  const [whole, fraction = ''] = text.split('.')
  return [BigInt(whole + fraction), 10n ** BigInt(fraction.length)]
}
function round(numerator, denominator) {
  return (numerator * 2n + denominator) / (denominator * 2n)
}
export function lineAmounts(item) {
  const q = ratio(item.quantity)
  const p = ratio(item.unit_price)
  if (!q || !p) return { gross: 0, discount: 0, total: 0 }

  const grossCents = round(q[0] * p[0] * 100n, q[1] * p[1])
  let discountCents = 0n
  if ((item.discount_type || 'Percentage') === 'Amount') {
    const amount = ratio(item.discount_amount ?? 0)
    if (!amount) return { gross: 0, discount: 0, total: 0 }
    discountCents = round(amount[0] * 100n, amount[1])
  } else {
    const percent = ratio(item.discount_percent ?? 0)
    if (!percent || percent[0] > 100n * percent[1]) return { gross: 0, discount: 0, total: 0 }
    discountCents = round(grossCents * percent[0], percent[1] * 100n)
  }
  if (discountCents > grossCents) return { gross: 0, discount: 0, total: 0 }
  return {
    gross: Number(grossCents) / 100,
    discount: Number(discountCents) / 100,
    total: Number(grossCents - discountCents) / 100,
  }
}
