import {
  buildChartData,
  buildChartConfig,
} from '@/features/chat/lib/chartData'
import { parseMarkdownTable } from '@/features/chat/lib/parseMarkdownTable'

const agg = parseMarkdownTable(
  ['Status', 'Total'],
  [
    ['Approved', '5000'],
    ['Rejected', '1200'],
    ['Draft', '0'],
  ],
)

describe('buildChartData', () => {
  it('maps label and value columns into {name, value}', () => {
    const data = buildChartData(agg, { valueIndex: 1, chartType: 'bar' })
    expect(data).toEqual([
      { name: 'Approved', value: 5000 },
      { name: 'Rejected', value: 1200 },
      { name: 'Draft', value: 0 },
    ])
  })

  it('keeps zero/negative values for bar charts', () => {
    const t = parseMarkdownTable(
      ['Dept', 'Delta'],
      [['A', '-5'], ['B', '3']],
    )
    const data = buildChartData(t, { valueIndex: 1, chartType: 'bar' })
    expect(data).toEqual([
      { name: 'A', value: -5 },
      { name: 'B', value: 3 },
    ])
  })

  it('drops non-positive slices for pie charts', () => {
    const data = buildChartData(agg, { valueIndex: 1, chartType: 'pie' })
    expect(data.map((d) => d.name)).toEqual(['Approved', 'Rejected'])
  })

  it('groups the long tail into "Other" for pie charts', () => {
    const many = parseMarkdownTable(
      ['Cat', 'N'],
      Array.from({ length: 12 }, (_, i) => [`C${i}`, String(12 - i)]),
    )
    const data = buildChartData(many, {
      valueIndex: 1,
      chartType: 'pie',
      maxSlices: 8,
    })
    expect(data).toHaveLength(8)
    expect(data[data.length - 1].name).toBe('Other')
    // Values are 12..1; head keeps the top 7 (12..6), tail = 5,4,3,2,1.
    expect(data[data.length - 1].value).toBe(5 + 4 + 3 + 2 + 1)
  })

  it('coerces blank/non-numeric value cells to 0', () => {
    const t = parseMarkdownTable(
      ['Dept', 'Amount'],
      [['A', ''], ['B', '10'], ['C', '7']],
    )
    const data = buildChartData(t, { valueIndex: 1, chartType: 'bar' })
    expect(data[0]).toEqual({ name: 'A', value: 0 })
  })
})

describe('buildChartConfig', () => {
  it('assigns a label and a distinct colour per category', () => {
    const cfg = buildChartConfig([
      { name: 'Approved', value: 1 },
      { name: 'Closed', value: 2 },
    ])
    expect(cfg.Approved.label).toBe('Approved')
    expect(cfg.Closed.label).toBe('Closed')
    expect(cfg.Approved.color).toBeTruthy()
    expect(cfg.Approved.color).not.toBe(cfg.Closed.color)
  })

  it('cycles colours when categories exceed the palette', () => {
    const many = Array.from({ length: 7 }, (_, i) => ({
      name: `C${i}`,
      value: 1,
    }))
    const cfg = buildChartConfig(many)
    expect(Object.keys(cfg)).toHaveLength(7)
    // wraps around: 6th category reuses the first palette colour
    expect(cfg.C5.color).toBe(cfg.C0.color)
  })
})
