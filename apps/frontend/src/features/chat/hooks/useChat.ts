'use client'

import { useState, useRef, useCallback } from 'react'
import { streamMessage } from '@/features/chat/api/streamMessage'
import type { Message } from '@/features/chat/types'
import { useToken } from '@/features/auth/hooks/useToken'
import { ApiError } from '@/features/chat/api/apiError'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [streamingText, setStreamingText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamError, setStreamError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const sessionIdRef = useRef(crypto.randomUUID())
  const { getToken } = useToken()
  const getTokenRef = useRef(getToken)
  getTokenRef.current = getToken

  const sendMessage = useCallback(async (text: string) => {
    if (abortRef.current) return

    setMessages(prev => [...prev, { role: 'user', text }])
    setIsStreaming(true)
    setStreamError(null)
    setStreamingText('')

    const controller = new AbortController()
    abortRef.current = controller

    let accumulated = ''

    try {
      for await (const token of streamMessage(text, sessionIdRef.current, controller.signal, getTokenRef.current)) {
        accumulated += token
        setStreamingText(accumulated)
      }
      if (accumulated) {
        setMessages(prev => [...prev, { role: 'assistant', text: accumulated }])
      }
    } catch (err) {
      if (accumulated) {
        setMessages(prev => [...prev, { role: 'assistant', text: accumulated }])
      }
      if (!(err instanceof DOMException && err.name === 'AbortError')) {
        setStreamError(
          err instanceof ApiError && err.kind === 'auth'
            ? 'Session expired — please sign in again'
            : 'Something went wrong — please try again'
        )
      }
    } finally {
      setStreamingText('')
      setIsStreaming(false)
      abortRef.current = null
    }
  }, [])

  const stopStream = useCallback(() => {
    abortRef.current?.abort()
  }, [])

  const resetSession = useCallback(() => {
    abortRef.current?.abort()
    sessionIdRef.current = crypto.randomUUID()
    setMessages([])
    setStreamingText('')
    setStreamError(null)
    setIsStreaming(false)
  }, [])

  return { messages, streamingText, isStreaming, streamError, sendMessage, stopStream, resetSession }
}
