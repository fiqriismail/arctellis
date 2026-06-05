export type UserMessage = { role: 'user'; text: string }
export type AssistantMessage = { role: 'assistant'; text: string }
export type Message = UserMessage | AssistantMessage
