import { Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface SignInCardProps {
  onSignIn: () => void
}

export function SignInCard({ onSignIn }: SignInCardProps) {
  return (
    <div style={{
      height: '100dvh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--background)',
    }}>
      <div style={{
        width: '100%',
        maxWidth: 360,
        padding: '40px 32px',
        background: 'var(--card)',
        border: '1px solid var(--border)',
        borderRadius: 16,
        boxShadow: 'var(--shadow-card-md)',
        textAlign: 'center',
      }}>
        <div style={{
          width: 52,
          height: 52,
          borderRadius: 14,
          background: 'var(--brand)',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 20px',
          boxShadow: 'var(--shadow-card-md)',
        }}>
          <Sparkles style={{ width: 26, height: 26 }} strokeWidth={2.1} />
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 680, letterSpacing: '-.02em', margin: '0 0 8px' }}>
          List AI Assistant
        </h1>
        <p style={{ fontSize: 14, color: 'var(--muted-foreground)', margin: '0 0 28px', lineHeight: 1.5 }}>
          Sign in with your organisation account to continue.
        </p>
        <Button onClick={onSignIn} style={{ width: '100%' }}>
          Sign in with Microsoft
        </Button>
      </div>
    </div>
  )
}
