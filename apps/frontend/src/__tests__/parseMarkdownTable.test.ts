import {
  parseNumeric,
  parseMarkdownTable,
} from '@/features/chat/lib/parseMarkdownTable'

describe('parseNumeric', () => {
  it('parses a plain integer', () => {
    expect(parseNumeric('42')).toBe(42)
  })

  it('parses a decimal', () => {
    expect(parseNumeric('48.7')).toBe(48.7)
  })

  it('strips thousands separators', () => {
    expect(parseNumeric('1,234.50')).toBe(1234.5)
  })

  it('strips a leading currency symbol', () => {
    expect(parseNumeric('£12')).toBe(12)
    expect(parseNumeric('$1,000')).toBe(1000)
  })

  it('parses negative numbers', () => {
    expect(parseNumeric('-5')).toBe(-5)
  })

  it('returns null for empty string', () => {
    expect(parseNumeric('')).toBeNull()
    expect(parseNumeric('   ')).toBeNull()
  })

  it('returns null for non-numeric text', () => {
    expect(parseNumeric('Active')).toBeNull()
    expect(parseNumeric('N/A')).toBeNull()
  })
})

describe('parseMarkdownTable', () => {
  it('infers a numeric column when the majority of cells are numbers', () => {
    const result = parseMarkdownTable(
      ['Status', 'Amount'],
      [
        ['Approved', '1000'],
        ['Draft', '250.5'],
        ['Closed', '0'],
      ],
    )
    expect(result.columns).toEqual([
      { name: 'Status', numeric: false, kind: 'text' },
      { name: 'Amount', numeric: true, kind: 'currency' },
    ])
    expect(result.numericIndexes).toEqual([1])
    expect(result.labelIndex).toBe(0)
  })

  it('does not treat a mostly-text column as numeric', () => {
    const result = parseMarkdownTable(
      ['Status', 'Note'],
      [
        ['Approved', 'ok'],
        ['Draft', 'pending'],
        ['Closed', '5'],
      ],
    )
    expect(result.columns[1].numeric).toBe(false)
    expect(result.chartable).toBe(false)
  })

  it('marks a table chartable when it has a label and a numeric column', () => {
    const result = parseMarkdownTable(
      ['Department', 'Count'],
      [['CIO', '12'], ['CTO', '8']],
    )
    expect(result.chartable).toBe(true)
  })

  it('is not chartable with no numeric column', () => {
    const result = parseMarkdownTable(
      ['Title', 'Status'],
      [['Laptop', 'Active'], ['Chair', 'Draft']],
    )
    expect(result.chartable).toBe(false)
  })

  it('is not chartable with no label column', () => {
    const result = parseMarkdownTable(
      ['A', 'B'],
      [['1', '2'], ['3', '4']],
    )
    expect(result.chartable).toBe(false)
  })

  it('flags an aggregation: exactly one label + one numeric column', () => {
    const result = parseMarkdownTable(
      ['Status', 'Total'],
      [['Approved', '5000'], ['Rejected', '1200']],
    )
    expect(result.isAggregation).toBe(true)
  })

  it('does not flag a multi-numeric table as an aggregation', () => {
    const result = parseMarkdownTable(
      ['Status', 'Count', 'Total'],
      [['Approved', '3', '5000'], ['Rejected', '2', '1200']],
    )
    expect(result.isAggregation).toBe(false)
    expect(result.numericIndexes).toEqual([1, 2])
  })

  it('handles an empty rows list', () => {
    const result = parseMarkdownTable(['Status', 'Amount'], [])
    expect(result.chartable).toBe(false)
  })
})

describe('parseMarkdownTable column kinds', () => {
  it('classifies a money-named numeric column as currency', () => {
    const r = parseMarkdownTable(
      ['Status', 'Estimated Amount (€)'],
      [['Approved', '6343.32'], ['Closed', '1514.88']],
    )
    expect(r.columns[1].kind).toBe('currency')
    expect(r.columns[1].numeric).toBe(true)
  })

  it('classifies a non-money numeric column as number', () => {
    const r = parseMarkdownTable(
      ['Status', 'Count'],
      [['Approved', '12'], ['Closed', '3']],
    )
    expect(r.columns[1].kind).toBe('integer')
    expect(r.columns[1].numeric).toBe(true)
  })

  it('classifies row_count as integer even when values look like currency', () => {
    const r = parseMarkdownTable(
      ['Status', 'row_count'],
      [['Approved', '4.00'], ['Closed', '12']],
    )
    expect(r.columns[1].kind).toBe('integer')
  })

  it('does not classify Sum header as currency for count-style tables', () => {
    const r = parseMarkdownTable(
      ['Status', 'Sum'],
      [['Approved', '4'], ['Closed', '12']],
    )
    expect(r.columns[1].kind).toBe('number')
  })

  it('classifies an ISO date column as date (and not numeric)', () => {
    const r = parseMarkdownTable(
      ['Created', 'Count'],
      [['2026-05-25', '1'], ['2026-01-03', '2']],
    )
    expect(r.columns[0].kind).toBe('date')
    expect(r.columns[0].numeric).toBe(false)
  })

  it('classifies a plain text column as text', () => {
    const r = parseMarkdownTable(
      ['Title', 'Count'],
      [['Laptop', '1'], ['Chair', '2']],
    )
    expect(r.columns[0].kind).toBe('text')
  })
})
