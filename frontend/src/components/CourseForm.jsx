import { useState } from 'react'

function CourseForm({ course, onSubmit, onCancel, saving, error }) {
  const [form, setForm] = useState({
    title: course?.title || '',
    description: course?.description || '',
    grade_level: course?.grade_level || '',
    subject: course?.subject || 'Matemáticas',
    topics: (course?.topics || []).join('\n'),
  })

  function update(field, value) {
    setForm((current) => ({ ...current, [field]: value }))
  }

  function handleSubmit(event) {
    event.preventDefault()
    onSubmit({
      title: form.title.trim(),
      description: form.description.trim(),
      grade_level: form.grade_level.trim() || null,
      subject: form.subject.trim(),
      topics: form.topics.split('\n').map((topic) => topic.trim()).filter(Boolean),
    })
  }

  return (
    <form className="course-form" onSubmit={handleSubmit}>
      <div className="course-form-title">
        <div>
          <p className="eyebrow">{course ? 'ACTUALIZA EL CONTENIDO' : 'UN NUEVO COMIENZO'}</p>
          <h3>{course ? 'Editar curso' : 'Crear curso'}</h3>
        </div>
        <button className="icon-button" type="button" onClick={onCancel} aria-label="Cerrar formulario">×</button>
      </div>

      <div className="form-grid">
        <div className="field-group field-wide">
          <label htmlFor="course-title">Nombre del curso <span aria-hidden="true">*</span></label>
          <input id="course-title" value={form.title} onChange={(event) => update('title', event.target.value)} maxLength={150} required />
        </div>
        <div className="field-group">
          <label htmlFor="course-subject">Asignatura <span aria-hidden="true">*</span></label>
          <input id="course-subject" value={form.subject} onChange={(event) => update('subject', event.target.value)} maxLength={80} required />
        </div>
        <div className="field-group">
          <label htmlFor="course-grade">Nivel o grado</label>
          <input id="course-grade" value={form.grade_level} onChange={(event) => update('grade_level', event.target.value)} maxLength={60} placeholder="Ej. Octavo" />
        </div>
        <div className="field-group field-wide">
          <label htmlFor="course-description">Descripción <span aria-hidden="true">*</span></label>
          <textarea id="course-description" value={form.description} onChange={(event) => update('description', event.target.value)} maxLength={5000} rows={3} required />
        </div>
        <div className="field-group field-wide">
          <label htmlFor="course-topics">Temas clave</label>
          <textarea id="course-topics" value={form.topics} onChange={(event) => update('topics', event.target.value)} rows={3} placeholder={'Un tema por línea\nEj. Factor común'} />
          <small>Escribe un tema por línea, hasta 30 temas.</small>
        </div>
      </div>

      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="form-actions">
        <button className="button button-secondary" type="button" onClick={onCancel}>Cancelar</button>
        <button className="button button-primary" type="submit" disabled={saving}>
          {saving ? 'Guardando…' : course ? 'Guardar cambios' : 'Crear curso'}
        </button>
      </div>
    </form>
  )
}

export default CourseForm
