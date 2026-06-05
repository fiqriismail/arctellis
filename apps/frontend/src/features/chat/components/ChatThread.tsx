'use client'

import { useRef, useEffect } from 'react'
import { Sparkles } from 'lucide-react'
import { Message } from '@/features/chat/types'

interface ChatThreadProps {
  messages: Message[]
}

export function ChatThread({ messages }: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div style={{ maxWidth: 780, margin: '0 auto', padding: '28px 24px 16px' }}>
      {messages.map((msg, i) =>
        msg.role === 'user'
          ? <UserMessage key={i} text={msg.text} />
          : <AssistantMessage key={i} text={msg.text} />
      )}
      <div ref={bottomRef} />
    </div>
  )
}

function UserMessage({ text }: { text: string }) {
  return (
    <div
      data-testid="message"
      className="anim-msg"
      style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 22 }}
    >
      <div style={{
        maxWidth: '78%',
        background: 'var(--muted)',
        color: 'var(--foreground)',
        padding: '10px 15px',
        borderRadius: '16px 16px 4px 16px',
        fontSize: 14.5,
        lineHeight: 1.5,
        whiteSpace: 'pre-wrap',
        fontWeight: 450,
      }}>
        {text}
      </div>
    </div>
  )
}

function AssistantMessage({ text }: { text: string }) {
  return (
    <div
      data-testid="message"
      className="anim-msg"
      style={{ display: 'flex', gap: 13, marginBottom: 30 }}
    >
      <div style={{
        width: 30, height: 30, borderRadius: 8, flexShrink: 0,
        background: 'var(--brand)', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: 'var(--shadow-card-sm)',
      }}>
        <Sparkles style={{ width: 16, height: 16 }} strokeWidth={2.2} />
      </div>
      <div style={{ flex: 1, minWidth: 0, paddingTop: 3 }}>
        <div style={{
          fontSize: 14.5,
          lineHeight: 1.62,
          color: 'var(--foreground)',
          whiteSpace: 'pre-wrap',
        }}>
          {text}
        </div>
      </div>
    </div>
  )
}
