import Image from 'next/image'
import { Plus } from 'lucide-react'
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
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        <Image
          src="/arctellis-lockup.png"
          alt="Arctellis"
          width={118}
          height={28}
          priority
        />
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
