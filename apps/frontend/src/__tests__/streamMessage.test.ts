import { streamMessage } from '@/features/chat/api/streamMessage'
import { ApiError } from '@/features/chat/api/apiError'

const getToken = async () => 'fake-token'

// Builds a fake Response whose body.getReader() yields the given SSE chunks.
function mockResponse(
  chunks: string[],
  { ok = true, status = 200 }: { ok?: boolean; status?: number } = {}
): Response {
  const encoder = new TextEncoder()
  let i = 0
  const body = {
    getReader() {
      return {
        read: async () => {
          if (i < chunks.length) {
            return { done: false, value: encoder.encode(chunks[i++]) }
          }
          return { done: true, value: undefined }
        },
        cancel: async () => {},
        releaseLock: () => {},
      }
    },
  }
  return { ok, status, body } as unknown as Response
}

async function collect(gen: AsyncGenerator<string>): Promise<string[]> {
  const out: string[] = []
  for await (const t of gen) out.push(t)
  return out
}

afterEach(() => { jest.restoreAllMocks() })

describe('streamMessage', () => {
  it('yields tokens in order and stops on [DONE]', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      mockResponse(['data: "Hello"\n\n', 'data: "world"\n\n', 'data: [DONE]\n\n', 'data: "ignored"\n\n'])
    )
    const tokens = await collect(
      streamMessage('q', 'sess', new AbortController().signal, getToken)
    )
    expect(tokens).toEqual(['Hello', 'world'])
  })

  it('attaches the Bearer token, URL and JSON body', async () => {
    const fetchMock = jest.fn().mockResolvedValue(mockResponse(['data: [DONE]\n\n']))
    global.fetch = fetchMock
    await collect(streamMessage('my question', 'sess-1', new AbortController().signal, getToken))

    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('http://localhost:8000/chat')
    expect(init.method).toBe('POST')
    expect(init.headers['Authorization']).toBe('Bearer fake-token')
    expect(init.headers['Content-Type']).toBe('application/json')
    expect(init.headers['Accept']).toBe('text/event-stream')
    expect(JSON.parse(init.body)).toEqual({ question: 'my question', session_id: 'sess-1' })
  })

  it('preserves a token that has its own leading space', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      mockResponse(['data: " world"\n\n', 'data: [DONE]\n\n'])
    )
    const tokens = await collect(
      streamMessage('q', 'sess', new AbortController().signal, getToken)
    )
    expect(tokens).toEqual([' world'])
  })

  it('throws ApiError(server) on the [ERROR] sentinel', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      mockResponse(['data: "partial"\n\n', 'data: [ERROR] boom\n\n'])
    )
    await expect(
      collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    ).rejects.toMatchObject({ name: 'ApiError', kind: 'server' })
  })

  it('throws ApiError(server) when the response has no body', async () => {
    global.fetch = jest.fn().mockResolvedValue({ ok: true, status: 200, body: null } as unknown as Response)
    await expect(
      collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    ).rejects.toMatchObject({ name: 'ApiError', kind: 'server' })
  })

  it('throws ApiError(auth) on HTTP 401', async () => {
    global.fetch = jest.fn().mockResolvedValue(mockResponse([], { ok: false, status: 401 }))
    await expect(
      collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    ).rejects.toMatchObject({ name: 'ApiError', kind: 'auth' })
  })

  it('throws ApiError(server) on other non-2xx', async () => {
    global.fetch = jest.fn().mockResolvedValue(mockResponse([], { ok: false, status: 500 }))
    await expect(
      collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    ).rejects.toMatchObject({ name: 'ApiError', kind: 'server' })
  })

  it('throws ApiError(network) when fetch rejects with a non-abort error', async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError('Failed to fetch'))
    await expect(
      collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    ).rejects.toMatchObject({ name: 'ApiError', kind: 'network' })
  })

  it('propagates AbortError (not ApiError) when fetch is aborted', async () => {
    global.fetch = jest.fn().mockRejectedValue(new DOMException('Aborted', 'AbortError'))
    let caught: Error | null = null
    try {
      await collect(streamMessage('q', 'sess', new AbortController().signal, getToken))
    } catch (e) {
      caught = e as Error
    }
    expect(caught).not.toBeNull()
    expect(caught!.name).toBe('AbortError')
    expect(caught).not.toBeInstanceOf(ApiError)
  })

  it('defensively ignores non-data lines within an event', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      mockResponse(['event: message\ndata: "Hi"\n\n', 'data: [DONE]\n\n'])
    )
    const tokens = await collect(
      streamMessage('q', 'sess', new AbortController().signal, getToken)
    )
    expect(tokens).toEqual(['Hi'])
  })

  it('throws ApiError(auth) when getToken rejects', async () => {
    const failingGetToken = async () => { throw new Error('popup closed') }
    global.fetch = jest.fn()
    await expect(
      collect(streamMessage('q', 'sess', new AbortController().signal, failingGetToken))
    ).rejects.toMatchObject({ name: 'ApiError', kind: 'auth' })
    expect(global.fetch).not.toHaveBeenCalled()
  })
})
