# AulaMate — frontend

Interfaz React + Vite en español. Incluye la galería de cursos, el acceso docente, la administración de cursos y la gestión de documentos desde la API.

## Ejecutar en local (PowerShell)

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Vite inicia normalmente en `http://localhost:5173`. La API base se configura con `VITE_API_URL` en `.env`; por defecto es `http://localhost:8000/api/v1`. El backend debe estar iniciado y tener `TEACHER_ACCESS_CODE`, `JWT_SECRET_KEY` y `DATABASE_URL` configuradas para habilitar la administración.

## Comprobaciones

```powershell
npm run build
npm run lint
```

El modo docente usa la clave compartida que valida el backend y mantiene el JWT en `sessionStorage` durante la sesión de la pestaña. Las operaciones de cursos y documentos requieren ese token. El chat con Markdown y LaTeX se integrará en su siguiente etapa.
