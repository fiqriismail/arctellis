describe('getApiUrl', () => {
  const original = process.env.NEXT_PUBLIC_API_URL

  afterEach(() => {
    process.env.NEXT_PUBLIC_API_URL = original
    jest.resetModules()
  })

  it('returns NEXT_PUBLIC_API_URL when set', async () => {
    process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com'
    jest.resetModules()
    const { getApiUrl } = await import('@/features/chat/config')
    expect(getApiUrl()).toBe('https://api.example.com')
  })

  it('defaults to http://localhost:8000 when unset', async () => {
    delete process.env.NEXT_PUBLIC_API_URL
    jest.resetModules()
    const { getApiUrl } = await import('@/features/chat/config')
    expect(getApiUrl()).toBe('http://localhost:8000')
  })
})
