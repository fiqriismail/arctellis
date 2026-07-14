'use client'

import { useRef, useEffect } from 'react'
import { Message } from '@/features/chat/types'
import { AppIcon } from '@/components/AppIcon'
import { MarkdownContent } from '@/features/chat/components/MarkdownContent'

interface ChatThreadProps {
  messages: Message[]
  streamingText?: string
  isStreaming?: boolean
  streamError?: string | null
}

export function ChatThread({
  messages,
  streamingText = '',
  isStreaming = false,
  streamError = null,
}: ChatThreadProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isStreaming])

  return (
    <div className="mx-auto w-full max-w-[860px] px-4 pt-7 pb-4 md:px-6 lg:max-w-[1280px] xl:max-w-[1536px]">
      {messages.map((msg, i) =>
        msg.role === 'user'
          ? <UserMessage key={i} text={msg.text} />
          : <AssistantMessage key={i} text={msg.text} />
      )}
      {isStreaming && (
        <div
          data-testid="streaming-message"
          className="anim-msg"
          style={{ display: 'flex', gap: 13, marginBottom: 30 }}
        >
          <div style={{
            width: 30, height: 30, borderRadius: 8, flexShrink: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            overflow: 'hidden',
            boxShadow: 'var(--shadow-card-sm)',
          }}>
            <AppIcon size={30} />
          </div>
          <div style={{ flex: 1, minWidth: 0, paddingTop: 3 }}>
            {streamingText && <MarkdownContent text={streamingText} />}
            <TypingIndicator />
          </div>
        </div>
      )}
      {!isStreaming && streamError && (
        <p
          data-testid="stream-error"
          style={{
            fontSize: 13,
            color: 'var(--status-red)',
            textAlign: 'center',
            padding: '8px 0 16px',
          }}
        >
          {streamError}
        </p>
      )}
      <div ref={bottomRef} />
    </div>
  )
}

function TypingIndicator() {
  return (
    <div
      data-testid="typing-indicator"
      style={{ display: 'flex', gap: 5, padding: '6px 0 2px' }}
    >
      {[0, 1, 2].map(i => (
        <span
          key={i}
          style={{
            display: 'inline-block',
            width: 7,
            height: 7,
            borderRadius: '50%',
            background: 'var(--azure)',
            animation: `typingBounce 1.2s ease-in-out ${i * 0.2}s infinite`,
          }}
        />
      ))}
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
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-card-sm)',
      }}>
        <AppIcon size={30} />
      </div>
      <div style={{ flex: 1, minWidth: 0, paddingTop: 3 }}>
        <MarkdownContent text={text} />
      </div>
    </div>
  )
}
