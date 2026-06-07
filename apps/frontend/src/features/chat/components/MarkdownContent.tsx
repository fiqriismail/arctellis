'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'
import { DataTable } from './DataTable'
import { TableChartToggle } from './TableChartToggle'
import { extractTableFromNode } from '../lib/extractTableFromNode'
import { parseMarkdownTable } from '../lib/parseMarkdownTable'

const components: Components = {
  p({ children }) {
    return <p style={{ margin: '0 0 12px' }}>{children}</p>
  },
  strong({ children }) {
    return <strong style={{ fontWeight: 600 }}>{children}</strong>
  },
  em({ children }) {
    return <em style={{ fontStyle: 'italic', color: 'var(--muted-foreground)' }}>{children}</em>
  },
  ul({ children }) {
    return <ul style={{ margin: '8px 0 12px', paddingLeft: 22 }}>{children}</ul>
  },
  ol({ children }) {
    return <ol style={{ margin: '8px 0 12px', paddingLeft: 22 }}>{children}</ol>
  },
  li({ children }) {
    return <li style={{ marginBottom: 5, fontSize: 'inherit' }}>{children}</li>
  },
  pre({ children }) {
    return (
      <pre style={{
        background: '#18181b',
        color: '#e4e4e7',
        padding: '14px 16px',
        borderRadius: 10,
        fontSize: 12.5,
        overflowX: 'auto',
        margin: '12px 0',
        fontFamily: 'ui-monospace, monospace',
        lineHeight: 1.6,
        boxShadow: '0 2px 8px rgba(0,0,0,.15)',
      }}>
        {children}
      </pre>
    )
  },
  code({ className, children }) {
    // className is set when inside a fenced code block (e.g. "language-js").
    // When className is set, the code is already inside a styled <pre> — render plain.
    // When className is absent, this is inline code — apply brand-tint style.
    if (className) {
      return (
        <code style={{ fontFamily: 'ui-monospace, monospace', fontSize: 'inherit', color: 'inherit' }}>
          {children}
        </code>
      )
    }
    return (
      <code style={{
        fontFamily: 'ui-monospace, monospace',
        fontSize: 12.5,
        background: 'var(--brand-tint)',
        color: 'var(--brand-strong)',
        padding: '2px 6px',
        borderRadius: 4,
        border: '1px solid var(--border)',
      }}>
        {children}
      </code>
    )
  },
  h2({ children }) {
    return (
      <h2 style={{
        fontSize: 17,
        fontWeight: 700,
        margin: '16px 0 7px',
        color: 'var(--foreground)',
        letterSpacing: '-0.01em',
        paddingBottom: 5,
        borderBottom: '1px solid var(--border)',
      }}>
        {children}
      </h2>
    )
  },
  h3({ children }) {
    return (
      <h3 style={{
        fontSize: 15,
        fontWeight: 600,
        margin: '13px 0 6px',
        color: 'var(--foreground)',
      }}>
        {children}
      </h3>
    )
  },
  table({ node }) {
    if (!node) return null

    // Render a sortable, formatted data table from the parsed cells; offer a
    // chart view when the table has label + numeric columns.
    const { headers, rows } = extractTableFromNode(node)
    const parsed = parseMarkdownTable(headers, rows)
    if (!parsed.columns.length) return null

    // Only offer the chart view for simple two-column aggregations
    // (one label + one numeric). Wider tables keep it to the table to avoid
    // ambiguous/confusing charts.
    const dataTable = <DataTable table={parsed} />
    return parsed.isAggregation ? (
      <TableChartToggle table={parsed}>{dataTable}</TableChartToggle>
    ) : (
      dataTable
    )
  },
  blockquote({ children }) {
    return (
      <blockquote style={{
        borderLeft: '3px solid var(--brand)',
        margin: '10px 0',
        padding: '6px 12px',
        background: 'var(--brand-tint)',
        borderRadius: '0 6px 6px 0',
        color: 'var(--muted-foreground)',
        fontStyle: 'italic',
      }}>
        {children}
      </blockquote>
    )
  },
}

interface MarkdownContentProps {
  text: string
}

export function MarkdownContent({ text }: MarkdownContentProps) {
  return (
    <div style={{ fontSize: 14.5, lineHeight: 1.68, color: 'var(--foreground)' }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {text}
      </ReactMarkdown>
    </div>
  )
}
