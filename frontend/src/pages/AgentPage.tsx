import { FormEvent, useState } from 'react'
import { PageHeader } from '../components/layout/PageHeader'

interface ChatMessage {
  id: number
  role: 'assistant' | 'user'
  content: string
}

const suggestedQuestions = [
  '25-26赛季队内射手榜是什么？',
  '干宸浩有什么技术特点？',
  '张谢童甲25-26赛季进了几个球？',
]

export function AgentPage() {
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 1,
      role: 'assistant',
      content:
        '你好，我是 Supersonic FC AI Agent。当前是界面预览，Agent API 将在后续接入。',
    },
  ])

  function sendMessage(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const content = input.trim()

    if (!content) return

    const timestamp = Date.now()
    setMessages((current) => [
      ...current,
      { id: timestamp, role: 'user', content },
      {
        id: timestamp + 1,
        role: 'assistant',
        content: 'Agent API 尚未接入。这条消息仅用于展示完整的聊天交互。',
      },
    ])
    setInput('')
  }

  return (
    <div className="page page-ai">
      <section className="content-wrap">
        <PageHeader
          eyebrow="CLUB INTELLIGENCE"
          title="Supersonic FC AI Agent"
          description="可以询问球队比赛、球员、数据、战术与球队知识。"
          aside={
            <div className="agent-page-identity">
              <span className="agent-page-logo">
                <img src="/supersonic-logo.png" alt="超音速球队队徽" />
              </span>
              <span className="status-pill"><i /> UI Preview</span>
            </div>
          }
        />

        <div className="agent-layout">
          <section className="chat-panel" aria-label="AI Agent 聊天区">
            <div className="chat-toolbar">
              <div>
                <strong>球队助理</strong>
                <span>基于结构化数据与 RAG 知识库</span>
              </div>
              <span className="mock-badge">MOCK MODE</span>
            </div>

            <div className="message-list" aria-live="polite">
              {messages.map((message) => (
                <div key={message.id} className={`message ${message.role}`}>
                  {message.role === 'assistant' ? (
                    <span className="message-role assistant-avatar">
                      <img src="/supersonic-logo.png" alt="超音速 AI Agent" />
                    </span>
                  ) : (
                    <span className="message-role user-avatar">YOU</span>
                  )}
                  <p>{message.content}</p>
                </div>
              ))}
            </div>

            <form className="chat-composer" onSubmit={sendMessage}>
              <label htmlFor="agent-question">向球队 Agent 提问</label>
              <div>
                <input
                  id="agent-question"
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="例如：25-26赛季队内射手榜是什么？"
                />
                <button type="submit">发送</button>
              </div>
              <small>当前不连接 LLM，也不会向外部服务发送内容。</small>
            </form>
          </section>

          <aside className="suggestion-panel">
            <p className="section-kicker">建议问题</p>
            <h2>从球队资料开始</h2>
            <p>选择一个问题放入输入框，体验未来 Agent 的使用方式。</p>
            <div className="suggestion-list">
              {suggestedQuestions.map((question, index) => (
                <button key={question} type="button" onClick={() => setInput(question)}>
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
