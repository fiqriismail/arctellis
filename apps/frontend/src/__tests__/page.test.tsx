import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import HomePage from '@/app/page'

jest.mock('@/features/chat/api/streamMessage', () => ({
  streamMessage: jest.fn().mockImplementation(async function* () {
    yield 'Streamed response'
  }),
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
})
