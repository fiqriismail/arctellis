import { ApiError } from '@/features/chat/api/apiError'

describe('ApiError', () => {
  it('is an Error with a kind and message', () => {
    const err = new ApiError('auth', 'Unauthorized')
    expect(err).toBeInstanceOf(Error)
    expect(err.name).toBe('ApiError')
    expect(err.kind).toBe('auth')
    expect(err.message).toBe('Unauthorized')
  })

  it('supports server and network kinds', () => {
    expect(new ApiError('server', 'boom').kind).toBe('server')
    expect(new ApiError('network', 'down').kind).toBe('network')
  })
})
