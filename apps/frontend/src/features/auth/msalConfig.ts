import { PublicClientApplication } from '@azure/msal-browser'

export const msalInstance = new PublicClientApplication({
  auth: {
    clientId: process.env.NEXT_PUBLIC_ENTRA_CLIENT_ID!,
    authority: `https://login.microsoftonline.com/${process.env.NEXT_PUBLIC_ENTRA_TENANT_ID}`,
    redirectUri: typeof window !== 'undefined' ? window.location.origin : '/',
  },
  cache: { cacheLocation: 'sessionStorage', storeAuthStateInCookie: false },
})
