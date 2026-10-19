import { dayjs, dayjsLocal, getConfig } from 'frappe-ui'

export function isEmoji(str) {
  if (!str) return false
  const regex = /\p{Extended_Pictographic}/u
  return regex.test(str)
}

export function formatDate(date, format, onlyDate = false, onlyTime = false) {
  if (!date) return ''
  try {
    const dateFormat = window.sysdefaults?.date_format
      ? window.sysdefaults.date_format.replace('mm', 'MM').replace('yyyy', 'YYYY').replace('dd', 'DD')
      : 'YYYY-MM-DD'
    const timeFormat = window.sysdefaults?.time_format || 'HH:mm:ss'

    if (onlyDate) return dayjs(date).format(dateFormat)
    if (onlyTime) return dayjs(date).format(timeFormat)
    if (format) return dayjs(date).format(format)
    return dayjs(date).format(`${dateFormat} ${timeFormat}`)
  } catch (e) {
    return String(date)
  }
}

export function timeAgo(date) {
  if (!date) return ''
  try {
    const d = dayjs(date)
    const now = dayjs()
    const diffSec = now.diff(d, 'seconds')

    if (diffSec < 60) return 'Just now'
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
    if (diffSec < 86400 * 7) return `${Math.floor(diffSec / 86400)}d ago`
    return d.format('YYYY-MM-DD')
  } catch (e) {
    return String(date)
  }
}

export function formatCurrency(value, currency = 'USD') {
  if (value === null || value === undefined || value === '') return '$ 0.00'
  const num = Number(value)
  if (isNaN(num)) return String(value)
  try {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency || 'USD',
      maximumFractionDigits: 2,
    }).format(num)
  } catch {
    return `$ ${num.toLocaleString()}`
  }
}

export function formatDuration(totalSeconds) {
  if (!totalSeconds) return ''
  const s = parseInt(totalSeconds, 10)
  if (isNaN(s)) return ''
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  const sec = s % 60
  const parts = []
  if (h) parts.push(`${h}h`)
  if (m) parts.push(`${m}m`)
  if (sec) parts.push(`${sec}s`)
  return parts.join(' ')
}

export function isTranslatable(val) {
  return false
}

export function website(url) {
  if (!url) return ''
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    return 'https://' + url
  }
  return url
}

export * from './frappe-index.js'
