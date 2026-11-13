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
