import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SuggestedPrompts } from '@/features/chat/components/SuggestedPrompts'
import { SUGGESTED_PROMPTS } from '@/features/chat/lib/suggestedPrompts'

describe('SuggestedPrompts', () => {
  it('renders a button for every predefined prompt', () => {
    render(<SuggestedPrompts onSelect={jest.fn()} />)
    for (const prompt of SUGGESTED_PROMPTS) {
      expect(screen.getByRole('button', { name: prompt })).toBeInTheDocument()
    }
  })

  it('calls onSelect with the exact prompt text when clicked', async () => {
    const user = userEvent.setup()
    const onSelect = jest.fn()
    render(<SuggestedPrompts onSelect={onSelect} />)

    await user.click(screen.getByRole('button', { name: SUGGESTED_PROMPTS[2] }))

    expect(onSelect).toHaveBeenCalledWith(SUGGESTED_PROMPTS[2])
    expect(onSelect).toHaveBeenCalledTimes(1)
  })
})
