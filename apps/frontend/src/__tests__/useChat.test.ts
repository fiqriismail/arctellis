import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '@/features/chat/hooks/useChat'
import { streamMessage } from '@/features/chat/api/streamMessage'
import { ApiError } from '@/features/chat/api/apiError'

jest.mock('@/features/chat/api/streamMessage')
const mockStreamMessage = streamMessage as jest.Mock

const mockGetToken = jest.fn().mockResolvedValue('fake-token')
jest.mock('@/features/auth/hooks/useToken', () => ({
  useToken: () => ({ getToken: mockGetToken }),
}))

async function* makeTokenStream(tokens: string[]): AsyncGenerator<string> {
  for (const token of tokens) {
    yield token
  }
}

beforeEach(() => {
  jest.clearAllMocks()
})

describe('useChat', () => {
  it('appends the user message to messages immediately on sendMessage', async () => {
    let resolveStream: () => void
    mockStreamMessage.mockImplementation(async function* () {
      await new Promise<void>(r => { resolveStream = r })
      yield 'Hello'
    })
    const { result } = renderHook(() => useChat())

    act(() => { result.current.sendMessage('test question') })

    await waitFor(() => expect(result.current.isStreaming).toBe(true))
    expect(result.current.messages).toHaveLength(1)
    expect(result.current.messages[0]).toEqual({ role: 'user', text: 'test question' })

    // Let stream complete for cleanup
    resolveStream!()
    await waitFor(() => expect(result.current.isStreaming).toBe(false))
  })

  it('accumulates tokens and adds a completed assistant message when stream ends', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['Hello ', 'world']))
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[1]).toEqual({ role: 'assistant', text: 'Hello world' })
    expect(result.current.streamingText).toBe('')
    expect(result.current.isStreaming).toBe(false)
  })

  it('preserves partial text in messages and clears streaming when stopStream is called', async () => {
    mockStreamMessage.mockImplementation(async function* (_text: string, _sessionId: string, signal: AbortSignal) {
      yield 'Partial '
      await new Promise<never>((_, reject) =>
        signal.addEventListener('abort', () =>
          reject(new DOMException('Aborted', 'AbortError'))
        )
      )
    })

    const { result } = renderHook(() => useChat())

    act(() => { result.current.sendMessage('hi') })

    await waitFor(() => expect(result.current.streamingText).toBe('Partial '))

    act(() => { result.current.stopStream() })

    await waitFor(() => expect(result.current.isStreaming).toBe(false))

    expect(result.current.messages).toHaveLength(2)
    expect(result.current.messages[1]).toEqual({ role: 'assistant', text: 'Partial ' })
    expect(result.current.streamingText).toBe('')
  })

  it('sets streamError and preserves partial text on stream failure', async () => {
    mockStreamMessage.mockImplementation(async function* () {
      yield 'Partial '
      throw new Error('Network error')
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(result.current.streamError).toBe('Something went wrong — please try again')
    expect(result.current.messages).toHaveLength(2) // user message and assistant with partial text
    expect(result.current.messages[1]).toEqual({ role: 'assistant', text: 'Partial ' })
    expect(result.current.isStreaming).toBe(false)
  })

  it('clears streamError at the start of the next sendMessage', async () => {
    mockStreamMessage.mockImplementationOnce(async function* () {
      throw new Error('fail')
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('first')
    })

    expect(result.current.streamError).toBe('Something went wrong — please try again')

    mockStreamMessage.mockImplementationOnce(() => makeTokenStream(['OK']))

    await act(async () => {
      await result.current.sendMessage('second')
    })

    expect(result.current.streamError).toBeNull()
  })

  it('does not add an assistant message when stream completes with no tokens', async () => {
    mockStreamMessage.mockImplementation(async function* () {
      // yields nothing
    })
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(result.current.messages).toHaveLength(1) // user message only
    expect(result.current.messages[0].role).toBe('user')
    expect(result.current.isStreaming).toBe(false)
  })

  it('passes a valid UUID as sessionId to streamMessage', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    const sessionId = mockStreamMessage.mock.calls[0][1]
    expect(sessionId).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
    )
  })

  it('passes the same sessionId on consecutive sendMessage calls', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))
    const { result } = renderHook(() => useChat())

    await act(async () => { await result.current.sendMessage('first') })
    await act(async () => { await result.current.sendMessage('second') })

    const firstId = mockStreamMessage.mock.calls[0][1]
    const secondId = mockStreamMessage.mock.calls[1][1]
    expect(firstId).toBe(secondId)
  })

  it('resetSession clears messages and all streaming state', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['Hello']))
    const { result } = renderHook(() => useChat())

    await act(async () => { await result.current.sendMessage('test') })
    expect(result.current.messages).toHaveLength(2)

    act(() => { result.current.resetSession() })

    expect(result.current.messages).toHaveLength(0)
    expect(result.current.streamingText).toBe('')
    expect(result.current.streamError).toBeNull()
    expect(result.current.isStreaming).toBe(false)
  })

  it('resetSession generates a new sessionId', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))
    const { result } = renderHook(() => useChat())

    await act(async () => { await result.current.sendMessage('before') })
    const idBefore = mockStreamMessage.mock.calls[0][1]

    act(() => { result.current.resetSession() })

    await act(async () => { await result.current.sendMessage('after') })
    const idAfter = mockStreamMessage.mock.calls[1][1]

    expect(idAfter).not.toBe(idBefore)
    expect(idAfter).toMatch(
      /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/
    )
  })

  it('sendMessage after resetSession uses the new sessionId', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))
    const { result } = renderHook(() => useChat())

    await act(async () => { await result.current.sendMessage('before') })
    const idBefore = mockStreamMessage.mock.calls[0][1]

    act(() => { result.current.resetSession() })
    jest.clearAllMocks()
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))

    await act(async () => { await result.current.sendMessage('after') })
    const idAfter = mockStreamMessage.mock.calls[0][1]

    expect(idAfter).not.toBe(idBefore)
  })

  it('resetSession aborts an in-flight stream', async () => {
    let resolveStream: () => void
    mockStreamMessage.mockImplementation(async function* (_text: string, _sessionId: string, signal: AbortSignal) {
      yield 'Partial '
      await new Promise<never>((_, reject) => {
        resolveStream = () => reject(new DOMException('Aborted', 'AbortError'))
        signal.addEventListener('abort', () => resolveStream(), { once: true })
      })
    })

    const { result } = renderHook(() => useChat())

    act(() => { result.current.sendMessage('hi') })
    await waitFor(() => expect(result.current.streamingText).toBe('Partial '))
    expect(result.current.isStreaming).toBe(true)

    act(() => { result.current.resetSession() })

    await waitFor(() => expect(result.current.isStreaming).toBe(false))
    expect(result.current.messages).toHaveLength(0)
    expect(result.current.streamingText).toBe('')
  })

  it('shows the session-expired message on an auth ApiError', async () => {
    mockStreamMessage.mockImplementation(async function* () {
      throw new ApiError('auth', 'Unauthorized')
    })
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(result.current.streamError).toBe('Session expired — please sign in again')
    expect(result.current.isStreaming).toBe(false)
  })

  it('shows the generic message on a server ApiError', async () => {
    mockStreamMessage.mockImplementation(async function* () {
      throw new ApiError('server', 'boom')
    })
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(result.current.streamError).toBe('Something went wrong — please try again')
  })

  it('passes a getToken function as the fourth argument to streamMessage', async () => {
    mockStreamMessage.mockImplementation(() => makeTokenStream(['ok']))
    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test')
    })

    expect(typeof mockStreamMessage.mock.calls[0][3]).toBe('function')
  })
})
