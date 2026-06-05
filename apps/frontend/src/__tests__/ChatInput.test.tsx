import { render, screen } from '@testing-library/react'
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
})
