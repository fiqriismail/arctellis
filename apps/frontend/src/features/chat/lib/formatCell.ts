/**
 * Pure cell parsing/formatting and detection helpers for data tables. No React.
 *
 * Defaults: money columns render as currency (£ unless the cell carries an
 * explicit symbol) with two decimals; dates render as dd-mm-yyyy.
 */

export type ColumnKind = 'currency' | 'integer' | 'number' | 'date' | 'text'

const CURRENCY_PREFIX = /^[£$€¥]\s*/

/** Headers that indicate a count / row-count aggregation (never currency). */
const COUNT_HEADER_PATTERNS = [
  /\bcount\b/i,
  /\brow_count\b/i,
  /\brow count\b/i,
  /\bnumber of\b/i,
  /\bnum(?:ber)? of\b/i,
  /\b# of\b/i,
  /\brecords?\b/i,
  /\bitems?\b/i,
  /\brequests?\b/i,
]

export function isCountHeader(name: string): boolean {
  return COUNT_HEADER_PATTERNS.some((p) => p.test(name))
}

/**
 * Parse a cell into a number, tolerating thousands separators and a leading
 * currency symbol. Returns null when the value is blank or not numeric.
 */
export function parseNumeric(value: string): number | null {
  const trimmed = value.trim()
  if (trimmed === '') return null
  const cleaned = trimmed.replace(CURRENCY_PREFIX, '').replace(/,/g, '')
  if (cleaned === '') return null
  const n = Number(cleaned)
  return Number.isFinite(n) ? n : null
}

const MONEY_KEYWORDS = [
  'amount',
  'cost',
  'price',
  'budget',
  'estimate',
  'spend',
  'paid',
  'revenue',
  'salary',
  'fee',
  'balance',
  'subtotal',
]

export function isMoneyHeader(name: string): boolean {
  if (isCountHeader(name)) return false

  const n = name.toLowerCase()
  if (/\(€\)|\(eur\)|\(£\)|\(gbp\)/i.test(name)) return true
  if (/\btotal\s+(amount|cost|spend|budget|estimated)/i.test(n)) return true
  if (/\b(sum|subtotal)\s+of\b/i.test(n)) return true
  return MONEY_KEYWORDS.some((k) => n.includes(k))
}

const SYMBOL_TO_CURRENCY: Record<string, string> = {
  '€': 'EUR',
  $: 'USD',
  '£': 'GBP',
  '¥': 'JPY',
}

const CURRENCY_TO_SYMBOL: Record<string, string> = {
  EUR: '€',
  USD: '$',
  GBP: '£',
  JPY: '¥',
}

/** Currency code implied by a leading symbol in the raw cell, or null. */
export function detectCurrency(raw: string): string | null {
  const m = raw.trim().match(/^([£$€¥])/)
  return m ? SYMBOL_TO_CURRENCY[m[1]] : null
}

export function formatInteger(value: number): string {
  return new Intl.NumberFormat('en-US', {
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatCurrency(value: number, currency = 'GBP'): string {
  const symbol = CURRENCY_TO_SYMBOL[currency] ?? '£'
  const n = new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
  return `${symbol}${n}`
}

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})(?:[T ]\d{2}:\d{2})?/

/** Parse ISO date / datetime strings to a Date, else null. */
export function parseDate(raw: string): Date | null {
  const m = raw.trim().match(ISO_DATE)
  if (!m) return null
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
  return Number.isNaN(d.getTime()) ? null : d
}

export function formatDate(d: Date): string {
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  return `${dd}-${mm}-${d.getFullYear()}`
}

/** Format a raw cell for display according to its column kind. */
export function formatCellValue(raw: string, kind: ColumnKind): string {
  if (raw.trim() === '') return raw

  if (kind === 'currency') {
    const n = parseNumeric(raw)
    if (n === null) return raw
    return formatCurrency(n, detectCurrency(raw) ?? 'GBP')
  }

  if (kind === 'integer') {
    const n = parseNumeric(raw)
    if (n === null) return raw
    return formatInteger(n)
  }

  if (kind === 'date') {
    const d = parseDate(raw)
    return d ? formatDate(d) : raw
  }

  // number / text render as-is (numbers are right-aligned by the table).
  return raw
}
