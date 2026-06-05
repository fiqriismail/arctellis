'use client'

import { useEffect } from 'react'
import { msalInstance } from '@/features/auth/msalConfig'

export default function AuthRedirect() {
  useEffect(() => {
    msalInstance.handleRedirectPromise().catch(console.error)
  }, [])
  return null
}
