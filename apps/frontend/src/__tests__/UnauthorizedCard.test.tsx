import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { UnauthorizedCard } from '@/features/auth/components/UnauthorizedCard'

const mockOnSignOut = jest.fn()
const mockAccount = { name: 'Alice Smith', username: 'alice@example.com' }

beforeEach(() => jest.clearAllMocks())

describe('UnauthorizedCard', () => {
  it('renders the denial message', () => {
    render(<UnauthorizedCard account={mockAccount} onSignOut={mockOnSignOut} />)
    expect(screen.getByText(/you don't have access/i)).toBeInTheDocument()
  })

  it('renders the signed-in user name', () => {
    render(<UnauthorizedCard account={mockAccount} onSignOut={mockOnSignOut} />)
    expect(screen.getByText('Alice Smith')).toBeInTheDocument()
  })

  it('renders the signed-in user email', () => {
    render(<UnauthorizedCard account={mockAccount} onSignOut={mockOnSignOut} />)
    expect(screen.getByText('alice@example.com')).toBeInTheDocument()
  })

  it('renders a sign-out button', () => {
    render(<UnauthorizedCard account={mockAccount} onSignOut={mockOnSignOut} />)
    expect(screen.getByRole('button', { name: /sign out/i })).toBeInTheDocument()
  })

  it('calls onSignOut when sign-out button is clicked', async () => {
    const user = userEvent.setup()
    render(<UnauthorizedCard account={mockAccount} onSignOut={mockOnSignOut} />)
    await user.click(screen.getByRole('button', { name: /sign out/i }))
    expect(mockOnSignOut).toHaveBeenCalledTimes(1)
  })

  it('renders username as fallback when name is absent', () => {
    render(<UnauthorizedCard account={{ username: 'bob@example.com' }} onSignOut={mockOnSignOut} />)
    expect(screen.getByText('bob@example.com')).toBeInTheDocument()
  })
})
