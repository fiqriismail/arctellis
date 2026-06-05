import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import HomePage from '@/app/page'

jest.mock('@/features/chat/api/streamMessage', () => ({
  streamMessage: jest.fn().mockImplementation(async function* () {
    yield 'Streamed response'
  }),
}))

jest.mock('@azure/msal-react', () => ({
  useIsAuthenticated: jest.fn().mockReturnValue(true),
  useMsal: jest.fn().mockReturnValue({ instance: { loginPopup: jest.fn() } }),
}))

describe('HomePage', () => {
  it('shows empty state by default', () => {
    render(<HomePage />)
    expect(screen.getByText('SharePoint List AI Assistant')).toBeInTheDocument()
  })

  it('hides empty state and shows user message after submit', async () => {
    const user = userEvent.setup()
    render(<HomePage />)
    const textarea = screen.getByPlaceholderText(/ask a question/i)
    await user.type(textarea, 'Test question')
    await user.keyboard('{Enter}')
    expect(screen.queryByText('SharePoint List AI Assistant')).not.toBeInTheDocument()
    expect(screen.getByText('Test question')).toBeInTheDocument()
    // drain async streaming so React act() queue is empty before test exits
    await waitFor(() => expect(screen.getByText('Streamed response')).toBeInTheDocument())
  })

  it('shows assistant response after submit', async () => {
    const user = userEvent.setup()
    render(<HomePage />)
    await user.type(screen.getByPlaceholderText(/ask a question/i), 'Hello')
    await user.keyboard('{Enter}')
    await waitFor(() => expect(screen.getByText('Streamed response')).toBeInTheDocument())
  })

  it('clicking a suggestion card submits it as a user message and shows response', async () => {
    const user = userEvent.setup()
    render(<HomePage />)
    await user.click(screen.getByText('Show overdue tasks'))
    expect(screen.getByText('Show overdue tasks')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Streamed response')).toBeInTheDocument())
  })

  it('shows new conversation button after a message is sent and clicking it returns to empty state', async () => {
    const user = userEvent.setup()
    render(<HomePage />)

    // Send a message to enter conversation view
    await user.type(screen.getByPlaceholderText(/ask a question/i), 'Hello')
    await user.keyboard('{Enter}')
    await waitFor(() => expect(screen.getByText('Streamed response')).toBeInTheDocument())

    // New conversation button should now be visible
    const newConvButton = screen.getByRole('button', { name: /new conversation/i })
    expect(newConvButton).toBeInTheDocument()

    // Click it — thread clears, landing heading returns
    await user.click(newConvButton)
    expect(screen.getByText('SharePoint List AI Assistant')).toBeInTheDocument()
    expect(screen.queryByText('Hello')).not.toBeInTheDocument()
  })
})
