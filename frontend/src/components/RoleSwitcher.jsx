function RoleSwitcher({ role, onChange }) {
  return (
    <div className="role-switcher" role="group" aria-label="Elegir modo de uso">
      <button
        className={role === 'student' ? 'role-option is-active' : 'role-option'}
        type="button"
        aria-pressed={role === 'student'}
        onClick={() => onChange('student')}
      >
        <span aria-hidden="true">⌂</span> Estudiante
      </button>
      <button
        className={role === 'teacher' ? 'role-option is-active' : 'role-option'}
        type="button"
        aria-pressed={role === 'teacher'}
        onClick={() => onChange('teacher')}
      >
        <span aria-hidden="true">✎</span> Docente
      </button>
    </div>
  )
}

export default RoleSwitcher
