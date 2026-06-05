'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { ArrowUp } from 'lucide-react'

interface ChatInputProps {
  onSubmit: (question: string) => void
  disabled?: boolean
  compact?: boolean
}

export function ChatInput({ onSubmit, disabled = false, compact = false }: ChatInputProps) {
  const [value, setValue] = useState('')
  const [focused, setFocused] = useState(false)
  const ref = useRef<HTMLTextAreaElement>(null)

  const autosize = useCallback(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }, [])

  useEffect(() => { autosize() }, [value, autosize])

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue('')
  }

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit() }
  }

  const canSend = !!value.trim() && !disabled

  return (
    <div>
      <div
        style={{
          display: 'flex', alignItems: 'flex-end', gap: 10,
          padding: '10px 10px 10px 16px',
          background: 'var(--card)',
          border: `1px solid ${focused ? 'var(--brand)' : 'var(--border-strong)'}`,
          borderRadius: compact ? 14 : 16,
          boxShadow: focused ? '0 0 0 3px rgba(15,108,189,.12)' : 'var(--shadow-card-md)',
          transition: 'box-shadow .2s, border-color .2s',
        }}
        onFocusCapture={() => setFocused(true)}
        onBlurCapture={() => setFocused(false)}
      >
        <textarea
          ref={ref}
          value={value}
          rows={1}
          disabled={disabled}
          onChange={e => setValue(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask a question about your SharePoint list…"
          style={{
            flex: 1, border: 'none', outline: 'none', resize: 'none',
            background: 'transparent', fontFamily: 'inherit',
            fontSize: 15, lineHeight: 1.5, color: 'var(--foreground)',
            maxHeight: 200, padding: '6px 0', margin: 0,
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={!canSend}
          aria-label="Send"
          style={{
            width: 34, height: 34, flexShrink: 0, borderRadius: 9,
            border: 'none', cursor: canSend ? 'pointer' : 'default',
            background: canSend ? 'var(--brand)' : '#e4e4e7', color: '#fff',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'background .15s', marginBottom: 1,
          }}
        >
          <ArrowUp style={{ width: 17, height: 17 }} strokeWidth={2.4} />
        </button>
      </div>

      <div style={{ display: 'flex', justifyContent: 'center', gap: 6, marginTop: 10, fontSize: 12, color: '#a1a1aa' }}>
        <span><Kbd>Enter</Kbd> to send</span>
        <span style={{ opacity: .5 }}>·</span>
        <span><Kbd>Shift</Kbd>+<Kbd>Enter</Kbd> for a new line</span>
      </div>
    </div>
  )
}

function Kbd({ children }: { children: React.ReactNode }) {
  return (
    <kbd style={{
      fontFamily: 'ui-monospace, "SF Mono", monospace',
      fontSize: 11, padding: '1.5px 5px', borderRadius: 5,
      background: 'var(--muted)', border: '1px solid var(--border)',
      color: 'var(--muted-foreground)', boxShadow: '0 1px 0 var(--border)',
    }}>{children}</kbd>
  )
}
