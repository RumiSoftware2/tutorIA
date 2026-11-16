const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

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
    throw new Error('No pudimos conectar con el servidor. Comprueba que el backend esté iniciado e inténtalo de nuevo.')
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
    const error = new Error(detail || 'No se pudo completar la solicitud. Inténtalo de nuevo.')
    error.status = response.status
    throw error
  }

  if (response.status === 204) return null
  return response.json()
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
