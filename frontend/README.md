# AulaMate — frontend

Interfaz React + Vite en español. Incluye la galería de cursos, el acceso docente, la administración de cursos y documentos, y el chat del tutor con renderizado Markdown y LaTeX.

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

El modo docente usa la clave compartida que valida el backend y mantiene el JWT en `sessionStorage` durante la sesión de la pestaña. Las operaciones de cursos y documentos requieren ese token. El estudiante abre un curso publicado para conversar; el historial solo vive en memoria y se reinicia al salir del curso. Las claves Gemini y Groq pertenecen exclusivamente a `backend/.env` y nunca deben añadirse a variables `VITE_`.

## Prueba integrada local

1. Inicia FastAPI desde `backend/` y confirma `http://localhost:8000/health`.
2. En `frontend/`, ejecuta `npm run dev` y abre `http://localhost:5173`.
3. Como docente, crea o publica un curso y carga un PDF, DOCX o PPTX didáctico.
4. Vuelve al modo Estudiante, abre ese curso y pregunta sobre el material.
5. Confirma que se ve la respuesta, las fuentes por nombre de documento y las fórmulas en línea o bloque. Usa **Shift + Enter** para saltar de línea; **Enter** envía.
6. Vuelve a la galería y entra a otro curso: la conversación anterior debe desaparecer.

## Errores y responsive

- Si la API no conecta, confirma que backend y frontend estén activos y que `backend/.env` incluya `CORS_ORIGINS=http://localhost:5173`.
- Si el servidor está iniciando o el proveedor de IA no responde, espera un momento y usa el botón de reintento. El frontend no presenta detalles internos del servidor.
- La carga docente acepta PDF, DOCX y PPTX hasta 10 MB; los PDF escaneados pueden no tener texto extraíble porque el OCR no está incluido.
- Revisa la galería, el panel docente y el chat en móvil (320–640 px), tableta (641–1024 px) y escritorio; no debe aparecer scroll horizontal de página.
- Usa solamente material didáctico de prueba; no cargues información personal o confidencial de estudiantes.
