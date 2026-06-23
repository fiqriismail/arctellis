import {
  isCountHeader,
  isMoneyHeader,
  detectCurrency,
  formatCurrency,
  formatInteger,
  parseDate,
  formatDate,
  formatCellValue,
} from '@/features/chat/lib/formatCell'

describe('isCountHeader', () => {
  it.each([
    'Count',
    'row_count',
    'Row Count',
    'Number of requests',
    '# of items',
    'Record Count',
  ])('treats %s as a count column', (h) => {
    expect(isCountHeader(h)).toBe(true)
  })

  it.each(['Estimated Amount (€)', 'Total Cost', 'Sum of Estimated Amount'])(
    'does not treat %s as a count column',
    (h) => {
      expect(isCountHeader(h)).toBe(false)
    },
  )
})

describe('isMoneyHeader', () => {
  it.each([
    'Amount',
    'Estimated Amount (€)',
    'Total Cost',
    'Budget',
    'Unit Price',
    'Sum of Estimated Amount',
  ])('treats %s as a money column', (h) => {
    expect(isMoneyHeader(h)).toBe(true)
  })

  it.each(['Count', 'Quantity', 'ID', 'Status', 'Title', 'Age'])(
    'does not treat %s as a money column',
    (h) => {
      expect(isMoneyHeader(h)).toBe(false)
    },
  )

  it.each(['Total', 'Sum'])(
    'does not treat bare %s as a money column (count aggregations use this header)',
    (h) => {
      expect(isMoneyHeader(h)).toBe(false)
    },
  )
})

describe('detectCurrency', () => {
  it('detects currency from a leading symbol', () => {
    expect(detectCurrency('$1,000')).toBe('USD')
    expect(detectCurrency('£500')).toBe('GBP')
    expect(detectCurrency('€42')).toBe('EUR')
  })

  it('returns null for a bare number', () => {
    expect(detectCurrency('6343.32')).toBeNull()
  })
})

describe('formatInteger', () => {
  it('formats whole numbers without decimals or currency', () => {
    expect(formatInteger(4)).toBe('4')
    expect(formatInteger(1234)).toBe('1,234')
  })
})

describe('formatCurrency', () => {
  it('formats with two decimals, thousands separators and € by default', () => {
    expect(formatCurrency(6343.32)).toBe('€6,343.32')
    expect(formatCurrency(1514.8)).toBe('€1,514.80')
    expect(formatCurrency(0)).toBe('€0.00')
  })

  it('uses the given currency symbol', () => {
    expect(formatCurrency(1000, 'USD')).toBe('$1,000.00')
    expect(formatCurrency(500, 'GBP')).toBe('£500.00')
  })
})

describe('parseDate', () => {
  it('parses an ISO date', () => {
    const d = parseDate('2026-05-25')
    expect(d?.getFullYear()).toBe(2026)
    expect(d?.getMonth()).toBe(4) // May (0-indexed)
    expect(d?.getDate()).toBe(25)
  })

  it('parses an ISO datetime', () => {
    expect(parseDate('2026-05-25T13:30:00Z')?.getDate()).toBe(25)
  })

  it('returns null for non-dates', () => {
    expect(parseDate('Approved')).toBeNull()
    expect(parseDate('1234')).toBeNull()
    expect(parseDate('')).toBeNull()
  })
})

describe('formatDate', () => {
  it('formats to dd-mm-yyyy', () => {
    expect(formatDate(new Date(2026, 4, 25))).toBe('25-05-2026')
    expect(formatDate(new Date(2026, 0, 3))).toBe('03-01-2026')
  })
})

describe('formatCellValue', () => {
  it('formats currency cells, defaulting to €', () => {
    expect(formatCellValue('6343.32', 'currency')).toBe('€6,343.32')
  })

  it('keeps an explicit currency symbol', () => {
    expect(formatCellValue('$1000', 'currency')).toBe('$1,000.00')
  })

  it('formats date cells to dd-mm-yyyy', () => {
    expect(formatCellValue('2026-05-25', 'date')).toBe('25-05-2026')
  })

  it('leaves number and text cells unchanged', () => {
    expect(formatCellValue('12', 'number')).toBe('12')
    expect(formatCellValue('Laptop', 'text')).toBe('Laptop')
  })

  it('formats integer cells without currency or decimals', () => {
    expect(formatCellValue('4', 'integer')).toBe('4')
    expect(formatCellValue('4.00', 'integer')).toBe('4')
    expect(formatCellValue('1234', 'integer')).toBe('1,234')
  })

  it('returns the raw value when a currency cell is not numeric', () => {
    expect(formatCellValue('N/A', 'currency')).toBe('N/A')
  })
})
