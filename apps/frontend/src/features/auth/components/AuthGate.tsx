'use client'

import { useIsAuthenticated, useMsal } from '@azure/msal-react'
import { SignInCard } from './SignInCard'

interface AuthGateProps {
  children: React.ReactNode
}

export function AuthGate({ children }: AuthGateProps) {
  const isAuthenticated = useIsAuthenticated()
  const { instance } = useMsal()

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
      // user_cancelled or popup_window_error — no action needed
      console.warn('loginPopup dismissed', e)
    }
  }

  if (!isAuthenticated) {
    return <SignInCard onSignIn={handleSignIn} />
  }

  return <>{children}</>
}
