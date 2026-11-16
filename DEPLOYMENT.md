# Despliegue de AulaMate

Esta guía corresponde a la Etapa 10. La aplicación usa Vercel para React, Render para FastAPI y el proyecto Supabase existente para PostgreSQL. Render lee la configuración de `render.yaml`; Vercel detecta Vite desde `frontend/`.

## Antes de empezar

1. Revisa los cambios de esta etapa y haz tu commit local.
2. Sube la rama `main` a GitHub. Render y Vercel necesitan leer del repositorio remoto.
3. Ten a mano, sin pegarlos en este archivo ni en el chat, `DATABASE_URL`, la clave de Gemini y la clave de Groq. Mantén los secretos en los paneles de Render.
4. No cargues documentos personales o confidenciales de estudiantes.

## 1. Crear el servicio backend en Render

1. En Render, conecta la cuenta de GitHub y selecciona el repositorio de Tutor Matemático IA.
2. Crea un **Blueprint** usando el `render.yaml` de la raíz. Render encuentra este archivo en la raíz del repositorio y deja los valores secretos (`sync: false`) para introducir en su panel.
3. Confirma que el servicio se llame `tutoria-backend`, use el plan `Free` y tenga `/health` como health check. El servicio usa `backend/` como raíz, instala `requirements.txt` y ejecuta Alembic antes de iniciar FastAPI.
4. Completa las variables secretas solicitadas:
   - `DATABASE_URL`: la URI de Supabase Session Pooler que ya probaste localmente. Mantén el esquema compatible con el backend (`postgresql+psycopg://...`).
   - `JWT_SECRET_KEY`: genera una clave distinta de la docente; en PowerShell puedes ejecutar `python -c "import secrets; print(secrets.token_urlsafe(48))"` y pegar el resultado directamente en Render.
   - `TEACHER_ACCESS_CODE`: crea una clave larga para iniciar sesión como docente.
   - `GEMINI_API_KEY` y `GROQ_API_KEY`: pega las claves desde sus paneles oficiales. No las pongas en Vercel ni en el navegador.
   - `CORS_ORIGINS`: inicialmente puedes poner `http://localhost:5173`; la reemplazarás por el origen de Vercel después de desplegar el frontend.
5. Guarda y deja que termine el despliegue. En los logs, confirma que `alembic upgrade head` termina correctamente y que Uvicorn inicia.
6. Abre `https://<servicio>.onrender.com/health`. Debe responder `{"status":"ok"}`. Guarda la URL base del servicio.

## 2. Crear el frontend en Vercel

1. Importa el mismo repositorio desde GitHub.
2. Configura **Root Directory** en `frontend` y confirma Vite. Build y output esperados: `npm run build` y `dist` (Vercel suele detectarlos automáticamente).
3. Antes del primer deploy, agrega `VITE_API_URL` con el valor `https://<servicio>.onrender.com/api/v1`, usando la URL real que anotaste en el paso anterior.
4. Despliega y abre la URL pública de Vercel.

## 3. Completar CORS y comprobar el MVP

1. Copia el origen de Vercel, por ejemplo `https://proyecto.vercel.app`, sin ruta final.
2. En el panel de Render, cambia `CORS_ORIGINS` al origen exacto de Vercel y guarda el cambio. Render reiniciará el backend.
3. En la URL pública, revisa galería, login docente, creación/edición de cursos, carga de un documento de prueba y una pregunta al chat.
4. Comprueba que las fuentes se muestran, que LaTeX se renderiza y que el curso y los fragmentos siguen presentes tras un redeploy.
5. El primer request después de inactividad puede tardar porque el servicio gratuito puede suspenderse. Espera que responda y vuelve a intentar si el navegador agota el tiempo.

## Límites y seguridad

- El servicio gratuito puede suspenderse por inactividad y no ofrece disponibilidad garantizada. Revisa los planes y términos actuales antes de usarlo institucionalmente.
- No añadir claves de Gemini, Groq, JWT ni PostgreSQL a variables `VITE_*`; cualquier variable de Vite queda accesible al frontend.
- Los archivos originales no se guardan en el filesystem efímero de Render; la app conserva metadatos y fragmentos en Supabase.
- No crear tablas manualmente ni generar migraciones en el comando de inicio. Render ejecuta las migraciones ya versionadas.
- No habilitar facturación ni cambiar a un plan pago para este prototipo.
