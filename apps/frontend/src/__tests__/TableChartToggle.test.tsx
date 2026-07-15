import { render, screen, fireEvent } from '@testing-library/react'
import { TableChartToggle } from '@/features/chat/components/TableChartToggle'
import { parseMarkdownTable } from '@/features/chat/lib/parseMarkdownTable'

const origTable = (
  <table data-testid="orig-table">
    <tbody>
      <tr>
        <td>x</td>
      </tr>
    </tbody>
  </table>
)

const aggregation = parseMarkdownTable(
  ['Status', 'Total'],
  [
    ['Approved', '5000'],
    ['Rejected', '1200'],
  ],
)

const multiNumeric = parseMarkdownTable(
  ['Status', 'Count', 'Total'],
  [
    ['Approved', '3', '5000'],
    ['Rejected', '2', '1200'],
  ],
)

const chart = () => document.querySelector('[data-slot="chart"]')

describe('TableChartToggle', () => {
  it('defaults to the table view for an aggregation table, with pie preselected for chart', () => {
    render(<TableChartToggle table={aggregation}>{origTable}</TableChartToggle>)
    expect(screen.getByTestId('orig-table')).toBeInTheDocument()
    expect(chart()).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /chart/i }))
    expect(chart()).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /pie/i })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('defaults to the table view for a non-aggregation chartable table', () => {
    render(<TableChartToggle table={multiNumeric}>{origTable}</TableChartToggle>)
    expect(screen.getByTestId('orig-table')).toBeInTheDocument()
    expect(chart()).not.toBeInTheDocument()
  })

  it('switches from table to chart and back', () => {
    render(<TableChartToggle table={multiNumeric}>{origTable}</TableChartToggle>)
    fireEvent.click(screen.getByRole('button', { name: /chart/i }))
    expect(chart()).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /table/i }))
    expect(screen.getByTestId('orig-table')).toBeInTheDocument()
  })

  it('lets the user switch chart type to donut', () => {
    render(<TableChartToggle table={aggregation}>{origTable}</TableChartToggle>)
    fireEvent.click(screen.getByRole('button', { name: /chart/i }))
    fireEvent.click(screen.getByRole('button', { name: /donut/i }))
    expect(screen.getByRole('button', { name: /donut/i })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('shows value-column choices only when there are multiple numeric columns', () => {
    const { rerender } = render(
      <TableChartToggle table={aggregation}>{origTable}</TableChartToggle>,
    )
    // single numeric column → no value-column picker
    expect(screen.queryByRole('button', { name: 'Total' })).not.toBeInTheDocument()

    rerender(
      <TableChartToggle table={multiNumeric}>{origTable}</TableChartToggle>,
    )
    fireEvent.click(screen.getByRole('button', { name: /chart/i }))
    // multiple numeric columns → value-column buttons present
    expect(screen.getByRole('button', { name: 'Count' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Total' })).toBeInTheDocument()
  })
})
