import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { ChatInput } from '@/features/chat/components/ChatInput'

describe('ChatInput', () => {
  it('shows the stop button when isStreaming is true', () => {
    render(<ChatInput onSubmit={jest.fn()} onStop={jest.fn()} isStreaming={true} />)
    expect(screen.getByRole('button', { name: /stop/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /send/i })).not.toBeInTheDocument()
  })

  it('shows the send button when isStreaming is false', () => {
    render(<ChatInput onSubmit={jest.fn()} isStreaming={false} />)
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /stop/i })).not.toBeInTheDocument()
  })

  it('stop button is not disabled when isStreaming is true', () => {
    render(<ChatInput onSubmit={jest.fn()} onStop={jest.fn()} isStreaming={true} />)
    expect(screen.getByRole('button', { name: /stop/i })).not.toBeDisabled()
  })

  it('calls onStop when stop button is clicked', async () => {
    const onStop = jest.fn()
    const user = userEvent.setup()
    render(<ChatInput onSubmit={jest.fn()} onStop={onStop} isStreaming={true} />)
    await user.click(screen.getByRole('button', { name: /stop/i }))
    expect(onStop).toHaveBeenCalledTimes(1)
  })

  it('does not call onSubmit when Enter is pressed while isStreaming is true', async () => {
    const onSubmit = jest.fn()
    const user = userEvent.setup()
    render(<ChatInput onSubmit={onSubmit} isStreaming={true} />)
    await user.type(screen.getByRole('textbox'), 'hello{Enter}')
    expect(onSubmit).not.toHaveBeenCalled()
  })
})
