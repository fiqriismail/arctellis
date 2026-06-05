import { render, screen } from '@testing-library/react'
import { MarkdownContent } from '@/features/chat/components/MarkdownContent'

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
    const md = '| Name | Age |\n|---|---|\n| Alice | 30 |'
    render(<MarkdownContent text={md} />)
    expect(document.querySelector('table')).toBeInTheDocument()
    expect(screen.getByText('Name')).toBeInTheDocument()
    expect(screen.getByText('Alice')).toBeInTheDocument()
  })
})
