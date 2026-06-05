import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthGate } from '@/features/auth/components/AuthGate'
import { useIsAuthenticated, useMsal } from '@azure/msal-react'

const mockLoginPopup = jest.fn()
const mockSetActiveAccount = jest.fn()

jest.mock('@azure/msal-react', () => ({
  useIsAuthenticated: jest.fn(),
  useMsal: jest.fn(),
}))

const mockUseIsAuthenticated = useIsAuthenticated as jest.Mock
const mockUseMsal = useMsal as jest.Mock

beforeEach(() => {
  jest.clearAllMocks()
  mockUseMsal.mockReturnValue({
    instance: { loginPopup: mockLoginPopup, setActiveAccount: mockSetActiveAccount },
  })
})

describe('AuthGate', () => {
  it('renders SignInCard when unauthenticated', () => {
    mockUseIsAuthenticated.mockReturnValue(false)
    render(<AuthGate><div>Protected content</div></AuthGate>)
    expect(screen.getByRole('button', { name: /sign in with microsoft/i })).toBeInTheDocument()
    expect(screen.queryByText('Protected content')).not.toBeInTheDocument()
  })

  it('renders children when authenticated', () => {
    mockUseIsAuthenticated.mockReturnValue(true)
    render(<AuthGate><div>Protected content</div></AuthGate>)
    expect(screen.getByText('Protected content')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /sign in with microsoft/i })).not.toBeInTheDocument()
  })

  it('calls loginPopup with the API scope when sign in button is clicked', async () => {
    const user = userEvent.setup()
    mockUseIsAuthenticated.mockReturnValue(false)
    mockLoginPopup.mockResolvedValue(null)
    render(<AuthGate><div>Protected content</div></AuthGate>)
    await user.click(screen.getByRole('button', { name: /sign in with microsoft/i }))
    expect(mockLoginPopup).toHaveBeenCalledWith({
      scopes: [process.env.NEXT_PUBLIC_ENTRA_API_SCOPE],
    })
  })

  it('sets active account after successful login', async () => {
    const user = userEvent.setup()
    const mockAccount = { username: 'user@example.com' }
    mockUseIsAuthenticated.mockReturnValue(false)
    mockLoginPopup.mockResolvedValue({ account: mockAccount })
    render(<AuthGate><div>Protected content</div></AuthGate>)
    await user.click(screen.getByRole('button', { name: /sign in with microsoft/i }))
    expect(mockSetActiveAccount).toHaveBeenCalledWith(mockAccount)
  })
})
