import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SignInCard } from '@/features/auth/components/SignInCard'

describe('SignInCard', () => {
  it('renders the app title', () => {
    render(<SignInCard onSignIn={() => {}} />)
    expect(screen.getByText('List AI Assistant')).toBeInTheDocument()
  })

  it('renders a Sign in with Microsoft button', () => {
    render(<SignInCard onSignIn={() => {}} />)
    expect(screen.getByRole('button', { name: /sign in with microsoft/i })).toBeInTheDocument()
  })

  it('calls onSignIn when the button is clicked', async () => {
    const user = userEvent.setup()
    const onSignIn = jest.fn()
    render(<SignInCard onSignIn={onSignIn} />)
    await user.click(screen.getByRole('button', { name: /sign in with microsoft/i }))
    expect(onSignIn).toHaveBeenCalledTimes(1)
  })
})
