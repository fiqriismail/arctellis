'use client'

import { useState } from 'react'
import { Sparkles, AlertTriangle, PieChart, BadgeEuro, Building2 } from 'lucide-react'

import { ChatHeader } from '@/features/chat/components/ChatHeader'
import { ChatInput } from '@/features/chat/components/ChatInput'
import { ChatThread } from '@/features/chat/components/ChatThread'
import { useChat } from '@/features/chat/hooks/useChat'
import { AuthGate } from '@/features/auth/components/AuthGate'

const SUGGESTIONS = [
  { label: 'Requests under SME Review',       icon: AlertTriangle, tint: 'var(--status-red)' },
  { label: 'Estimated amounts by status',     icon: PieChart,      tint: 'var(--brand)' },
  { label: 'Top requests by estimated amount', icon: BadgeEuro,    tint: 'var(--status-green)' },
  { label: 'Total spend by department',       icon: Building2,     tint: 'var(--status-amber)' },
]

export default function HomePage() {
  const { messages, streamingText, isStreaming, streamError, sendMessage, stopStream, resetSession } = useChat()

  return (
    <AuthGate>
      {messages.length > 0 ? (
        <div style={{ height: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--background)', overflow: 'hidden' }}>
          <ChatHeader onNewConversation={resetSession} />
          <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }} className="scroll">
            <ChatThread
              messages={messages}
              streamingText={streamingText}
              isStreaming={isStreaming}
              streamError={streamError}
            />
          </div>
          <div style={{
            flexShrink: 0,
            borderTop: '1px solid var(--border)',
            background: 'rgba(255,255,255,.9)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
          }}>
            <div className="mx-auto w-full max-w-[860px] px-4 pt-3.5 pb-4 md:px-6 lg:max-w-[1280px] xl:max-w-[1536px]">
              <ChatInput onSubmit={sendMessage} onStop={stopStream} isStreaming={isStreaming} compact />
            </div>
          </div>
        </div>
      ) : (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
          <ChatHeader />
          <div style={{
            flex: 1, overflowY: 'auto',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            padding: '40px 24px',
          }}>
            <div style={{ width: '100%', maxWidth: 680 }}>
              <div style={{ textAlign: 'center', marginBottom: 26 }}>
                <div style={{
                  width: 52, height: 52, borderRadius: 14,
                  background: 'var(--brand)', color: 'var(--primary-foreground)',
                  margin: '0 auto 18px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  boxShadow: 'var(--shadow-card-md)',
                }}>
                  <Sparkles style={{ width: 26, height: 26 }} strokeWidth={2.1} />
                </div>
                <h1 style={{ fontSize: 30, fontWeight: 680, letterSpacing: '-.025em', margin: '0 0 8px' }}>
                  RTP Intelligent Hub
                </h1>
                <p style={{ fontSize: 15.5, color: 'var(--muted-foreground)', margin: 0, lineHeight: 1.5 }}>
                  Ask anything about your{' '}
                  <span style={{ fontWeight: 550, color: 'var(--foreground)' }}>purchase requests</span>
                  {' '}in plain English — no formulas, no filters.
                </p>
              </div>

              <ChatInput onSubmit={sendMessage} onStop={stopStream} isStreaming={isStreaming} />

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 18 }}>
                {SUGGESTIONS.map(s => <SuggestionCard key={s.label} {...s} onSubmit={sendMessage} />)}
              </div>
            </div>
          </div>
        </div>
      )}
    </AuthGate>
  )
}

function SuggestionCard({
  label, icon: Icon, tint, onSubmit,
}: {
  label: string
  icon: React.ElementType
  tint: string
  onSubmit: (text: string) => void
}) {
  const [hovered, setHovered] = useState(false)
  return (
    <button
      onClick={() => onSubmit(label)}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        display: 'flex', alignItems: 'center', gap: 11,
        padding: '13px 15px', textAlign: 'left',
        background: 'var(--card)',
        border: `1px solid ${hovered ? 'var(--border-strong)' : 'var(--border)'}`,
        borderRadius: 11, cursor: 'pointer', fontFamily: 'inherit',
        boxShadow: hovered ? 'var(--shadow-card-md)' : 'var(--shadow-card-sm)',
        transform: hovered ? 'translateY(-1px)' : 'none',
        transition: 'all .16s',
      }}
    >
      <span style={{
        width: 30, height: 30, borderRadius: 8, flexShrink: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        background: 'var(--muted-2)', border: '1px solid var(--border)',
        color: tint,
      }}>
        <Icon style={{ width: 15, height: 15 }} />
      </span>
      <span style={{ fontSize: 13.5, fontWeight: 500, color: 'var(--foreground)' }}>{label}</span>
    </button>
  )
}
