'use client'

import { Hash, ListFilter, Table2, Calculator, TrendingUp, type LucideIcon } from 'lucide-react'
import { SUGGESTED_PROMPTS } from '../lib/suggestedPrompts'

interface SuggestedPromptsProps {
  onSelect: (prompt: string) => void
}

const ICONS: LucideIcon[] = [Hash, ListFilter, Table2, Calculator, TrendingUp]

/** Clickable starter prompts shown as small cards on the empty-state welcome screen. */
export function SuggestedPrompts({ onSelect }: SuggestedPromptsProps) {
  return (
    <div className="mt-6 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
      {SUGGESTED_PROMPTS.map((prompt, i) => {
        const Icon = ICONS[i % ICONS.length]
        return (
          <button
            key={prompt}
            type="button"
            onClick={() => onSelect(prompt)}
            className="flex items-start gap-2.5 rounded-xl border border-border bg-card p-3.5 text-left text-[13px] leading-snug text-muted-foreground shadow-sm transition-colors hover:border-primary/30 hover:bg-muted/50 hover:text-foreground"
          >
            <Icon className="mt-0.5 size-4 shrink-0 text-primary" aria-hidden="true" />
            <span>{prompt}</span>
          </button>
        )
      })}
    </div>
  )
}
