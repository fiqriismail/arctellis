'use client'

import { ChatHeader } from '@/features/chat/components/ChatHeader'
import { AppIcon } from '@/components/AppIcon'
import { ChatInput } from '@/features/chat/components/ChatInput'
import { ChatThread } from '@/features/chat/components/ChatThread'
import { useChat } from '@/features/chat/hooks/useChat'
import { AuthGate } from '@/features/auth/components/AuthGate'

export default function HomePage() {
  const { messages, streamingText, isStreaming, streamError, sendMessage, stopStream, resetSession } = useChat()

  return (
    <AuthGate>
      {messages.length > 0 ? (
        <div style={{ height: '100dvh', display: 'flex', flexDirection: 'column', background: 'var(--background)', overflow: 'hidden' }}>
          <ChatHeader onNewConversation={resetSession} />
          <div style={{ flex: 1, overflowY: 'auto', minHeight: 0 }} className="scroll">
            <ChatThread
              messages={messages}
              streamingText={streamingText}
              isStreaming={isStreaming}
              streamError={streamError}
            />
          </div>
          <div style={{
            flexShrink: 0,
            borderTop: '1px solid var(--border)',
            background: 'rgba(255,255,255,.9)',
            backdropFilter: 'blur(8px)',
            WebkitBackdropFilter: 'blur(8px)',
          }}>
            <div className="mx-auto w-full max-w-[860px] px-4 pt-3.5 pb-4 md:px-6 lg:max-w-[1280px] xl:max-w-[1536px]">
              <ChatInput onSubmit={sendMessage} onStop={stopStream} isStreaming={isStreaming} compact />
            </div>
          </div>
        </div>
      ) : (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--background)' }}>
          <ChatHeader />
          <div style={{
            flex: 1, overflowY: 'auto',
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            padding: '40px 24px',
          }}>
            <div style={{ width: '100%', maxWidth: 680 }}>
              <div style={{ textAlign: 'center', marginBottom: 26 }}>
                <div style={{
                  margin: '0 auto 18px',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                }}>
                  <AppIcon size={52} priority />
                </div>
                <h1 style={{ fontSize: 30, fontWeight: 680, letterSpacing: '-.025em', margin: '0 0 8px' }}>
                  RTP Intelligence Hub
                </h1>
                <p style={{ fontSize: 15.5, color: 'var(--muted-foreground)', margin: 0, lineHeight: 1.5 }}>
                  Ask anything about your{' '}
                  <span style={{ fontWeight: 550, color: 'var(--foreground)' }}>purchase requests</span>
                  {' '}in plain English — no formulas, no filters.
                </p>
              </div>

              <ChatInput onSubmit={sendMessage} onStop={stopStream} isStreaming={isStreaming} />
            </div>
          </div>
        </div>
      )}
    </AuthGate>
  )
}
