const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

function messageForStatus(status, detail = '') {
  if (status === 400) return detail || 'No se pudo procesar la solicitud. Revisa los datos e inténtalo de nuevo.'
  if (status === 422) return 'Revisa los datos ingresados y vuelve a intentarlo.'
  if (status === 401) return 'Tu sesión no es válida. Vuelve a ingresar.'
  if (status === 403) return 'No tienes permiso para realizar esta acción.'
  if (status === 404) return 'No encontramos ese recurso. Actualiza la página e inténtalo de nuevo.'
  if (status === 409) return detail || 'Esta acción entra en conflicto con el estado actual. Actualiza e inténtalo de nuevo.'
  if (status === 413) return 'El archivo supera el tamaño permitido.'
  if (status === 429) return 'El servicio alcanzó un límite temporal. Espera un momento e inténtalo de nuevo.'
  if (status >= 500) return 'El servidor está iniciando o tuvo un problema temporal. Vuelve a intentarlo en unos segundos.'
  return detail || 'No se pudo completar la solicitud. Inténtalo de nuevo.'
}

async function request(path, { token, ...options } = {}) {
  const headers = new Headers(options.headers || {})
  headers.set('Accept', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)

  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  if (options.body && !isFormData && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  let response
  try {
    response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers })
  } catch {
    throw new Error('No pudimos conectar con el servidor. Comprueba tu conexión y que el backend esté iniciado; luego inténtalo de nuevo.')
  }

  if (!response.ok) {
    let detail = ''
    try {
      const body = await response.json()
      if (typeof body.detail === 'string') detail = body.detail
      else if (Array.isArray(body.detail)) detail = body.detail.map((item) => item.msg).filter(Boolean).join(' ')
    } catch {
      // Keep the friendly fallback for non-JSON responses.
    }
    const error = new Error(messageForStatus(response.status, detail))
    error.status = response.status
    throw error
  }

  if (response.status === 204) return null
  try {
    return await response.json()
  } catch {
    throw new Error('El servidor respondió en un formato inesperado. Inténtalo de nuevo.')
  }
}

export function getCourses() {
  return request('/courses')
}

export function teacherLogin(accessCode) {
  return request('/auth/teacher/login', {
    method: 'POST',
    body: JSON.stringify({ access_code: accessCode }),
  })
}

export function getManagedCourses(token) {
  return request('/courses/manage', { token })
}

export function createCourse(data, token) {
  return request('/courses', { method: 'POST', token, body: JSON.stringify(data) })
}

export function updateCourse(courseId, data, token) {
  return request(`/courses/${encodeURIComponent(courseId)}`, {
    method: 'PATCH', token, body: JSON.stringify(data),
  })
}

export function setCourseActive(courseId, isActive, token) {
  return request(`/courses/${encodeURIComponent(courseId)}/status`, {
    method: 'PATCH', token, body: JSON.stringify({ is_active: isActive }),
  })
}

export function getDocuments(courseId, token) {
  return request(`/courses/${encodeURIComponent(courseId)}/documents`, { token })
}

export function uploadDocument(courseId, file, token) {
  const form = new FormData()
  form.append('file', file)
  return request(`/courses/${encodeURIComponent(courseId)}/documents`, {
    method: 'POST', token, body: form,
  })
}

export function deleteDocument(documentId, token) {
  return request(`/documents/${encodeURIComponent(documentId)}`, { method: 'DELETE', token })
}

export function sendChatMessage(payload) {
  return request('/chat', { method: 'POST', body: JSON.stringify(payload) })
}

export function getChatProviders() {
  return request('/chat/providers')
}
