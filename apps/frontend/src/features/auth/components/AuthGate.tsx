'use client'

import { useIsAuthenticated, useMsal } from '@azure/msal-react'
import { SignInCard } from './SignInCard'

interface AuthGateProps {
  children: React.ReactNode
}

export function AuthGate({ children }: AuthGateProps) {
  const isAuthenticated = useIsAuthenticated()
  const { instance } = useMsal()

  const handleSignIn = () => {
    instance.loginPopup({
      scopes: [process.env.NEXT_PUBLIC_ENTRA_API_SCOPE!],
    })
  }

  if (!isAuthenticated) {
    return <SignInCard onSignIn={handleSignIn} />
  }

  return <>{children}</>
}
