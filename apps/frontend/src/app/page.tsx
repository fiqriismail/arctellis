'use client'

import { useState } from 'react'
import { Sparkles, AlertTriangle, AlignLeft, User, Clock } from 'lucide-react'

import { ChatHeader } from '@/features/chat/components/ChatHeader'
import { ChatInput } from '@/features/chat/components/ChatInput'

const SUGGESTIONS = [
  { label: 'Show overdue tasks',        icon: AlertTriangle, tint: 'var(--status-red)' },
  { label: 'Summarize the list',        icon: AlignLeft,     tint: 'var(--brand)' },
  { label: 'Who has the most tasks?',   icon: User,          tint: 'var(--status-green)' },
  { label: 'High-priority in progress', icon: Clock,         tint: 'var(--status-amber)' },
]

export default function HomePage() {
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
      <ChatHeader />

      <div style={{
        flex: 1, overflowY: 'auto',
        display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
        padding: '40px 24px',
      }}>
        <div style={{ width: '100%', maxWidth: 680 }}>

          {/* Hero */}
          <div style={{ textAlign: 'center', marginBottom: 26 }}>
            <div style={{
              width: 52, height: 52, borderRadius: 14,
              background: 'var(--brand)', color: '#fff',
              margin: '0 auto 18px',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: 'var(--shadow-card-md)',
            }}>
              <Sparkles style={{ width: 26, height: 26 }} strokeWidth={2.1} />
            </div>
            <h1 style={{ fontSize: 30, fontWeight: 680, letterSpacing: '-.025em', margin: '0 0 8px' }}>
              SharePoint List AI Assistant
            </h1>
            <p style={{ fontSize: 15.5, color: 'var(--muted-foreground)', margin: 0, lineHeight: 1.5 }}>
              Ask anything about{' '}
              <span style={{ fontWeight: 550, color: 'var(--foreground)' }}>Project Tasks</span>
              {' '}in plain English — no formulas, no filters.
            </p>
          </div>

          {/* Composer */}
          <ChatInput onSubmit={() => {}} />

          {/* Suggestions */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 18 }}>
            {SUGGESTIONS.map(s => <SuggestionCard key={s.label} {...s} />)}
          </div>

        </div>
      </div>
    </div>
  )
}

function SuggestionCard({ label, icon: Icon, tint }: { label: string; icon: React.ElementType; tint: string }) {
  const [hovered, setHovered] = useState(false)
  return (
    <button
      onClick={() => {}}
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
