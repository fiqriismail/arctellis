import { getApiUrl } from '@/features/chat/config'

export async function checkAccess(getToken: () => Promise<string>): Promise<boolean> {
  const token = await getToken()
  const response = await fetch(`${getApiUrl()}/access`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (response.ok) return true
  if (response.status === 403) return false
  throw new Error(`Unexpected /access status: ${response.status}`)
}
