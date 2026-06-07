/**
 * Pure helpers for turning a Markdown table's header + rows into a structured,
 * chartable shape. No React — unit-tested in isolation.
 */

export interface ParsedColumn {
  name: string
  numeric: boolean
}

export interface ParsedTable {
  columns: ParsedColumn[]
  rows: string[][]
  /** Index of the first non-numeric (label) column, or -1 if none. */
  labelIndex: number
  /** Indexes of all numeric columns, left to right. */
  numericIndexes: number[]
  /** A label column and at least one numeric column are present. */
  chartable: boolean
  /** Exactly one label column and exactly one numeric column (a group-by result). */
  isAggregation: boolean
}

const CURRENCY_PREFIX = /^[£$€¥]\s*/

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

/** A column is numeric when the majority of its non-empty cells parse as numbers. */
function isColumnNumeric(rows: string[][], colIndex: number): boolean {
  let nonEmpty = 0
  let numeric = 0
  for (const row of rows) {
    const cell = (row[colIndex] ?? '').trim()
    if (cell === '') continue
    nonEmpty++
    if (parseNumeric(cell) !== null) numeric++
  }
  return nonEmpty > 0 && numeric * 2 > nonEmpty
}

export function parseMarkdownTable(
  headers: string[],
  rows: string[][],
): ParsedTable {
  const columns: ParsedColumn[] = headers.map((name, i) => ({
    name,
    numeric: isColumnNumeric(rows, i),
  }))

  const numericIndexes = columns
    .map((c, i) => (c.numeric ? i : -1))
    .filter((i) => i >= 0)
  const labelIndex = columns.findIndex((c) => !c.numeric)

  const chartable = labelIndex >= 0 && numericIndexes.length >= 1
  const isAggregation =
    columns.length === 2 && labelIndex >= 0 && numericIndexes.length === 1

  return { columns, rows, labelIndex, numericIndexes, chartable, isAggregation }
}
