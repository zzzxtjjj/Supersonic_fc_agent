import { apiRequest } from './api'

interface AgentChatResponse {
  answer: string
  session_id: string
  sources: Array<{
    id: string
    title: string
    source_type: string | null
  }>
}

export const agentData = {
  async chat(
    message: string,
    sessionId?: string,
    signal?: AbortSignal,
  ): Promise<{ answer: string; sessionId: string }> {
    const response = await apiRequest<AgentChatResponse>('/agent/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        session_id: sessionId ?? null,
      }),
      signal,
    })

    return {
      answer: response.answer,
      sessionId: response.session_id,
    }
  },
}
