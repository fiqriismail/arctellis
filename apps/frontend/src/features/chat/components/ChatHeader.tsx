import { Plus, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ChatHeaderProps {
  onNewConversation?: () => void
}

export function ChatHeader({ onNewConversation }: ChatHeaderProps) {
  return (
    <header style={{
      height: 56, flexShrink: 0,
      borderBottom: '1px solid var(--border)',
      background: 'rgba(255,255,255,.82)',
      backdropFilter: 'blur(10px) saturate(1.1)',
      WebkitBackdropFilter: 'blur(10px) saturate(1.1)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
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
      {onNewConversation && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onNewConversation}
          className="rounded-md text-muted-foreground hover:text-foreground gap-1.5"
        >
          <Plus className="h-3.5 w-3.5" />
          New conversation
        </Button>
      )}
    </header>
  )
}
