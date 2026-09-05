import { FormEvent, useEffect, useRef, useState } from 'react'
import { PageHeader } from '../components/layout/PageHeader'
import { agentData } from '../services/agentData'

interface ChatMessage {
  id: string
  role: 'assistant' | 'user'
  content: string
  error?: boolean
}

const safeErrorMessage = 'AI 助手暂时无法完成请求，请稍后重试。'

const suggestedQuestions = [
  '25-26赛季队内射手榜是什么？',
  '干宸浩有什么技术特点？',
  '张谢童甲25-26赛季进了几个球？',
]

export function AgentPage() {
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [sessionId, setSessionId] = useState<string>()
  const messageListRef = useRef<HTMLDivElement>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content:
        '你好，我是 Supersonic FC AI Assistant。你可以询问球队比赛、球员数据与球队知识。',
    },
  ])

  useEffect(() => {
    const list = messageListRef.current
    if (list) list.scrollTop = list.scrollHeight
  }, [messages, sending])

  async function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const content = input.trim()

    if (!content || sending) return

    const requestId = crypto.randomUUID()
    setMessages((current) => [
      ...current,
      { id: `user-${requestId}`, role: 'user', content },
    ])
    setInput('')
    setSending(true)

    try {
      const response = await agentData.chat(content, sessionId)
      setSessionId(response.sessionId)
      setMessages((current) => [
        ...current,
        {
          id: `assistant-${requestId}`,
          role: 'assistant',
          content: response.answer,
        },
      ])
    } catch {
      setMessages((current) => [
        ...current,
        {
          id: `error-${requestId}`,
          role: 'assistant',
          content: safeErrorMessage,
          error: true,
        },
      ])
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="page page-ai">
      <section className="content-wrap">
        <PageHeader
          eyebrow="CLUB INTELLIGENCE"
          title="Supersonic FC AI Assistant"
          description="可以询问球队比赛、球员、数据、战术与球队知识。"
          aside={
            <div className="agent-page-identity">
              <span className="agent-page-logo">
                <img src="/supersonic-logo.png" alt="超音速球队队徽" />
              </span>
              <span className="status-pill"><i /> LANGGRAPH</span>
            </div>
          }
        />

        <div className="agent-layout">
          <section className="chat-panel" aria-label="AI Assistant 聊天区">
            <div className="chat-toolbar">
              <div>
                <strong>球队助理</strong>
                <span>基于结构化数据与 RAG 知识库</span>
              </div>
              <span className="live-badge">AI ASSISTANT</span>
            </div>

            <div
              className="message-list"
              aria-live="polite"
              aria-busy={sending}
              ref={messageListRef}
            >
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`message ${message.role}${message.error ? ' error' : ''}`}
                >
                  {message.role === 'assistant' ? (
                    <span className="message-role assistant-avatar">
                      <img src="/supersonic-logo.png" alt="超音速 AI Assistant" />
                    </span>
                  ) : (
                    <span className="message-role user-avatar">YOU</span>
                  )}
                  <p>{message.content}</p>
                </div>
              ))}
              {sending && (
                <div className="message assistant loading-message">
                  <span className="message-role assistant-avatar">
                    <img src="/supersonic-logo.png" alt="超音速 AI Assistant" />
                  </span>
                  <p>正在查询球队资料…</p>
                </div>
              )}
            </div>

            <form className="chat-composer" onSubmit={sendMessage}>
              <label htmlFor="agent-question">向球队 AI Assistant 提问</label>
              <div>
                <input
                  id="agent-question"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="例如：25-26赛季队内射手榜是什么？"
                  disabled={sending}
                />
                <button type="submit" disabled={sending || !input.trim()}>
                  {sending ? '处理中…' : '发送'}
                </button>
              </div>
              <small>回答由现有 LangGraph Agent、结构化工具与球队知识库生成。</small>
            </form>
          </section>

          <aside className="suggestion-panel">
            <p className="section-kicker">建议问题</p>
            <h2>从球队资料开始</h2>
            <p>选择一个问题放入输入框，体验 AI Assistant。</p>
            <div className="suggestion-list">
              {suggestedQuestions.map((question, index) => (
                <button
                  key={question}
                  type="button"
                  disabled={sending}
                  onClick={() => setInput(question)}
                >
                  <span>0{index + 1}</span>
                  {question}
                </button>
              ))}
            </div>
          </aside>
        </div>
      </section>
    </div>
  )
}
