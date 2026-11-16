# Backend

API de Tutor Matemático IA. Incluye FastAPI, configuración por entorno, CORS, `GET /health`, modelos iniciales de SQLAlchemy y migraciones Alembic.

## Requisitos

- Python 3.12 o superior (la auditoría local encontró Python 3.13.3).

## Ejecución local (PowerShell)

Desde la raíz del repositorio:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Comprueba `http://localhost:8000/health` (esperado: `{"status":"ok"}`) y la documentación OpenAPI en `http://localhost:8000/docs`.

## Base de datos y migraciones

Los modelos iniciales describen cursos, documentos y fragmentos. Para aplicar la migración se necesita un proyecto PostgreSQL (la guía del repositorio indica cómo preparar Supabase) y una `DATABASE_URL` válida en `backend/.env`. Usa el formato entregado por Supabase, con el prefijo `postgresql+psycopg://` y `sslmode=require`; no uses el valor de ejemplo como credencial real.

Cuando la URL real esté configurada:

```powershell
alembic upgrade head
```

La migración crea `courses`, `documents` y `document_chunks`, sus claves foráneas, restricciones, índices y el índice GIN de búsqueda. No se ejecuta automáticamente al iniciar FastAPI.

## Acceso docente y cursos

Antes de probar el login, agrega estas variables a tu archivo local `.env` (no lo subas a Git):

```dotenv
TEACHER_ACCESS_CODE=elige_una_clave_larga_para_docentes
JWT_SECRET_KEY=secreto_aleatorio_generado_localmente
JWT_EXPIRE_HOURS=8
```

Genera el secreto JWT desde PowerShell con `python -c "import secrets; print(secrets.token_urlsafe(48))"` y guarda el resultado en `.env`. No compartas ese valor. El login se prueba en `POST /api/v1/auth/teacher/login`; las rutas de administración requieren `Authorization: Bearer <token>`. Las rutas `GET /api/v1/courses` y `GET /api/v1/courses/{id}` muestran solo cursos activos. Para el panel docente, `GET /api/v1/courses/manage` devuelve todos los cursos y también requiere token.

Operaciones docentes disponibles: `POST /api/v1/courses`, `PATCH /api/v1/courses/{id}` y `PATCH /api/v1/courses/{id}/status`.

## Documentos de estudio

El docente autenticado puede usar `POST /api/v1/courses/{course_id}/documents` para cargar un PDF, DOCX o PPTX en `multipart/form-data`, `GET` en la misma ruta para ver los materiales del curso y `DELETE /api/v1/documents/{document_id}` para borrar uno. El límite inicial es 10 MB; se guardan los metadatos y fragmentos de texto en PostgreSQL, no el archivo original. Si un PDF no permite extraer texto, la API informa que el OCR no está incluido. La conversión usa MarkItDown con plugins desactivados.

En Swagger (`/docs`), autentícate con el botón **Authorize** después del login. Para cargar un archivo, abre el endpoint `POST`, indica el UUID del curso y selecciona el archivo en el campo `file`. La respuesta indica estado y cantidad de fragmentos. Después puedes verificar el listado del curso con su endpoint `GET`.

Para ejecutar la prueba de salud, en otra terminal dentro de `backend/`:

```powershell
pytest
```

`CORS_ORIGINS` acepta una lista de orígenes separados por comas; en local usa `http://localhost:5173`. La aplicación puede arrancar y servir `/health` sin conexión de base de datos; Alembic sí requiere `DATABASE_URL` para una migración real.
