import Image from 'next/image'
import { Button } from '@/components/ui/button'

interface UnauthorizedCardProps {
  account: { name?: string; username: string }
  onSignOut: () => void
}

export function UnauthorizedCard({ account, onSignOut }: UnauthorizedCardProps) {
  const displayName = account.name ?? account.username

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
            src="/arctellis-lockup.png"
            alt="Arctellis"
            width={118}
            height={28}
            priority
          />
        </div>
        <h1 style={{ fontSize: 22, fontWeight: 680, letterSpacing: '-.02em', margin: '0 0 8px' }}>
          Access Denied
        </h1>
        <p style={{ fontSize: 14, color: 'var(--muted-foreground)', margin: '0 0 16px', lineHeight: 1.5 }}>
          You don&apos;t have access to this application.
        </p>
        <p style={{ fontSize: 13, color: 'var(--muted-foreground)', margin: '0 0 28px', lineHeight: 1.4 }}>
          <strong style={{ color: 'var(--foreground)', display: 'block' }}>{displayName}</strong>
          {account.name ? account.username : null}
        </p>
        <Button
          onClick={onSignOut}
          style={{ width: '100%' }}
          className="bg-[var(--azure)] text-white hover:bg-[var(--azure)]/90"
        >
          Sign out
        </Button>
      </div>
    </div>
  )
}
