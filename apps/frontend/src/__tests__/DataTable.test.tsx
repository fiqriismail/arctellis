import { render, screen, fireEvent } from '@testing-library/react'
import { DataTable } from '@/features/chat/components/DataTable'
import { parseMarkdownTable } from '@/features/chat/lib/parseMarkdownTable'

const table = parseMarkdownTable(
  ['Status', 'Estimated Amount (€)', 'Created'],
  [
    ['Approved', '6343.32', '2026-05-25'],
    ['Closed', '1514.88', '2026-01-03'],
    ['Draft', '252.48', '2026-03-10'],
  ],
)

function firstCellTexts(): (string | null)[] {
  const tbody = document.querySelector('tbody')!
  return Array.from(tbody.querySelectorAll('tr')).map(
    (r) => r.querySelector('td')!.textContent,
  )
}

describe('DataTable', () => {
  it('renders a rounded container and headers', () => {
    const { container } = render(<DataTable table={table} />)
    expect(container.querySelector('div.rounded-lg')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
  })

  it('formats currency cells as € with two decimals', () => {
    render(<DataTable table={table} />)
    expect(screen.getByText('€6,343.32')).toBeInTheDocument()
    expect(screen.getByText('€252.48')).toBeInTheDocument()
  })

  it('formats date cells as dd-mm-yyyy', () => {
    render(<DataTable table={table} />)
    expect(screen.getByText('25-05-2026')).toBeInTheDocument()
    expect(screen.getByText('03-01-2026')).toBeInTheDocument()
  })

  it('renders status badges for known statuses', () => {
    render(<DataTable table={table} />)
    expect(screen.getByText('Approved').tagName).not.toBe('TD')
  })

  it('right-aligns currency cells', () => {
    render(<DataTable table={table} />)
    const cell = screen.getByText('€6,343.32').closest('td')!
    expect(cell.className).toMatch(/text-right/)
  })

  it('sorts a numeric column ascending then descending', () => {
    render(<DataTable table={table} />)
    expect(firstCellTexts()).toEqual(['Approved', 'Closed', 'Draft'])

    const amountHeader = screen.getByRole('button', { name: /Estimated Amount/i })
    fireEvent.click(amountHeader) // asc: 252, 1514, 6343
    expect(firstCellTexts()).toEqual(['Draft', 'Closed', 'Approved'])

    fireEvent.click(amountHeader) // desc
    expect(firstCellTexts()).toEqual(['Approved', 'Closed', 'Draft'])
  })

  it('sorts a date column chronologically', () => {
    render(<DataTable table={table} />)
    fireEvent.click(screen.getByRole('button', { name: /Created/i }))
    // 2026-01-03 (Closed), 2026-03-10 (Draft), 2026-05-25 (Approved)
    expect(firstCellTexts()).toEqual(['Closed', 'Draft', 'Approved'])
  })

  it('sorts a text column alphabetically', () => {
    render(<DataTable table={table} />)
    const statusHeader = screen.getByRole('button', { name: /Status/i })
    fireEvent.click(statusHeader) // asc (already alpha)
    expect(firstCellTexts()).toEqual(['Approved', 'Closed', 'Draft'])
    fireEvent.click(statusHeader) // desc
    expect(firstCellTexts()).toEqual(['Draft', 'Closed', 'Approved'])
  })
})
