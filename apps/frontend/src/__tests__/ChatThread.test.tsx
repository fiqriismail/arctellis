import { render, screen } from '@testing-library/react'
import { ChatThread } from '@/features/chat/components/ChatThread'

describe('ChatThread', () => {
  it('renders a user message', () => {
    render(<ChatThread messages={[{ role: 'user', text: 'Hello' }]} />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders an assistant message', () => {
    render(<ChatThread messages={[{ role: 'assistant', text: 'World' }]} />)
    expect(screen.getByText('World')).toBeInTheDocument()
  })

  it('renders messages in order', () => {
    render(<ChatThread messages={[
      { role: 'user', text: 'First' },
      { role: 'assistant', text: 'Second' },
    ]} />)
    const items = screen.getAllByTestId('message')
    expect(items[0]).toHaveTextContent('First')
    expect(items[1]).toHaveTextContent('Second')
  })

  it('renders empty thread without error', () => {
    render(<ChatThread messages={[]} />)
    expect(screen.queryByTestId('message')).not.toBeInTheDocument()
  })

  it('calls scrollIntoView when messages change', () => {
    const scrollSpy = jest.spyOn(window.HTMLElement.prototype, 'scrollIntoView')
    const { rerender } = render(<ChatThread messages={[{ role: 'user', text: 'Hello' }]} />)
    expect(scrollSpy).toHaveBeenCalled()

    scrollSpy.mockClear()
    rerender(<ChatThread messages={[
      { role: 'user', text: 'Hello' },
      { role: 'assistant', text: 'World' },
    ]} />)
    expect(scrollSpy).toHaveBeenCalled()
    scrollSpy.mockRestore()
  })
})
