'use client'

import { useIsAuthenticated, useMsal } from '@azure/msal-react'
import { SignInCard } from './SignInCard'
import { UnauthorizedCard } from './UnauthorizedCard'
import { useGroupAccess } from '@/features/auth/hooks/useGroupAccess'

interface AuthGateProps {
  children: React.ReactNode
}

export function AuthGate({ children }: AuthGateProps) {
  const isAuthenticated = useIsAuthenticated()
  const { instance, accounts } = useMsal()
  const { status } = useGroupAccess(isAuthenticated)

  const handleSignIn = async () => {
    try {
      const result = await instance.loginPopup({
        scopes: [process.env.NEXT_PUBLIC_ENTRA_API_SCOPE!],
        redirectUri: `${window.location.origin}/auth-redirect`,
      })
      if (result?.account) {
        instance.setActiveAccount(result.account)
      }
    } catch (e) {
      console.warn('loginPopup dismissed', e)
    }
  }

  const handleSignOut = async () => {
    try {
      await instance.logoutPopup()
    } catch (e) {
      console.warn('logoutPopup dismissed', e)
    }
  }

  if (!isAuthenticated) {
    return <SignInCard onSignIn={handleSignIn} />
  }

  if (status === 'loading') {
    return (
      <div style={{
        height: '100dvh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'var(--background)',
        color: 'var(--muted-foreground)',
        fontSize: 14,
      }}>
        Checking access…
      </div>
    )
  }

  if (status === 'unauthorized') {
    const account = accounts[0] ?? { username: '' }
    return (
      <UnauthorizedCard
        account={{ name: account.name, username: account.username }}
        onSignOut={handleSignOut}
      />
    )
  }

  return <>{children}</>
}
