import { renderHook, act, waitFor } from '@testing-library/react'
import { useChat } from '@/features/chat/hooks/useChat'
import { streamMessage } from '@/features/chat/api/streamMessage'

jest.mock('@/features/chat/api/streamMessage')
const mockStreamMessage = streamMessage as jest.Mock

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
    mockStreamMessage.mockImplementation(async function* (_: string, signal: AbortSignal) {
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
})
