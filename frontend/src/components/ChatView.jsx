import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { sendChatMessage } from '../services/api.js'
import 'katex/dist/katex.min.css'

const MathMarkdown = lazy(() => import('./MathMarkdown.jsx'))

function friendlyError(error) {
  if (!error.status) return error.message || 'No pudimos conectar con el tutor. Revisa que el backend esté activo.'
  if (error.status === 429) return 'El tutor está recibiendo muchas solicitudes o alcanzó su cuota temporal. Espera un momento e inténtalo de nuevo.'
  if (error.status >= 500) return 'El tutor no está disponible mientras el servidor inicia o se recupera. Vuelve a intentarlo en unos segundos.'
  return error.message || 'No se pudo enviar tu pregunta. Inténtalo de nuevo.'
}

export default function ChatView({ course, onBack }) {
  const [messages, setMessages] = useState(() => [{
    role: 'assistant',
    content: `¡Hola! Soy tu tutor de **${course.title}**. Pregúntame sobre el material del curso y lo revisamos paso a paso.`,
    sources: [],
    isWelcome: true,
  }])
  const [draft, setDraft] = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, sending, error])

  async function submitMessage(event) {
    event?.preventDefault()
    const message = draft.trim()
    if (!message || sending) return

    const priorMessages = messages.filter((item) => !item.isWelcome).slice(-8)
    setMessages((current) => [...current, { role: 'user', content: message }])
    setDraft('')
    setError('')
    setSending(true)

    try {
      const result = await sendChatMessage({
        course_id: course.id,
        message,
        history: priorMessages.map(({ role, content }) => ({ role, content })),
      })
      const answer = typeof result?.answer === 'string' ? result.answer.trim() : ''
      setMessages((current) => [...current, {
        role: 'assistant',
        content: answer || 'No recibí una respuesta completa esta vez. Puedes volver a enviar la pregunta.',
        sources: Array.isArray(result?.sources) ? result.sources : [],
      }])
    } catch (requestError) {
      setMessages((current) => current.at(-1)?.role === 'user' ? current.slice(0, -1) : current)
      setDraft(message)
      setError(friendlyError(requestError))
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  function onComposerKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      submitMessage()
    }
  }

  return (
    <section className="chat-page" aria-label={`Tutoría de ${course.title}`}>
      <header className="chat-course-header">
        <button className="back-link" onClick={onBack} type="button"><span aria-hidden="true">←</span> Cursos</button>
        <div className="chat-course-copy">
          <span className="chat-course-subject">{course.subject || 'MATEMÁTICAS'} · {course.grade_level || 'Todos los niveles'}</span>
          <h1>{course.title}</h1>
        </div>
      </header>

      <div className="chat-transcript" aria-live="polite" aria-relevant="additions text">
        <div className="chat-intro-note">Tus respuestas se apoyan en los documentos disponibles de este curso.</div>
        {messages.map((item, index) => (
          <article className={`chat-message is-${item.role}`} key={`${item.role}-${index}`}>
            <div className="chat-avatar" aria-hidden="true">{item.role === 'assistant' ? '✦' : 'Tú'}</div>
            <div className="chat-message-body">
              <span className="chat-speaker">{item.role === 'assistant' ? 'Tutor' : 'Tú'}</span>
              <div className="chat-bubble"><Suspense fallback={<span>{item.content}</span>}><MathMarkdown>{item.content}</MathMarkdown></Suspense></div>
              {item.sources?.length > 0 && (
                <div className="chat-sources">
                  <span>Fuentes del curso</span>
                  <ul>{[...new Set(item.sources.map((source) => source.document_title))].map((title) => <li key={title}>{title}</li>)}</ul>
                </div>
              )}
            </div>
          </article>
        ))}
        {sending && <div className="chat-pending" role="status"><span className="typing-dots" aria-hidden="true">•••</span> El tutor está preparando una respuesta…</div>}
        {error && <div className="chat-error" role="alert"><span>{error}</span><button className="text-button" type="button" onClick={() => submitMessage()}>Reintentar pregunta</button></div>}
        <div ref={endRef} />
      </div>

      <form className="chat-composer" onSubmit={submitMessage}>
        <label className="sr-only" htmlFor="chat-question">Escribe tu pregunta</label>
        <textarea
          id="chat-question"
          ref={inputRef}
          value={draft}
          maxLength={1500}
          rows={1}
          placeholder="Escribe tu pregunta de matemáticas…"
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={onComposerKeyDown}
          disabled={sending}
        />
        <div className="chat-composer-footer">
          <span>Enter para enviar · Shift + Enter para nueva línea <span className="chat-char-count">{draft.length}/1500</span></span>
          <button className="button button-primary chat-send" type="submit" disabled={sending || !draft.trim()} aria-label="Enviar pregunta">
            {sending ? 'Enviando…' : 'Enviar'} <span aria-hidden="true">↑</span>
          </button>
        </div>
      </form>
    </section>
  )
}
