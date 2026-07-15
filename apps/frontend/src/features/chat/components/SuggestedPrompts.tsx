'use client'

import { Button } from '@/components/ui/button'
import { SUGGESTED_PROMPTS } from '../lib/suggestedPrompts'

interface SuggestedPromptsProps {
  onSelect: (prompt: string) => void
}

/** Clickable starter prompts shown on the empty-state welcome screen. */
export function SuggestedPrompts({ onSelect }: SuggestedPromptsProps) {
  return (
    <div className="mt-5 flex flex-wrap justify-center gap-2">
      {SUGGESTED_PROMPTS.map((prompt) => (
        <Button
          key={prompt}
          type="button"
          variant="outline"
          size="sm"
          className="h-auto max-w-full rounded-full text-left text-xs font-normal whitespace-normal text-muted-foreground"
          onClick={() => onSelect(prompt)}
        >
          {prompt}
        </Button>
      ))}
    </div>
  )
}
