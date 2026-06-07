/**
 * Pure helper that turns a ParsedTable into chart-ready `{ name, value }[]`,
 * applying chart-type-specific rules (long-tail grouping and dropping
 * non-positive slices for pie/donut). No React.
 */
import { parseNumeric, type ParsedTable } from './parseMarkdownTable'

export type ChartType = 'bar' | 'pie' | 'donut'

export interface ChartDatum {
  name: string
  value: number
}

/** Categorical palette, wired to the theme's chart CSS variables. */
export const CHART_PALETTE = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)',
]

/** Map each category to a label + a distinct (cycling) colour for charts. */
export function buildChartConfig(
  data: ChartDatum[],
): Record<string, { label: string; color: string }> {
  const config: Record<string, { label: string; color: string }> = {}
  data.forEach((d, i) => {
    config[d.name] = {
      label: d.name,
      color: CHART_PALETTE[i % CHART_PALETTE.length],
    }
  })
  return config
}

interface BuildOptions {
  valueIndex: number
  chartType: ChartType
  /** Max slices before the tail is grouped into "Other" (pie/donut only). */
  maxSlices?: number
}

export function buildChartData(
  table: ParsedTable,
  { valueIndex, chartType, maxSlices = 8 }: BuildOptions,
): ChartDatum[] {
  const { rows, labelIndex } = table

  const data: ChartDatum[] = rows.map((row) => ({
    name: row[labelIndex] ?? '',
    value: parseNumeric(row[valueIndex] ?? '') ?? 0,
  }))

  // Bar charts show every category, including zero/negative values.
  if (chartType === 'bar') return data

  // Pie/donut: only positive slices make sense.
  const positive = data.filter((d) => d.value > 0)
  if (positive.length <= maxSlices) return positive

  const sorted = [...positive].sort((a, b) => b.value - a.value)
  const head = sorted.slice(0, maxSlices - 1)
  const tail = sorted.slice(maxSlices - 1)
  const other = tail.reduce((sum, d) => sum + d.value, 0)
  return [...head, { name: 'Other', value: other }]
}
