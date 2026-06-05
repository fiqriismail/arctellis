import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import HomePage from '@/app/page'

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

  it('shows stub assistant response after submit', async () => {
    const user = userEvent.setup()
    render(<HomePage />)
    await user.type(screen.getByPlaceholderText(/ask a question/i), 'Hello')
    await user.keyboard('{Enter}')
    expect(screen.getByText(/Connected to the backend in FE-08/)).toBeInTheDocument()
  })

  it('clicking a suggestion card submits it as a user message', async () => {
    const user = userEvent.setup()
    render(<HomePage />)
    await user.click(screen.getByText('Show overdue tasks'))
    expect(screen.getByText('Show overdue tasks')).toBeInTheDocument()
    expect(screen.getByText(/Connected to the backend in FE-08/)).toBeInTheDocument()
  })
})
