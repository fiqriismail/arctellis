'use client'

import { useEffect } from 'react'
import { useMsal } from '@azure/msal-react'

export default function AuthRedirect() {
  const { instance } = useMsal()

  useEffect(() => {
    instance.initialize()
      .then(() => instance.handleRedirectPromise())
      .catch(console.error)
  }, [instance])

  return null
}
