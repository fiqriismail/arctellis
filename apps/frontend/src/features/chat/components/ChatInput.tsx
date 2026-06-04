'use client'

import { useState } from 'react'
import { ArrowUp } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'

interface ChatInputProps {
  onSubmit: (question: string) => void
  disabled?: boolean
}

export function ChatInput({ onSubmit, disabled = false }: ChatInputProps) {
  const [value, setValue] = useState('')

  const handleSubmit = () => {
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSubmit(trimmed)
    setValue('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex items-end gap-2">
      <Textarea
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask a question about your SharePoint list…"
        rows={1}
        disabled={disabled}
        className="flex-1 resize-none overflow-hidden min-h-[44px]"
      />
      <Button
        onClick={handleSubmit}
        disabled={!value.trim() || disabled}
        size="icon"
        aria-label="Send"
      >
        <ArrowUp className="h-4 w-4" />
      </Button>
    </div>
  )
}
