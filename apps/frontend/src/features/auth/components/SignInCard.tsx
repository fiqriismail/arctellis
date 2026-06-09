import Image from 'next/image'
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
        <div style={{ margin: '0 auto 24px', display: 'flex', justifyContent: 'center' }}>
          <Image
            src="/group_one.svg"
            alt="group.one"
            width={142}
            height={26}
            priority
          />
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 680, letterSpacing: '-.02em', margin: '0 0 8px' }}>
          RTP Intelligent Hub
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
