export function money(value) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(Number(value) || 0)
}

export function message(error) {
  return error?.messages?.[0] || error?.message || __('Unable to complete the request. Please check your permissions and try again.')
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
  const q = ratio(item.quantity), p = ratio(item.unit_price), d = ratio(item.discount_percent ?? 0)
  if (!q || !p || !d || d[0] > 100n * d[1]) return { gross: 0, discount: 0, total: 0 }
  const gross = round(q[0] * p[0], q[1] * p[1])
  const discount = round(gross * d[0], d[1] * 100n)
  return { gross: Number(gross), discount: Number(discount), total: Number(gross - discount) }
}
