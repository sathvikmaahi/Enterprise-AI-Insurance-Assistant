import { useEffect, useRef, useState } from 'react'
import { ApiError, ask } from '../api'
import SuggestedPrompts from './SuggestedPrompts'
import './Chat.css'

function nextId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`
}

function formatAskError(err) {
  if (!(err instanceof ApiError)) {
    return 'Something went wrong'
  }
  if (err.status === 400) {
    return err.reason
      ? `Blocked by guardrail — ${err.reason}`
      : 'Blocked by guardrail'
  }
  if (err.status === 403) {
    return 'Access denied for this role'
  }
  if (err.status === 503) {
    return err.reason
      ? `Unable to answer — ${err.reason}`
      : 'Unable to answer'
  }
  return err.message
}

export default function Chat({ session, onUnauthorized, onAskSettled }) {
  const [messages, setMessages] = useState([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy])

  async function sendQuestion(text) {
    const question = text.trim()
    if (!question || busy) return

    setDraft('')
    setMessages((prev) => [
      ...prev,
      { id: nextId(), role: 'user', text: question },
    ])
    setBusy(true)

    try {
      const result = await ask(question, session.access_token)
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: 'assistant',
          text: result.answer,
          path: result.path,
          tools_used: result.tools_used || [],
          fallback_reason: result.fallback_reason,
        },
      ])
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        onUnauthorized()
        return
      }
      setMessages((prev) => [
        ...prev,
        { id: nextId(), role: 'error', text: formatAskError(err) },
      ])
    } finally {
      setBusy(false)
      onAskSettled()
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    sendQuestion(draft)
  }

  return (
    <section className="chat" aria-label="Conversation">
      <div className="chat__thread">
        {messages.length === 0 ? (
          <p className="chat__empty">
            Ask a business question. The agent picks a semantic concept and SQL stays in the layer.
          </p>
        ) : null}
        {messages.map((msg) => (
          <article
            key={msg.id}
            className={`bubble bubble--${msg.role}`}
          >
            <p className="bubble__text">{msg.text}</p>
            {msg.role === 'assistant' ? (
              <p className="bubble__meta">
                <span className={`path-chip path-chip--${msg.path}`}>
                  path: {msg.path}
                </span>
                {msg.tools_used?.length ? (
                  <span>tools: {msg.tools_used.join(', ')}</span>
                ) : null}
                {msg.fallback_reason ? (
                  <span className="bubble__fallback">
                    fallback: {msg.fallback_reason}
                  </span>
                ) : null}
              </p>
            ) : null}
          </article>
        ))}
        {busy ? (
          <p className="chat__thinking" aria-live="polite">
            Working…
          </p>
        ) : null}
        <div ref={bottomRef} />
      </div>

      <SuggestedPrompts disabled={busy} onSelect={sendQuestion} />

      <form className="chat__composer" onSubmit={handleSubmit}>
        <label className="visually-hidden" htmlFor="question">
          Question
        </label>
        <input
          id="question"
          name="question"
          value={draft}
          disabled={busy}
          placeholder="Ask about policies, coverages, or claims…"
          onChange={(e) => setDraft(e.target.value)}
        />
        <button type="submit" disabled={busy || !draft.trim()}>
          Ask
        </button>
      </form>
    </section>
  )
}
