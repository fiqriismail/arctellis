import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AuthGate } from '@/features/auth/components/AuthGate'
import { useIsAuthenticated, useMsal } from '@azure/msal-react'
import { useGroupAccess } from '@/features/auth/hooks/useGroupAccess'

const mockLoginPopup = jest.fn()
const mockSetActiveAccount = jest.fn()

jest.mock('@azure/msal-react', () => ({
  useIsAuthenticated: jest.fn(),
  useMsal: jest.fn(),
}))

jest.mock('@/features/auth/hooks/useGroupAccess')

const mockUseIsAuthenticated = useIsAuthenticated as jest.Mock
const mockUseMsal = useMsal as jest.Mock
const mockUseGroupAccess = useGroupAccess as jest.Mock

beforeEach(() => {
  jest.clearAllMocks()
  mockUseMsal.mockReturnValue({
    instance: { loginPopup: mockLoginPopup, setActiveAccount: mockSetActiveAccount, logoutPopup: jest.fn() },
    accounts: [],
  })
  mockUseGroupAccess.mockReturnValue({ status: 'authorized' })
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
      redirectUri: expect.stringContaining('/auth-redirect'),
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

  it('renders a loading spinner while access check is in flight', () => {
    mockUseIsAuthenticated.mockReturnValue(true)
    mockUseGroupAccess.mockReturnValue({ status: 'loading' })
    mockUseMsal.mockReturnValue({
      instance: { loginPopup: mockLoginPopup, setActiveAccount: mockSetActiveAccount, logoutPopup: jest.fn() },
      accounts: [{ name: 'Alice', username: 'alice@example.com' }],
    })
    render(<AuthGate><div>Chat</div></AuthGate>)
    expect(screen.getByText(/checking access/i)).toBeInTheDocument()
    expect(screen.queryByText('Chat')).not.toBeInTheDocument()
  })

  it('renders children when access is authorized', () => {
    mockUseIsAuthenticated.mockReturnValue(true)
    mockUseGroupAccess.mockReturnValue({ status: 'authorized' })
    mockUseMsal.mockReturnValue({
      instance: { loginPopup: mockLoginPopup, setActiveAccount: mockSetActiveAccount, logoutPopup: jest.fn() },
      accounts: [{ name: 'Alice', username: 'alice@example.com' }],
    })
    render(<AuthGate><div>Chat</div></AuthGate>)
    expect(screen.getByText('Chat')).toBeInTheDocument()
  })

  it('renders UnauthorizedCard when access is denied', () => {
    mockUseIsAuthenticated.mockReturnValue(true)
    mockUseGroupAccess.mockReturnValue({ status: 'unauthorized' })
    mockUseMsal.mockReturnValue({
      instance: { loginPopup: mockLoginPopup, setActiveAccount: mockSetActiveAccount, logoutPopup: jest.fn() },
      accounts: [{ name: 'Alice', username: 'alice@example.com' }],
    })
    render(<AuthGate><div>Chat</div></AuthGate>)
    expect(screen.getByText(/you don't have access/i)).toBeInTheDocument()
    expect(screen.queryByText('Chat')).not.toBeInTheDocument()
  })
})
