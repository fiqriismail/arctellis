import { renderHook } from '@testing-library/react'
import { useToken } from '@/features/auth/hooks/useToken'
import { useMsal } from '@azure/msal-react'

jest.mock('@azure/msal-react', () => ({
  useMsal: jest.fn(),
}))

jest.mock('@azure/msal-browser', () => ({
  InteractionRequiredAuthError: class InteractionRequiredAuthError extends Error {
    constructor(errorCode: string) {
      super(errorCode)
      this.name = 'InteractionRequiredAuthError'
    }
  },
}))

const mockUseMsal = useMsal as jest.Mock

beforeEach(() => {
  jest.clearAllMocks()
})

describe('useToken', () => {
  it('returns the access token from acquireTokenSilent on success', async () => {
    mockUseMsal.mockReturnValue({
      instance: {
        acquireTokenSilent: jest.fn().mockResolvedValue({ accessToken: 'silent-token' }),
        acquireTokenPopup: jest.fn(),
      },
      accounts: [{ username: 'user@example.com' }],
    })

    const { result } = renderHook(() => useToken())
    const token = await result.current.getToken()
    expect(token).toBe('silent-token')
  })

  it('falls back to acquireTokenPopup when silent throws InteractionRequiredAuthError', async () => {
    const { InteractionRequiredAuthError: MockError } = jest.requireMock('@azure/msal-browser')
    mockUseMsal.mockReturnValue({
      instance: {
        acquireTokenSilent: jest.fn().mockRejectedValue(new MockError('interaction_required')),
        acquireTokenPopup: jest.fn().mockResolvedValue({ accessToken: 'popup-token' }),
      },
      accounts: [{ username: 'user@example.com' }],
    })

    const { result } = renderHook(() => useToken())
    const token = await result.current.getToken()
    expect(token).toBe('popup-token')
  })
})
