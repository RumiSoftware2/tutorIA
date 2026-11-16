import { useCallback, useEffect, useState } from 'react'
import CourseForm from './CourseForm.jsx'
import DocumentManager from './DocumentManager.jsx'
import { createCourse, getManagedCourses, setCourseActive, updateCourse } from '../services/api.js'

function TeacherDashboard({ token, onLogout, onUnauthorized }) {
  const [courses, setCourses] = useState([])
  const [loading, setLoading] = useState(true)
  const [pageError, setPageError] = useState('')
  const [notice, setNotice] = useState('')
  const [showForm, setShowForm] = useState(false)
  const [editingCourse, setEditingCourse] = useState(null)
  const [formError, setFormError] = useState('')
  const [saving, setSaving] = useState(false)
  const [busyCourseId, setBusyCourseId] = useState(null)
  const [selectedCourseId, setSelectedCourseId] = useState('')

  useEffect(() => {
    let isCurrent = true
    getManagedCourses(token)
      .then((items) => {
        if (!isCurrent) return
        setCourses(items)
        setSelectedCourseId(items[0]?.id || '')
      })
      .catch((requestError) => {
        if (requestError.status === 401) onUnauthorized()
        else if (isCurrent) setPageError(requestError.message)
      })
      .finally(() => { if (isCurrent) setLoading(false) })
    return () => { isCurrent = false }
  }, [token, onUnauthorized])

  const handleDocumentUnauthorized = useCallback(() => onUnauthorized(), [onUnauthorized])

  function beginCreate() {
    setEditingCourse(null)
    setFormError('')
    setNotice('')
    setShowForm(true)
  }

  function beginEdit(course) {
    setEditingCourse(course)
    setFormError('')
    setNotice('')
    setShowForm(true)
  }

  async function handleSaveCourse(data) {
    setSaving(true)
    setFormError('')
    setNotice('')
    try {
      const saved = editingCourse
        ? await updateCourse(editingCourse.id, data, token)
        : await createCourse(data, token)
      setCourses((current) => editingCourse
        ? current.map((course) => course.id === saved.id ? saved : course)
        : [saved, ...current])
      setSelectedCourseId(saved.id)
      setShowForm(false)
      setEditingCourse(null)
      setNotice(editingCourse ? 'Los cambios del curso se guardaron.' : 'El curso se creó correctamente.')
    } catch (requestError) {
      if (requestError.status === 401) onUnauthorized()
      else setFormError(requestError.message)
    } finally {
      setSaving(false)
    }
  }

  async function toggleCourse(course) {
    const nextState = !course.is_active
    const action = nextState ? 'publicar' : 'despublicar'
    if (!window.confirm(`¿Quieres ${action} “${course.title}”?`)) return
    setBusyCourseId(course.id)
    setPageError('')
    setNotice('')
    try {
      const updated = await setCourseActive(course.id, nextState, token)
      setCourses((current) => current.map((item) => item.id === updated.id ? updated : item))
      setNotice(nextState ? 'El curso está publicado.' : 'El curso quedó despublicado.')
    } catch (requestError) {
      if (requestError.status === 401) onUnauthorized()
      else setPageError(requestError.message)
    } finally {
      setBusyCourseId(null)
    }
  }

  async function retryLoad() {
    setLoading(true)
    setPageError('')
    try {
      const items = await getManagedCourses(token)
      setCourses(items)
      setSelectedCourseId(items[0]?.id || '')
    } catch (requestError) {
      if (requestError.status === 401) onUnauthorized()
      else setPageError(requestError.message)
    } finally {
      setLoading(false)
    }
  }

  const selectedCourse = courses.find((course) => course.id === selectedCourseId)

  return (
    <section className="teacher-dashboard">
      <div className="dashboard-heading">
        <div>
          <p className="eyebrow"><span className="eyebrow-dot" /> HERRAMIENTAS PARA ENSEÑAR</p>
          <h1>Panel docente</h1>
          <p>Organiza tus cursos y prepara el material para tus estudiantes.</p>
        </div>
        <button className="button button-secondary logout-button" onClick={onLogout}>Cerrar sesión</button>
      </div>

      {pageError && (
        <div className="dashboard-alert" role="alert">
          <span>{pageError}</span>
          <button className="text-button" onClick={retryLoad}>Reintentar</button>
        </div>
      )}
      {notice && <p className="dashboard-notice" role="status">{notice}</p>}

      <div className="teacher-workspace">
        <section className="course-management-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">TU CONTENIDO</p>
              <h2>Cursos <span className="count-pill">{courses.length}</span></h2>
            </div>
            <button className="button button-primary" onClick={beginCreate}>＋ Crear curso</button>
          </div>

          {showForm && (
            <CourseForm
              key={editingCourse?.id || 'new-course'}
              course={editingCourse}
              onSubmit={handleSaveCourse}
              onCancel={() => { setShowForm(false); setEditingCourse(null); setFormError('') }}
              saving={saving}
              error={formError}
            />
          )}

          {loading ? <p className="subtle-state">Cargando cursos…</p> : courses.length === 0 ? (
            <div className="manage-empty">
              <span aria-hidden="true">✦</span>
              <strong>Tu primer curso empieza aquí.</strong>
              <p>Crea un espacio para organizar temas y materiales de estudio.</p>
              <button className="button button-secondary" onClick={beginCreate}>Crear primer curso</button>
            </div>
          ) : (
            <div className="managed-course-list">
              {courses.map((course) => (
                <article className={`managed-course ${selectedCourseId === course.id ? 'is-selected' : ''}`} key={course.id}>
                  <button className="managed-course-select" onClick={() => setSelectedCourseId(course.id)}>
                    <span className="managed-course-symbol" aria-hidden="true">f(x)</span>
                    <span className="managed-course-copy">
                      <strong>{course.title}</strong>
                      <small>{course.grade_level || 'Sin nivel'} · {course.subject}</small>
                    </span>
                    <span className={`publication-status ${course.is_active ? 'is-published' : ''}`}>
                      {course.is_active ? 'Publicado' : 'Borrador'}
                    </span>
                  </button>
                  <div className="managed-course-actions">
                    <button className="text-button" onClick={() => beginEdit(course)}>Editar</button>
                    <button className="text-button" onClick={() => toggleCourse(course)} disabled={busyCourseId === course.id}>
                      {busyCourseId === course.id ? 'Actualizando…' : course.is_active ? 'Despublicar' : 'Publicar'}
                    </button>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>

        <div className="documents-panel-wrap">
          {selectedCourse ? (
            <DocumentManager
              key={selectedCourse.id}
              course={selectedCourse}
              token={token}
              onUnauthorized={handleDocumentUnauthorized}
            />
          ) : (
            <section className="document-placeholder">
              <span className="document-placeholder-icon" aria-hidden="true">▤</span>
              <p className="eyebrow">MATERIAL DE ESTUDIO</p>
              <h3>Elige un curso para organizar sus documentos.</h3>
              <p>Los archivos PDF, Word y PowerPoint se procesan para preparar fragmentos de estudio.</p>
            </section>
          )}
        </div>
      </div>
    </section>
  )
}

export default TeacherDashboard
