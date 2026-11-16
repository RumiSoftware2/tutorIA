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

Para ejecutar la prueba de salud, en otra terminal dentro de `backend/`:

```powershell
pytest
```

`CORS_ORIGINS` acepta una lista de orígenes separados por comas; en local usa `http://localhost:5173`. La aplicación puede arrancar y servir `/health` sin conexión de base de datos; Alembic sí requiere `DATABASE_URL` para una migración real.
