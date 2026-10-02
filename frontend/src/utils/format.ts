// Formatting helpers shared by every page.

export function todayString() {
  const now = new Date()
  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')

  return `${year}-${month}-${day}`
}

export function currentMonthString() {
  return todayString().slice(0, 7)
}

// "2026-09-28" -> "Sep 28, 2026" (no timezone shifting)
export function formatDate(date: string | null | undefined) {
  if (!date) return '—'

  const [year, month, day] = date.slice(0, 10).split('-')

  return new Date(
    Number(year),
    Number(month) - 1,
    Number(day),
  ).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export function formatDateTime(date: string | null | undefined) {
  if (!date) return '—'

  return new Date(date).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

// "2026-10-05T09:30:00" -> "Mon, Oct 5, 9:30 AM"
export function formatDateTimeShort(date: string | null | undefined) {
  if (!date) return '—'

  return new Date(date).toLocaleString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  })
}

export function formatTime(date: string) {
  return new Date(date).toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  })
}

const usd = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
})

export function formatMoney(value: number | null | undefined) {
  if (value === null || value === undefined) return '—'
  return usd.format(value)
}

export function formatPrice(value: number | null | undefined) {
  if (value === null || value === undefined) return '—'
  // Small crypto prices need more than 2 decimals
  if (Math.abs(value) < 1) {
    return `$${value.toPrecision(4)}`
  }
  return usd.format(value)
}

export function formatPercent(value: number | null | undefined) {
  if (value === null || value === undefined) return '—'
  return `${value > 0 ? '+' : ''}${value.toFixed(2)}%`
}

export function formatNumber(value: number) {
  return value.toLocaleString(undefined, { maximumFractionDigits: 8 })
}

export function monthLabel(year: number, month: number) {
  return new Date(year, month - 1, 1).toLocaleDateString(undefined, {
    month: 'long',
    year: 'numeric',
  })
}

export function titleCase(value: string) {
  return value
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
