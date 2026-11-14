# Backend

API inicial de Tutor Matemático IA. Esta primera etapa incluye FastAPI, configuración por variables de entorno, CORS y `GET /health`.

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

Para ejecutar la prueba de salud, en otra terminal dentro de `backend/`:

```powershell
pytest
```

`CORS_ORIGINS` acepta una lista de orígenes separados por comas; en local usa `http://localhost:5173`. No se configura todavía ninguna conexión externa.
