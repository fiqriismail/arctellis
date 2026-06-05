export type ApiErrorKind = 'auth' | 'server' | 'network'

export class ApiError extends Error {
  constructor(
    public readonly kind: ApiErrorKind,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}
