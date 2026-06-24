import { checkAccess } from '@/features/auth/api/checkAccess'

const mockGetToken = jest.fn().mockResolvedValue('mock-token')

beforeEach(() => {
  jest.clearAllMocks()
  global.fetch = jest.fn()
})

describe('checkAccess', () => {
  it('returns true when backend responds 200', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({ ok: true, status: 200 })
    const result = await checkAccess(mockGetToken)
    expect(result).toBe(true)
  })

  it('returns false when backend responds 403', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({ ok: false, status: 403 })
    const result = await checkAccess(mockGetToken)
    expect(result).toBe(false)
  })

  it('throws on unexpected status codes', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({ ok: false, status: 500 })
    await expect(checkAccess(mockGetToken)).rejects.toThrow()
  })

  it('calls the /access endpoint with Bearer token', async () => {
    ;(global.fetch as jest.Mock).mockResolvedValue({ ok: true, status: 200 })
    await checkAccess(mockGetToken)
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/access'),
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: 'Bearer mock-token' }),
      })
    )
  })
})
