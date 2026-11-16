import { useEffect, useState } from 'react'
import { deleteDocument, getDocuments, uploadDocument } from '../services/api.js'

const MAX_FILE_BYTES = 10 * 1024 * 1024
const ACCEPTED_EXTENSIONS = ['pdf', 'docx', 'pptx']

function formatDate(value) {
  return new Intl.DateTimeFormat('es', { dateStyle: 'medium' }).format(new Date(value))
}

function formatSize(bytes) {
  return bytes >= 1024 * 1024 ? `${(bytes / 1024 / 1024).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`
}

function DocumentManager({ course, token, onUnauthorized }) {
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    let isCurrent = true
    getDocuments(course.id, token)
      .then((items) => { if (isCurrent) setDocuments(items) })
      .catch((requestError) => {
        if (requestError.status === 401) onUnauthorized()
        else if (isCurrent) setError(requestError.message)
      })
      .finally(() => { if (isCurrent) setLoading(false) })
    return () => { isCurrent = false }
  }, [course.id, token, onUnauthorized])

  async function handleUpload(event) {
    const input = event.currentTarget
    const file = input.files?.[0]
    if (!file) return
    setError('')
    setNotice('')
    const extension = file.name.split('.').pop()?.toLowerCase()
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setError('Selecciona un archivo PDF, DOCX o PPTX.')
      input.value = ''
      return
    }
    if (file.size > MAX_FILE_BYTES) {
      setError('El archivo supera el límite de 10 MB.')
      input.value = ''
      return
    }

    setUploading(true)
    try {
      const document = await uploadDocument(course.id, file, token)
      setDocuments((current) => [document, ...current])
      setNotice(`“${document.title}” quedó listo con ${document.chunk_count} fragmentos.`)
    } catch (requestError) {
      if (requestError.status === 401) onUnauthorized()
      else setError(requestError.message)
    } finally {
      setUploading(false)
      input.value = ''
    }
  }

  async function handleDelete(document) {
    if (!window.confirm(`¿Eliminar “${document.title}” y sus fragmentos?`)) return
    setError('')
    setNotice('')
    try {
      await deleteDocument(document.id, token)
      setDocuments((current) => current.filter((item) => item.id !== document.id))
      setNotice('El material se eliminó correctamente.')
    } catch (requestError) {
      if (requestError.status === 401) onUnauthorized()
      else setError(requestError.message)
    }
  }

  return (
    <section className="document-manager">
      <div className="document-section-heading">
        <div>
          <p className="eyebrow">BIBLIOTECA DEL CURSO</p>
          <h3>Material de estudio</h3>
        </div>
        <label className={`button button-primary upload-button ${uploading ? 'is-disabled' : ''}`}>
          {uploading ? 'Procesando…' : '＋ Cargar material'}
          <input type="file" accept=".pdf,.docx,.pptx" onChange={handleUpload} disabled={uploading} />
        </label>
      </div>
      <p className="upload-help">PDF, DOCX o PPTX · máximo 10 MB. El archivo original no se conserva.</p>
      <p className="ocr-note">Los PDF escaneados como imagen pueden no tener texto extraíble; el OCR no está incluido.</p>
      {error && <p className="inline-error" role="alert">{error}</p>}
      {notice && <p className="inline-success" role="status">{notice}</p>}

      {loading ? <p className="subtle-state">Cargando materiales…</p> : documents.length === 0 ? (
        <div className="documents-empty">Todavía no hay materiales en este curso.</div>
      ) : (
        <div className="document-list">
          {documents.map((document) => (
            <article className="document-row" key={document.id}>
              <span className="document-file-icon" aria-hidden="true">▤</span>
              <div className="document-main">
                <strong>{document.title}</strong>
                <span>{document.original_filename} · {formatSize(document.file_size_bytes)}</span>
              </div>
              <div className="document-meta">
                <span className={`document-status ${document.status === 'ready' ? 'status-ready' : 'status-failed'}`}>
                  {document.status === 'ready' ? 'Listo' : 'Error'} · {document.chunk_count} frag.
                </span>
                <time dateTime={document.created_at}>{formatDate(document.created_at)}</time>
              </div>
              <button className="document-delete" type="button" onClick={() => handleDelete(document)} aria-label={`Eliminar ${document.title}`}>
                Eliminar
              </button>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}

export default DocumentManager
