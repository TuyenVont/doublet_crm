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
  } else if (preset === 'this-quarter') {
    start = new Date(end.getFullYear(), Math.floor(end.getMonth() / 3) * 3, 1)
  } else if (preset === 'previous-month') {
    start = new Date(end.getFullYear(), end.getMonth() - 1, 1)
    end.setDate(0)
  } else if (preset === 'previous-quarter') {
    const quarterStartMonth = Math.floor(end.getMonth() / 3) * 3
    start = new Date(end.getFullYear(), quarterStartMonth - 3, 1)
    end.setTime(new Date(end.getFullYear(), quarterStartMonth, 0).getTime())
  } else {
    const days = preset === '7-days' ? 7 : 30
    start = new Date(end)
    start.setDate(end.getDate() - (days - 1))
  }
  return { startDate: formatInputDate(start), endDate: formatInputDate(end) }
}

export function previousReportPeriod(startDate, endDate) {
  if (reportDateError(startDate, endDate)) return null
  const start = new Date(`${startDate}T00:00:00Z`)
  const end = new Date(`${endDate}T00:00:00Z`)
  const days = Math.round((end - start) / 86400000) + 1
  const previousEnd = new Date(start)
  previousEnd.setUTCDate(previousEnd.getUTCDate() - 1)
  const previousStart = new Date(previousEnd)
  previousStart.setUTCDate(previousStart.getUTCDate() - days + 1)
  return { startDate: formatInputDate(previousStart), endDate: formatInputDate(previousEnd) }
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
