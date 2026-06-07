/**
 * Pure helpers for turning a Markdown table's header + rows into a structured,
 * chartable shape. No React — unit-tested in isolation.
 */
import {
  isMoneyHeader,
  parseDate,
  parseNumeric,
  type ColumnKind,
} from './formatCell'

export { parseNumeric }
export type { ColumnKind }

export interface ParsedColumn {
  name: string
  numeric: boolean
  kind: ColumnKind
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

/** Majority of non-empty cells in a column satisfy the predicate. */
function columnMostly(
  rows: string[][],
  colIndex: number,
  predicate: (cell: string) => boolean,
): boolean {
  let nonEmpty = 0
  let hits = 0
  for (const row of rows) {
    const cell = (row[colIndex] ?? '').trim()
    if (cell === '') continue
    nonEmpty++
    if (predicate(cell)) hits++
  }
  return nonEmpty > 0 && hits * 2 > nonEmpty
}

function columnKind(name: string, rows: string[][], colIndex: number): ColumnKind {
  if (columnMostly(rows, colIndex, (c) => parseDate(c) !== null)) return 'date'
  if (columnMostly(rows, colIndex, (c) => parseNumeric(c) !== null)) {
    return isMoneyHeader(name) ? 'currency' : 'number'
  }
  return 'text'
}

export function parseMarkdownTable(
  headers: string[],
  rows: string[][],
): ParsedTable {
  const columns: ParsedColumn[] = headers.map((name, i) => {
    const kind = columnKind(name, rows, i)
    return { name, kind, numeric: kind === 'currency' || kind === 'number' }
  })

  const numericIndexes = columns
    .map((c, i) => (c.numeric ? i : -1))
    .filter((i) => i >= 0)
  const labelIndex = columns.findIndex((c) => !c.numeric)

  const chartable = labelIndex >= 0 && numericIndexes.length >= 1
  const isAggregation =
    columns.length === 2 && labelIndex >= 0 && numericIndexes.length === 1

  return { columns, rows, labelIndex, numericIndexes, chartable, isAggregation }
}
