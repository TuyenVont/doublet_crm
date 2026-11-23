export function formatInputDate(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function reportDatePreset(preset, today = new Date()) {
  const end = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  let start
  if (preset === 'this-month') {
    start = new Date(end.getFullYear(), end.getMonth(), 1)
  } else {
    const days = preset === '7-days' ? 7 : 30
    start = new Date(end)
    start.setDate(end.getDate() - (days - 1))
  }
  return { startDate: formatInputDate(start), endDate: formatInputDate(end) }
}

export function reportDateError(startDate, endDate) {
  if (!startDate || !endDate) return 'Start Date and End Date are required.'
  if (startDate > endDate) return 'Start Date cannot be after End Date.'
  return ''
}

export function isPermissionError(error) {
  const text = error?.messages?.[0] || error?.message || ''
  return error?.httpStatusCode === 403
    || error?.status === 403
    || error?.exc_type === 'PermissionError'
    || /\b(permission|not permitted|not allowed)\b/i.test(text)
}
