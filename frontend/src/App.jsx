import { useCallback, useEffect, useState } from 'react'
import CourseGallery from './components/CourseGallery.jsx'
import ChatView from './components/ChatView.jsx'
import RoleSwitcher from './components/RoleSwitcher.jsx'
import TeacherDashboard from './components/TeacherDashboard.jsx'
import TeacherLogin from './components/TeacherLogin.jsx'
import { getCourses } from './services/api.js'
import './App.css'

function App() {
  const [role, setRole] = useState('student')
  const [teacherToken, setTeacherToken] = useState(() => window.sessionStorage.getItem('teacherToken'))
  const [courses, setCourses] = useState([])
  const [selectedCourse, setSelectedCourse] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  async function loadCourses() {
    setLoading(true)
    setError('')
    try {
      setCourses(await getCourses())
    } catch (requestError) {
      setError(requestError.message || 'No pudimos cargar los cursos.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let isCurrent = true
    getCourses()
      .then((items) => {
        if (isCurrent) setCourses(items)
      })
      .catch((requestError) => {
        if (isCurrent) setError(requestError.message || 'No pudimos cargar los cursos.')
      })
      .finally(() => {
        if (isCurrent) setLoading(false)
      })
    return () => { isCurrent = false }
  }, [])

  function chooseRole(nextRole) {
    if (nextRole === 'student') {
      window.sessionStorage.removeItem('teacherToken')
      setTeacherToken(null)
      if (role !== 'student') loadCourses()
    }
    setRole(nextRole)
    setSelectedCourse(null)
  }

  function handleLoginSuccess(token) {
    window.sessionStorage.setItem('teacherToken', token)
    setTeacherToken(token)
  }

  const handleUnauthorized = useCallback(() => {
    window.sessionStorage.removeItem('teacherToken')
    setTeacherToken(null)
  }, [])

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#inicio" aria-label="AulaMate, inicio">
          <span className="brand-mark" aria-hidden="true">
            <svg viewBox="0 0 40 40" fill="none">
              <rect x="4" y="5" width="32" height="30" rx="10" fill="currentColor" />
              <path d="M12 15.5c3.1-2.3 6-.9 8 1.3 2-2.2 4.9-3.6 8-1.3v10.2c-3.1-2.3-6-.9-8 1.3-2-2.2-4.9-3.6-8-1.3V15.5Z" stroke="white" strokeWidth="1.8" strokeLinejoin="round" />
              <path d="M20 17v10" stroke="white" strokeWidth="1.8" />
              <circle cx="30.5" cy="9.5" r="4.5" fill="#FFC36A" stroke="#FFF9F0" strokeWidth="1.5" />
            </svg>
          </span>
          <span className="brand-copy">
            <strong>AulaMate</strong>
            <small>Tu espacio para aprender matemáticas</small>
          </span>
        </a>

        <RoleSwitcher role={role} onChange={chooseRole} />
      </header>

      <main id="inicio">
        {role === 'teacher' ? (
          teacherToken ? (
            <TeacherDashboard token={teacherToken} onLogout={() => chooseRole('student')} onUnauthorized={handleUnauthorized} />
          ) : (
            <TeacherLogin onSuccess={handleLoginSuccess} onCancel={() => chooseRole('student')} />
          )
        ) : selectedCourse ? (
          <ChatView course={selectedCourse} onBack={() => setSelectedCourse(null)} />
        ) : (
          <>
            <section className="hero-section">
              <div className="hero-copy">
                <p className="eyebrow"><span className="eyebrow-dot" /> APRENDER, PASO A PASO</p>
                <h1>¿Qué quieres<br /><span>aprender hoy?</span></h1>
                <p className="hero-description">
                  Elige un curso y descubre que las matemáticas se entienden mejor cuando avanzamos juntos.
                </p>
                <div className="hero-proof">
                  <span className="proof-icon" aria-hidden="true">✓</span>
                  <span>Lecciones organizadas para ti</span>
                </div>
              </div>
              <div className="hero-art" aria-hidden="true">
                <div className="art-orbit orbit-one" />
                <div className="art-orbit orbit-two" />
                <div className="math-card math-card-main">
                  <span className="math-card-label">UN PASO A LA VEZ</span>
                  <strong>x<sup>2</sup> + 5x + 6</strong>
                  <span className="math-answer">= (x + 2)(x + 3)</span>
                </div>
                <div className="floating-note note-star">✦</div>
                <div className="floating-note note-pi">π</div>
                <div className="floating-note note-check">✓</div>
                <div className="art-caption">Las ideas también<br />se conectan.</div>
              </div>
            </section>

            <CourseGallery
              courses={courses}
              loading={loading}
              error={error}
              onRetry={loadCourses}
              onSelect={setSelectedCourse}
            />
          </>
        )}
      </main>

      <footer className="site-footer">
        <span>Hecho para aprender con confianza</span>
        <span className="footer-sparkle" aria-hidden="true">✳</span>
        <span>Matemáticas a tu ritmo</span>
      </footer>
    </div>
  )
}

export default App
