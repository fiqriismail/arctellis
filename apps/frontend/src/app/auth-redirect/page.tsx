'use client'

import { useEffect } from 'react'
import { broadcastResponseToMainFrame } from '@azure/msal-browser/redirect-bridge'

export default function AuthRedirect() {
  useEffect(() => {
    // MSAL v5 popup flow: the popup lands here, broadcasts the auth response
    // back to the main window over a BroadcastChannel, and closes itself.
    // The main window completes the PKCE token exchange with its own cached
    // request. Do NOT call handleRedirectPromise here — that is the redirect
    // flow handler and throws no_token_request_cache_error in a popup.
    broadcastResponseToMainFrame().catch(console.error)
  }, [])

  return null
}
