import { useState } from 'react'
import { teacherLogin } from '../services/api.js'

function TeacherLogin({ onSuccess, onCancel }) {
  const [accessCode, setAccessCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setError('')
    try {
      const result = await teacherLogin(accessCode)
      setAccessCode('')
      onSuccess(result.access_token)
    } catch (requestError) {
      setError(requestError.status === 401 ? 'La clave docente no es válida.' : requestError.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="teacher-login-section">
      <button className="back-link" type="button" onClick={onCancel}>
        <span aria-hidden="true">←</span> Volver a Estudiante
      </button>
      <div className="teacher-login-card">
        <span className="teacher-login-icon" aria-hidden="true">✎</span>
        <p className="eyebrow">ESPACIO DOCENTE</p>
        <h1>Qué bueno tenerte aquí.</h1>
        <p className="teacher-login-copy">Ingresa tu clave para administrar los cursos y materiales de estudio.</p>
        <form onSubmit={handleSubmit} className="teacher-login-form">
          <label htmlFor="teacher-access-code">Clave de acceso</label>
          <input
            id="teacher-access-code"
            type="password"
            autoComplete="current-password"
            value={accessCode}
            onChange={(event) => setAccessCode(event.target.value)}
            maxLength={256}
            required
            autoFocus
          />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary login-submit" type="submit" disabled={loading || !accessCode}>
            {loading ? 'Verificando…' : 'Ingresar'}
          </button>
        </form>
        <p className="teacher-login-footnote">La clave se valida de forma segura en el servidor.</p>
      </div>
    </section>
  )
}

export default TeacherLogin
