function delay(ms: number, signal: AbortSignal): Promise<void> {
  return new Promise((resolve, reject) => {
    if (signal.aborted) {
      reject(new DOMException('Aborted', 'AbortError'))
      return
    }
    const id = setTimeout(resolve, ms)
    signal.addEventListener(
      'abort',
      () => { clearTimeout(id); reject(new DOMException('Aborted', 'AbortError')) },
      { once: true }
    )
  })
}

export async function* streamMessage(
  _text: string, // FE-08 will POST this to the backend SSE endpoint
  _sessionId: string, // stub ignores; FE-08 will POST with it
  signal: AbortSignal
): AsyncGenerator<string> {
  const tokens = 'This is a stub response — real answers arrive in FE-08.'.split(' ')
  for (const token of tokens) {
    await delay(80, signal)
    yield token + ' ' // stub adds trailing space; real SSE tokens won't
  }
}
