import { Sparkles } from 'lucide-react'

export function ChatHeader() {
  return (
    <header style={{
      height: 56, flexShrink: 0,
      borderBottom: '1px solid var(--border)',
      background: 'rgba(255,255,255,.82)',
      backdropFilter: 'blur(10px) saturate(1.1)',
      WebkitBackdropFilter: 'blur(10px) saturate(1.1)',
      display: 'flex', alignItems: 'center',
      padding: '0 20px', position: 'sticky', top: 0, zIndex: 20,
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 11 }}>
        <div style={{
          width: 30, height: 30, borderRadius: 8,
          background: 'var(--brand)', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: 'var(--shadow-card-sm)',
        }}>
          <Sparkles style={{ width: 17, height: 17 }} strokeWidth={2.2} />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
          <span style={{ fontSize: 14, fontWeight: 600, letterSpacing: '-.01em' }}>List AI Assistant</span>
          <span style={{ fontSize: 11.5, color: 'var(--muted-foreground)' }}>SharePoint · Group.one</span>
        </div>
      </div>
    </header>
  )
}
