const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export async function getCourses() {
  let response
  try {
    response = await fetch(`${API_BASE_URL}/courses`)
  } catch {
    throw new Error('No pudimos conectar con el servidor. Comprueba que el backend esté iniciado e inténtalo de nuevo.')
  }

  if (!response.ok) {
    let detail = ''
    try {
      const body = await response.json()
      detail = typeof body.detail === 'string' ? body.detail : ''
    } catch {
      // Use the friendly fallback below for a non-JSON error response.
    }
    throw new Error(detail || 'Los cursos no están disponibles por el momento.')
  }

  const data = await response.json()
  if (!Array.isArray(data)) throw new Error('El servidor devolvió una respuesta de cursos no válida.')
  return data
}
