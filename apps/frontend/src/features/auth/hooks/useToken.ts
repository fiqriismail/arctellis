'use client'

import { InteractionRequiredAuthError } from '@azure/msal-browser'
import { useMsal } from '@azure/msal-react'

export function useToken() {
  const { instance, accounts } = useMsal()
  const scope = process.env.NEXT_PUBLIC_ENTRA_API_SCOPE!

  const getToken = async (): Promise<string> => {
    const account = accounts[0] ?? instance.getActiveAccount() ?? undefined
    try {
      const response = await instance.acquireTokenSilent({
        scopes: [scope],
        account,
      })
      return response.accessToken
    } catch (err) {
      if (err instanceof InteractionRequiredAuthError) {
        const response = await instance.acquireTokenPopup({ scopes: [scope] })
        return response.accessToken
      }
      throw err
    }
  }

  return { getToken }
}
