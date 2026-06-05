import { ApiError } from './apiError'
import { getApiUrl } from '@/features/chat/config'

export async function* streamMessage(
  text: string,
  sessionId: string,
  signal: AbortSignal,
  getToken: () => Promise<string>
): AsyncGenerator<string> {
  let token: string
  try {
    token = await getToken()
  } catch {
    throw new ApiError('auth', 'Failed to acquire access token')
  }

  let response: Response
  try {
    response = await fetch(`${getApiUrl()}/chat`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
        Accept: 'text/event-stream',
      },
      body: JSON.stringify({ question: text, session_id: sessionId }),
      signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError('network', 'Network request failed')
  }

  if (!response.ok) {
    if (response.status === 401) throw new ApiError('auth', 'Unauthorized')
    throw new ApiError('server', `Request failed with status ${response.status}`)
  }
  if (!response.body) {
    throw new ApiError('server', 'Empty response body')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      let delimiter: number
      while ((delimiter = buffer.indexOf('\n\n')) !== -1) {
        const rawEvent = buffer.slice(0, delimiter)
        buffer = buffer.slice(delimiter + 2)

        for (const line of rawEvent.split('\n')) {
          if (!line.startsWith('data:')) continue
          const raw = line.slice(5).replace(/^ /, '')
          if (raw === '[DONE]') return
          if (raw.startsWith('[ERROR]')) {
            throw new ApiError('server', raw.slice('[ERROR]'.length).trim())
          }
          yield JSON.parse(raw) as string
        }
      }
    }
  } finally {
    reader.cancel().catch(() => {})
  }
}
