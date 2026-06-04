'use client'

import { ChatInput } from '@/features/chat/components/ChatInput'

export default function HomePage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <div className="w-full max-w-2xl space-y-6">
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-semibold tracking-tight">
            SharePoint List AI Assistant
          </h1>
          <p className="text-sm text-muted-foreground">
            Ask a question about your list in plain English.
          </p>
        </div>

        <ChatInput onSubmit={() => {}} />

        <p className="text-center text-xs text-muted-foreground">
          Press <kbd className="rounded border px-1 py-0.5 text-xs font-mono">Enter</kbd> to
          send · <kbd className="rounded border px-1 py-0.5 text-xs font-mono">Shift+Enter</kbd>{' '}
          for new line
        </p>
      </div>
    </div>
  )
}
