const cardAccents = ['lilac', 'mint', 'peach', 'blue']
const cardSymbols = ['x²', 'π', '∑', '÷']

function CourseCard({ course, index, onSelect }) {
  const topics = Array.isArray(course.topics) ? course.topics.slice(0, 3) : []

  return (
    <article className={`course-card accent-${cardAccents[index % cardAccents.length]}`}>
      <div className="course-card-top">
        <span className="course-symbol" aria-hidden="true">{cardSymbols[index % cardSymbols.length]}</span>
        <span className="course-subject">{course.subject || 'Matemáticas'}</span>
        <span className="course-arrow" aria-hidden="true">↗</span>
      </div>
      <div className="course-card-body">
        <p className="course-grade">{course.grade_level || 'Todos los niveles'}</p>
        <h3>{course.title}</h3>
        <p className="course-description">{course.description}</p>
        {topics.length > 0 && (
          <div className="topic-list" aria-label="Temas clave">
            {topics.map((topic) => <span className="topic-chip" key={topic}>{topic}</span>)}
          </div>
        )}
      </div>
      <button className="course-action" onClick={() => onSelect(course)}>
        Entrar al curso <span aria-hidden="true">→</span>
      </button>
    </article>
  )
}

function CourseGallery({ courses, loading, error, onRetry, onSelect }) {
  return (
    <section className="gallery-section" aria-labelledby="gallery-title">
      <div className="gallery-heading">
        <div>
          <p className="eyebrow">TU PRÓXIMO DESCUBRIMIENTO</p>
          <h2 id="gallery-title">Explora tus cursos</h2>
        </div>
        {!loading && !error && courses.length > 0 && (
          <span className="course-count">{courses.length} {courses.length === 1 ? 'curso' : 'cursos'} disponibles</span>
        )}
      </div>

      {loading && (
        <div className="course-grid" aria-label="Cargando cursos" aria-busy="true">
          {[0, 1, 2].map((item) => (
            <div className="course-skeleton" key={item}>
              <div className="skeleton-shape" />
              <div className="skeleton-line line-short" />
              <div className="skeleton-line line-long" />
              <div className="skeleton-line line-medium" />
              <div className="skeleton-action" />
            </div>
          ))}
        </div>
      )}

      {!loading && error && (
        <div className="state-panel error-panel" role="alert">
          <span className="state-icon" aria-hidden="true">!</span>
          <h3>No pudimos mostrar los cursos</h3>
          <p>{error}</p>
          <button className="button button-primary" onClick={onRetry}>Intentar de nuevo</button>
        </div>
      )}

      {!loading && !error && courses.length === 0 && (
        <div className="state-panel empty-panel">
          <span className="state-icon empty-icon" aria-hidden="true">✦</span>
          <h3>Muy pronto habrá cursos para explorar</h3>
          <p>Cuando el docente publique un curso, aparecerá aquí para que puedas comenzar.</p>
          <button className="button button-secondary" onClick={onRetry}>Actualizar cursos</button>
        </div>
      )}

      {!loading && !error && courses.length > 0 && (
        <div className="course-grid">
          {courses.map((course, index) => (
            <CourseCard key={course.id} course={course} index={index} onSelect={onSelect} />
          ))}
        </div>
      )}
    </section>
  )
}

export default CourseGallery
