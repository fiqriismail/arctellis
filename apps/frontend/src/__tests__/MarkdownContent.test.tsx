import { render, screen } from '@testing-library/react'
import { MarkdownContent } from '@/features/chat/components/MarkdownContent'
import { StatusBadge } from '@/features/chat/components/StatusBadge'

describe('MarkdownContent', () => {
  it('renders a paragraph', () => {
    render(<MarkdownContent text="Hello world" />)
    expect(screen.getByText('Hello world')).toBeInTheDocument()
  })

  it('renders bold text as <strong>', () => {
    render(<MarkdownContent text="**bold text**" />)
    const el = document.querySelector('strong')
    expect(el).toBeInTheDocument()
    expect(el).toHaveTextContent('bold text')
  })

  it('renders italic text as <em>', () => {
    render(<MarkdownContent text="_italic text_" />)
    const el = document.querySelector('em')
    expect(el).toBeInTheDocument()
    expect(el).toHaveTextContent('italic text')
  })

  it('renders an unordered list', () => {
    render(<MarkdownContent text={'- item one\n- item two'} />)
    expect(document.querySelector('ul')).toBeInTheDocument()
    expect(screen.getByText('item one')).toBeInTheDocument()
    expect(screen.getByText('item two')).toBeInTheDocument()
  })

  it('renders an ordered list', () => {
    render(<MarkdownContent text={'1. first\n2. second'} />)
    expect(document.querySelector('ol')).toBeInTheDocument()
    expect(screen.getByText('first')).toBeInTheDocument()
  })

  it('renders inline code', () => {
    render(<MarkdownContent text={'Use `console.log` to debug'} />)
    const code = document.querySelector('code')
    expect(code).toBeInTheDocument()
    expect(code).toHaveTextContent('console.log')
  })

  it('renders a fenced code block inside <pre>', () => {
    render(<MarkdownContent text={'```\nconst x = 1;\n```'} />)
    const pre = document.querySelector('pre')
    expect(pre).toBeInTheDocument()
    expect(pre).toHaveTextContent('const x = 1;')
  })

  it('renders an h2 heading', () => {
    render(<MarkdownContent text="## Summary" />)
    expect(document.querySelector('h2')).toBeInTheDocument()
    expect(screen.getByText('Summary')).toBeInTheDocument()
  })

  it('renders a GFM table', () => {
    // Non-chartable (all text) so it stays a table rather than defaulting to a chart.
    const md = '| Name | Role |\n|---|---|\n| Alice | Admin |'
    render(<MarkdownContent text={md} />)
    expect(document.querySelector('table')).toBeInTheDocument()
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Alice')).toBeInTheDocument()
  })
})

describe('StatusBadge', () => {
  it('renders a badge for a known status value', () => {
    render(<StatusBadge value="Active" />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('renders plain text for an unknown value', () => {
    const { container } = render(<StatusBadge value="Some random text" />)
    expect(container.firstChild).toHaveTextContent('Some random text')
    expect(container.firstChild?.nodeName).toBe('SPAN')
  })

  it('is case-insensitive — lowercase matches', () => {
    render(<StatusBadge value="approved" />)
    expect(screen.getByText('approved')).toBeInTheDocument()
  })

  it('is case-insensitive — uppercase matches', () => {
    render(<StatusBadge value="REJECTED" />)
    expect(screen.getByText('REJECTED')).toBeInTheDocument()
  })

  it('renders Rejected with destructive styling', () => {
    const { container } = render(<StatusBadge value="Rejected" />)
    const badge = container.firstChild as HTMLElement
    expect(badge.className).toMatch(/destructive/)
  })

  it('renders Approved with success styling', () => {
    const { container } = render(<StatusBadge value="Approved" />)
    const badge = container.firstChild as HTMLElement
    expect(badge.className).toMatch(/bg-green-100/)
  })

  it('renders Under SME Review with warning styling', () => {
    const { container } = render(<StatusBadge value="Under SME Review" />)
    const badge = container.firstChild as HTMLElement
    expect(badge.className).toMatch(/bg-amber-100/)
  })

  it('renders Draft with secondary styling', () => {
    const { container } = render(<StatusBadge value="Draft" />)
    const badge = container.firstChild as HTMLElement
    expect(badge.className).toMatch(/secondary/)
  })
})

describe('MarkdownContent table rendering', () => {
  const TABLE_MD = '| Title | Status |\n|---|---|\n| Laptop | Active |\n| Chair | Draft |'

  it('wraps table in a rounded border container', () => {
    const { container } = render(<MarkdownContent text={TABLE_MD} />)
    const wrapper = container.querySelector('div.rounded-lg')
    expect(wrapper).toBeInTheDocument()
    expect(wrapper?.querySelector('table')).toBeInTheDocument()
  })

  it('renders status cell as a badge, not bare td text', () => {
    render(<MarkdownContent text={TABLE_MD} />)
    const active = screen.getByText('Active')
    expect(active.tagName).not.toBe('TD')
  })

  it('renders non-status cell as plain text', () => {
    render(<MarkdownContent text={TABLE_MD} />)
    expect(screen.getByText('Laptop')).toBeInTheDocument()
  })

  it('renders table header cells', () => {
    render(<MarkdownContent text={TABLE_MD} />)
    expect(screen.getByText('Title')).toBeInTheDocument()
    expect(screen.getByText('Status')).toBeInTheDocument()
  })
})

describe('MarkdownContent chart toggle', () => {
  const AGG_MD =
    '| Status | Total |\n|---|---|\n| Approved | 5000 |\n| Rejected | 1200 |'
  const MULTI_MD =
    '| Status | Count | Total |\n|---|---|---|\n| Approved | 3 | 5000 |\n| Rejected | 2 | 1200 |'
  const PLAIN_MD =
    '| Title | Status |\n|---|---|\n| Laptop | Active |\n| Chair | Draft |'

  it('shows the table by default for an aggregation table, with a chart toggle available', () => {
    const { container } = render(<MarkdownContent text={AGG_MD} />)
    expect(container.querySelector('table')).toBeInTheDocument()
    expect(container.querySelector('[data-slot="chart"]')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /chart/i })).toBeInTheDocument()
  })

  it('shows no chart toggle for a table with more than two columns', () => {
    const { container } = render(<MarkdownContent text={MULTI_MD} />)
    expect(container.querySelector('table')).toBeInTheDocument()
    expect(container.querySelector('[data-slot="chart"]')).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /chart/i }),
    ).not.toBeInTheDocument()
  })

  it('shows no chart toggle for a non-chartable table', () => {
    const { container } = render(<MarkdownContent text={PLAIN_MD} />)
    expect(container.querySelector('[data-slot="chart"]')).not.toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /chart/i }),
    ).not.toBeInTheDocument()
  })
})
