'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { ArrowUp, Square } from 'lucide-react'

interface ChatInputProps {
  onSubmit: (question: string) => void
  onStop?: () => void
  isStreaming?: boolean
  disabled?: boolean
  compact?: boolean
}

export function ChatInput({
  onSubmit,
  onStop,
  isStreaming = false,
  disabled = false,
  compact = false,
}: ChatInputProps) {
  const [value, setValue] = useState('')
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
    if (!trimmed || disabled || isStreaming) return
    onSubmit(trimmed)
    setValue('')
  }

  const handleStop = () => {
    onStop?.()
  }

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit() }
  }

  const canSend = !!value.trim() && !disabled && !isStreaming
  const buttonActive = isStreaming || canSend

  return (
    <div>
      <div
        className="input-bar"
        style={{
          display: 'flex', alignItems: 'flex-end', gap: 10,
          padding: '10px 10px 10px 16px',
          background: 'var(--card)',
          border: '1px solid var(--border-strong)',
          borderRadius: compact ? 14 : 16,
          boxShadow: 'var(--shadow-card-md)',
        }}
      >
        <textarea
          ref={ref}
          value={value}
          rows={1}
          disabled={disabled}
          onChange={e => setValue(e.target.value)}
          onKeyDown={onKey}
          placeholder="Ask a question about your purchase requests — e.g. estimated amounts by status…"
          style={{
            flex: 1, border: 'none', outline: 'none', resize: 'none',
            background: 'transparent', fontFamily: 'inherit',
            fontSize: 15, lineHeight: 1.5, color: 'var(--foreground)',
            maxHeight: 200, padding: '6px 0', margin: 0,
          }}
        />
        <button
          onClick={isStreaming ? handleStop : handleSubmit}
          disabled={!buttonActive}
          aria-label={isStreaming ? 'Stop' : 'Send'}
          style={{
            width: 34, height: 34, flexShrink: 0, borderRadius: 9,
            border: 'none', cursor: buttonActive ? 'pointer' : 'default',
            background: buttonActive ? 'var(--brand-gold)' : '#e4e4e7',
            color: buttonActive ? 'var(--ink)' : '#a1a1aa',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'background .15s', marginBottom: 1,
          }}
        >
          {isStreaming ? (
            <Square style={{ width: 14, height: 14 }} fill="currentColor" strokeWidth={0} />
          ) : (
            <ArrowUp style={{ width: 17, height: 17 }} strokeWidth={2.4} />
          )}
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
