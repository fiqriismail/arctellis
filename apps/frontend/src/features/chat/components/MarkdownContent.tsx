'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'

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
    return <li style={{ marginBottom: 5, fontSize: 14.5 }}>{children}</li>
  },
  code({ className, children }) {
    const isBlock = /language-(\w+)/.test(className || '') || String(children).includes('\n')
    if (isBlock) {
      return (
        <code style={{ fontFamily: 'ui-monospace, monospace', fontSize: 'inherit' }}>
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
        border: '1px solid #bfdbfe',
      }}>
        {children}
      </code>
    )
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
  table({ children }) {
    return (
      <table style={{
        width: '100%',
        borderCollapse: 'collapse',
        fontSize: 13.5,
        margin: '12px 0',
      }}>
        {children}
      </table>
    )
  },
  th({ children }) {
    return (
      <th style={{
        background: 'var(--brand)',
        color: '#fff',
        fontWeight: 600,
        textAlign: 'left',
        padding: '8px 12px',
      }}>
        {children}
      </th>
    )
  },
  td({ children }) {
    return (
      <td style={{
        padding: '7px 12px',
        borderBottom: '1px solid var(--border)',
        color: 'var(--foreground)',
      }}>
        {children}
      </td>
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
