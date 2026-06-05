import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatHeader } from '@/features/chat/components/ChatHeader'

describe('ChatHeader', () => {
  it('does not render a new conversation button when onNewConversation is not provided', () => {
    render(<ChatHeader />)
    expect(screen.queryByRole('button', { name: /new conversation/i })).not.toBeInTheDocument()
  })

  it('renders a new conversation button when onNewConversation is provided', () => {
    render(<ChatHeader onNewConversation={() => {}} />)
    expect(screen.getByRole('button', { name: /new conversation/i })).toBeInTheDocument()
  })

  it('calls onNewConversation when the button is clicked', async () => {
    const user = userEvent.setup()
    const onNewConversation = jest.fn()
    render(<ChatHeader onNewConversation={onNewConversation} />)
    await user.click(screen.getByRole('button', { name: /new conversation/i }))
    expect(onNewConversation).toHaveBeenCalledTimes(1)
  })
})
