import { renderHook, waitFor } from '@testing-library/react'
import { useGroupAccess } from '@/features/auth/hooks/useGroupAccess'
import { useToken } from '@/features/auth/hooks/useToken'
import { checkAccess } from '@/features/auth/api/checkAccess'

jest.mock('@/features/auth/hooks/useToken')
jest.mock('@/features/auth/api/checkAccess')

const mockGetToken = jest.fn().mockResolvedValue('tok')
const mockUseToken = useToken as jest.Mock
const mockCheckAccess = checkAccess as jest.Mock

beforeEach(() => {
  jest.clearAllMocks()
  mockUseToken.mockReturnValue({ getToken: mockGetToken })
})

describe('useGroupAccess', () => {
  it('starts in loading state', () => {
    mockCheckAccess.mockReturnValue(new Promise(() => {})) // never resolves
    const { result } = renderHook(() => useGroupAccess(true))
    expect(result.current.status).toBe('loading')
  })

  it('resolves to authorized when checkAccess returns true', async () => {
    mockCheckAccess.mockResolvedValue(true)
    const { result } = renderHook(() => useGroupAccess(true))
    await waitFor(() => expect(result.current.status).toBe('authorized'))
  })

  it('resolves to unauthorized when checkAccess returns false', async () => {
    mockCheckAccess.mockResolvedValue(false)
    const { result } = renderHook(() => useGroupAccess(true))
    await waitFor(() => expect(result.current.status).toBe('unauthorized'))
  })

  it('retries once on transient error and resolves if retry succeeds', async () => {
    mockCheckAccess
      .mockRejectedValueOnce(new Error('503'))
      .mockResolvedValue(true)
    const { result } = renderHook(() => useGroupAccess(true))
    await waitFor(() => expect(result.current.status).toBe('authorized'))
    expect(mockCheckAccess).toHaveBeenCalledTimes(2)
  })

  it('resolves to unauthorized after two consecutive errors', async () => {
    mockCheckAccess.mockRejectedValue(new Error('503'))
    const { result } = renderHook(() => useGroupAccess(true))
    await waitFor(() => expect(result.current.status).toBe('unauthorized'))
    expect(mockCheckAccess).toHaveBeenCalledTimes(2)
  })
})
