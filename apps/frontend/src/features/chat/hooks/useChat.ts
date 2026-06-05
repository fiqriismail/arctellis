'use client'

import { useState, useRef, useCallback } from 'react'
import { streamMessage } from '@/features/chat/api/streamMessage'
import type { Message } from '@/features/chat/types'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [streamingText, setStreamingText] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamError, setStreamError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  const sessionIdRef = useRef(crypto.randomUUID())

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
      for await (const token of streamMessage(text, sessionIdRef.current, controller.signal)) {
        accumulated += token
        setStreamingText(accumulated)
      }
      if (accumulated) {
        setMessages(prev => [...prev, { role: 'assistant', text: accumulated }])
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        if (accumulated) {
          setMessages(prev => [...prev, { role: 'assistant', text: accumulated }])
        }
      } else {
        if (accumulated) {
          setMessages(prev => [...prev, { role: 'assistant', text: accumulated }])
        }
        setStreamError('Something went wrong — please try again')
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
    sessionIdRef.current = crypto.randomUUID()
    setMessages([])
    setStreamingText('')
    setStreamError(null)
    setIsStreaming(false)
  }, [])

  return { messages, streamingText, isStreaming, streamError, sendMessage, stopStream, resetSession }
}
