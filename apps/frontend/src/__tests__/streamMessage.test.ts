import { streamMessage } from '@/features/chat/api/streamMessage'

describe('streamMessage', () => {
  beforeEach(() => { jest.useFakeTimers() })
  afterEach(() => { jest.useRealTimers() })

  it('yields tokens that together contain the stub text', async () => {
    const controller = new AbortController()
    const tokens: string[] = []

    const collecting = (async () => {
      for await (const token of streamMessage('any question', 'test-session', controller.signal)) {
        tokens.push(token)
      }
    })()

    await jest.runAllTimersAsync()
    await collecting

    expect(tokens.length).toBeGreaterThan(0)
    expect(tokens.join('')).toContain('FE-08')
  })

  it('throws AbortError and stops after the signal is aborted', async () => {
    const controller = new AbortController()
    const tokens: string[] = []
    let caughtError: Error | null = null

    const collecting = (async () => {
      try {
        for await (const token of streamMessage('test', 'test-session', controller.signal)) {
          tokens.push(token)
          if (tokens.length === 1) controller.abort()
        }
      } catch (err) {
        caughtError = err as Error
      }
    })()

    await jest.runAllTimersAsync()
    await collecting

    expect(tokens.length).toBe(1)
    expect(caughtError).not.toBeNull()
    expect(caughtError!.name).toBe('AbortError')
  })

  it('throws AbortError immediately if signal is already aborted before first token', async () => {
    const controller = new AbortController()
    controller.abort()
    const tokens: string[] = []
    let caughtError: Error | null = null

    try {
      for await (const token of streamMessage('test', 'test-session', controller.signal)) {
        tokens.push(token)
      }
    } catch (err) {
      caughtError = err as Error
    }

    expect(tokens.length).toBe(0)
    expect(caughtError?.name).toBe('AbortError')
  })
})
