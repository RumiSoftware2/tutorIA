# 04. Base de datos, despliegue, pruebas y flujo de commits

> Este documento coordina el trabajo. Leer los cuatro archivos antes de iniciar.

## 1. Objetivo

Guiar a Codex y al propietario del proyecto por entregas pequeñas, conectando el backend a Supabase, publicando el frontend en Vercel y el backend en Render. El proceso debe permitir probar cada parte antes de avanzar.

**No crear cuentas, aceptar términos, introducir contraseñas, habilitar facturación ni cambiar planes en nombre del usuario.** Codex prepara código e instrucciones; el usuario crea los recursos y añade sus secretos desde los paneles oficiales.

## 2. Consideraciones actuales de los planes gratuitos

Verificadas el **14 de noviembre de 2026**. Los precios, cuotas y condiciones pueden cambiar; consultar los enlaces oficiales cuando se cree cada cuenta.

| Servicio | Uso en el proyecto | Advertencias del nivel gratuito |
|---|---|---|
| Vercel Hobby | Hospedar React/Vite | Está orientado a proyectos personales y uso no comercial. Para un uso institucional/comercial hay que revisar las condiciones o el plan adecuado. |
| Render Free Web Service | Hospedar FastAPI | Puede dormir tras 15 minutos sin tráfico; el primer acceso posterior puede tardar alrededor de un minuto. El sistema de archivos es efímero. No usarlo como producción crítica. |
| Supabase Free | PostgreSQL persistente | La cuota publicada incluye 500 MB de base de datos por proyecto; un proyecto con poca actividad puede pausarse después de una semana. Los datos permanecen y el proyecto se puede reactivar. |
| Gemini API Free Tier | Respuestas del tutor | Hay modelos y límites sujetos a disponibilidad/cuota. El contenido enviado puede utilizarse para mejorar productos en la modalidad gratuita. No enviar datos personales o confidenciales. |

Fuentes oficiales:

- Render Free: https://render.com/docs/free
- Render FAQ: https://render.com/docs/faq
- Supabase planes y cuotas: https://supabase.com/pricing
- Supabase pausa por inactividad: https://supabase.com/docs/guides/platform/free-project-pausing
- Supabase conexiones: https://supabase.com/docs/guides/database/connecting-to-postgres
- Vercel Hobby: https://vercel.com/docs/plans/hobby
- Vercel límites: https://vercel.com/docs/limits
- Gemini API precios y disponibilidad: https://ai.google.dev/gemini-api/docs/pricing
- Gemini términos: https://ai.google.dev/gemini-api/terms

### Consecuencia arquitectónica

Los datos duraderos deben almacenarse en Supabase, no en el disco local de Render. Esta guía guarda los fragmentos de documentos y los cursos en PostgreSQL. El archivo original no se conserva.

## 3. Paso A: crear el proyecto de Supabase

El propietario debe:

1. Entrar en https://supabase.com/ y crear una cuenta/proyecto.
2. Crear un proyecto nuevo para este prototipo.
3. Escoger una región cercana a los usuarios y compatible con las opciones de conexión disponibles.
4. Definir y guardar la contraseña de PostgreSQL en un gestor seguro.
5. Esperar a que el proyecto esté disponible.
6. En el panel, abrir **Connect** y consultar las opciones de conexión.
7. Copiar la conexión **Session pooler** si el backend de Render necesita conectividad IPv4. Si se confirma que la red acepta IPv6 y la conexión directa, Codex puede elegir la conexión directa tras documentar la decisión.
8. Guardar la URI como `DATABASE_URL` solamente en los secretos locales y en Render.

### Formato esperado para SQLAlchemy/Psycopg

Supabase entrega una URI PostgreSQL. Para usar el driver Psycopg 3 con SQLAlchemy, el esquema debe quedar en forma:

```text
postgresql+psycopg://USUARIO:CONTRASEÑA@HOST:PUERTO/postgres?sslmode=require
```

Copiar host, usuario, puerto y parámetros exactamente desde **Connect**. No inventar el host del pooler ni componerlo manualmente.

Si la contraseña contiene caracteres especiales (`@`, `#`, `?`, `/`, espacios, etc.), deben codificarse correctamente en la URI. Preferir copiar el connection string y sustituir únicamente el marcador de contraseña, codificando los caracteres reservados.

### Qué NO hacer

- No usar `service_role` ni claves de Supabase en el frontend.
- No conectar React directamente a PostgreSQL.
- No exponer `DATABASE_URL` en Vercel.
- No crear tablas manualmente y luego duplicarlas con SQLAlchemy. El esquema debe quedar versionado en Alembic.
- No guardar el archivo binario en el disco de Render.

### Crear el esquema

Con `DATABASE_URL` configurado localmente:

```bash
cd backend
alembic upgrade head
```

Codex debe confirmar que se crearon las tablas e índices previstos y dejar documentado cómo revisar el esquema en Supabase.

## 4. Paso B: crear la clave de Gemini

1. Abrir https://aistudio.google.com/.
2. Iniciar sesión y crear una API key desde el panel de API Keys.
3. Verificar que la clave puede invocar el modelo seleccionado en la cuenta y modalidad gratuita.
4. Guardar la clave en `GEMINI_API_KEY` dentro del backend, nunca en React.
5. Revisar el panel de Usage y los límites vigentes.

Modelo inicial sugerido a 14 de noviembre de 2026: `gemini-3.8-flash`. La tabla oficial consultada muestra precio gratuito para entrada y salida en el nivel Free; aun así, la disponibilidad, límites y nombre de modelo deben comprobarse al crear la clave. Modelos Gemini 4 de razonamiento como Carbon/Argon no están incluidos en el nivel gratuito consultado.

No escribir `gemini-3.8-flash` en múltiples archivos; usar una única variable `GEMINI_MODEL`.

### Nota de privacidad crítica

La modalidad gratuita indica que el contenido puede utilizarse para mejorar productos. Por tanto:

- En esta prueba solo usar guías y documentos didácticos no confidenciales.
- No incluir nombres, documentos de identidad, correos, notas, diagnósticos, información familiar o datos identificables de menores.
- No pedir información personal en el chat.
- Antes de uso institucional real, revisar las condiciones de tratamiento de datos y privacidad, y evaluar un plan/proveedor con condiciones apropiadas.

## 5. Paso C: variables locales

### Backend (`backend/.env`)

Basarse en `backend/.env.example`. Contendrá, como mínimo:

```dotenv
APP_ENV=development
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET_KEY=SECRETO_LARGO_ALEATORIO
JWT_EXPIRE_HOURS=8
TEACHER_ACCESS_CODE=CLAVE_DOCENTE_LARGA
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.8-flash
CORS_ORIGINS=http://localhost:5173
UPLOAD_MAX_MB=10
MAX_EXTRACTED_CHARS=250000
CHUNK_SIZE_CHARS=1200
CHUNK_OVERLAP_CHARS=150
RETRIEVAL_TOP_K=5
MAX_CHAT_MESSAGE_CHARS=1500
MAX_HISTORY_MESSAGES=8
MAX_CONTEXT_CHARS=8000
```

Generar `JWT_SECRET_KEY` aleatorio, no usar una palabra normal. Puede generarse con Python:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

La clave `TEACHER_ACCESS_CODE` debe ser larga y diferente a la contraseña de Supabase.

### Frontend (`frontend/.env`)

```dotenv
VITE_API_URL=http://localhost:8000/api/v1
```

Los dos `.env` deben estar ignorados por Git. Solo los `.env.example` sin secretos se versionan.

## 6. Paso D: ejecutar en local

Terminal 1, backend:

```bash
cd backend
# Activar el entorno virtual existente
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Terminal 2, frontend:

```bash
cd frontend
npm install
npm run dev
```

Direcciones esperadas:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Swagger local: `http://localhost:8000/docs`

Si el puerto ya está ocupado o el proyecto usa otros puertos, actualizar el `.env` del frontend y la lista CORS del backend de forma coherente.

### Prueba local mínima

1. Confirmar que `/health` responde.
2. Crear un curso desde modo Docente.
3. Cargar un documento PDF de texto seleccionable.
4. Confirmar que el documento queda `ready` y tiene fragmentos.
5. Cambiar a Estudiante.
6. Abrir el curso.
7. Hacer una pregunta relacionada con el documento.
8. Comprobar que la respuesta tiene pasos claros, LaTeX y referencias si encontró fragmentos.
9. Hacer una pregunta de otro tema o no matemático y comprobar la redirección amable.
10. Reiniciar el backend y confirmar que el curso y sus fragmentos siguen en Supabase.

## 7. Paso E: desplegar el backend en Render

Antes del despliegue, backend debe funcionar localmente y tener Dockerfile o configuración de runtime revisada. Para el servicio Python en Render se debe:

1. Entrar en https://render.com/.
2. Crear un **New Web Service** y conectar el repositorio GitHub.
3. Seleccionar la rama acordada.
4. Establecer **Root Directory** como `backend`.
5. Elegir plan Free para el prototipo.
6. Build Command:

```bash
pip install -r requirements.txt
```

7. Start Command (ajustar al módulo real de FastAPI):

```bash
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

8. Configurar las variables de entorno en el panel de Render:
   - `APP_ENV=production`
   - `DATABASE_URL`
   - `JWT_SECRET_KEY`
   - `TEACHER_ACCESS_CODE`
   - `GEMINI_API_KEY`
   - `GEMINI_MODEL`
   - `CORS_ORIGINS` con la URL real del frontend
   - límites del backend
9. Configurar Health Check Path como `/health`.
10. Desplegar y abrir la URL generada; probar `/health`.
11. Copiar la URL pública de Render para configurar el frontend.

### Reglas de despliegue

- No subir documentos originales al filesystem de Render.
- No usar SQLite local en Render.
- No añadir un proceso de ping artificial para intentar impedir el sleep. La experiencia debe informar al usuario del arranque en frío.
- No ejecutar `alembic revision --autogenerate` en el comando Start. Las migraciones se generan localmente, se revisan y se versionan; Render solamente ejecuta `alembic upgrade head`.
- No usar plan gratuito de Render como servicio crítico o con disponibilidad garantizada.

## 8. Paso F: desplegar el frontend en Vercel

1. Entrar en https://vercel.com/.
2. Importar el mismo repositorio de GitHub.
3. Establecer **Root Directory** como `frontend`.
4. Framework preset: Vite (o detección automática confirmada).
5. Build Command: `npm run build`.
6. Output Directory: `dist`.
7. Añadir variable:

```dotenv
VITE_API_URL=https://URL-REAL-DE-RENDER/api/v1
```

8. Ejecutar deployment.
9. Abrir la URL de Vercel y revisar galería, acceso docente, carga y chat.
10. Volver a Render y confirmar que `CORS_ORIGINS` contiene exactamente el origen de producción de Vercel, por ejemplo `https://proyecto.vercel.app` (sin ruta `/`).
11. Si se cambia `VITE_API_URL`, volver a desplegar el frontend, porque Vite inserta esa variable durante el build.

### Nota sobre Vercel Hobby

El plan Hobby se orienta a uso personal/no comercial. Antes de usar la aplicación formalmente en una institución o en un contexto comercial, revisar las condiciones actuales de Vercel y elegir el plan permitido. Si no encaja, se puede desplegar el frontend estático en Render u otro hosting compatible sin cambiar la arquitectura React.

## 9. Flujo de Git y commits pequeños

El usuario quiere revisar el sistema por etapas. Codex debe seguir este orden y detenerse tras cada commit.

| Etapa | Alcance | Commit sugerido | Criterio para detenerse |
|---|---|---|---|
| 0 | Inspección del repo, dependencias y estado actual | Sin commit si no hay cambios | Entregar diagnóstico y plan de adaptación |
| 1 | Esqueleto FastAPI, configuración, health y CORS | `chore(backend): scaffold FastAPI service` | `/health` responde localmente |
| 2 | SQLAlchemy, modelos iniciales y Alembic | `feat(backend): add database models and migrations` | Migraciones aplican en Supabase |
| 3 | Acceso docente JWT y CRUD de cursos | `feat(backend): add teacher access and course API` | Crear/editar/listar desde Swagger |
| 4 | MarkItDown, fragmentación y documentos | `feat(backend): process and index course documents` | PDF/DOCX/PPTX se guardan como fragmentos |
| 5 | Recuperación por curso, Gemini y endpoint de chat | `feat(backend): add grounded math tutor endpoint` | Prueba manual de una pregunta y referencias |
| 6 | UI base React, selector de rol y galería | `feat(frontend): build responsive course gallery` | Navegación y responsive local |
| 7 | Login docente, formulario de curso y carga | `feat(frontend): add teacher course management` | Docente crea curso y carga archivo |
| 8 | Chat, Markdown y LaTeX | `feat(frontend): add math tutor chat and katex` | Pregunta-respuesta con fórmulas |
| 9 | Integración, errores, ajustes responsive y guía | `chore: finish MVP integration and deployment docs` | Lista de aceptación completa |
| 10 | Configuración de despliegue y correcciones posteriores | Commits correctivos pequeños | Vercel/Render/Supabase validados |

### Reglas de commit

- Un commit debe representar una unidad funcional pequeña y verificable.
- Ejecutar pruebas y build antes de cada commit.
- Revisar `git diff` y `git status` antes de confirmar.
- Nunca incluir `.env`, secretos, archivos de carga reales ni datos personales.
- No usar commits masivos que mezclen frontend, backend y despliegue sin necesidad.
- No hacer `git push`, no cambiar la rama principal y no fusionar ramas sin autorización explícita del propietario.
- Después de cada commit, informar: archivos creados/modificados, funcionalidades, comandos ejecutados, pruebas aprobadas/fallidas, hash del commit y qué revisar.
- **Detenerse al terminar el commit**. Esperar la revisión del usuario y su instrucción para continuar con la siguiente etapa.

## 10. Guion de revisión del usuario por entrega

Después de cada etapa, el usuario debe poder comprobar algo concreto:

- Etapas 1–2: API arriba y tablas/migraciones en Supabase.
- Etapa 3: entrar como docente desde Swagger, crear curso y verificarlo en PostgreSQL.
- Etapa 4: cargar un archivo pequeño de prueba, ver metadatos y fragmentos en la base de datos.
- Etapa 5: pregunta real y respuesta del modelo; revisar tono y exactitud matemática.
- Etapa 6: abrir Vite, recorrer galería en escritorio y móvil.
- Etapa 7: entrar como docente desde interfaz, crear curso y subir documento.
- Etapa 8: conversar como estudiante y comprobar renderizado de LaTeX.
- Etapa 9–10: despliegue integrado y prueba desde URL pública.

No avanzar porque “compila”; avanzar cuando el usuario pueda probar el comportamiento visible y los datos estén donde corresponde.

## 11. Problemas frecuentes y diagnóstico

| Síntoma | Revisar primero |
|---|---|
| Frontend muestra error CORS | `CORS_ORIGINS`, origen exacto, protocolo HTTPS y reinicio del backend |
| API no conecta a Supabase | URL copiada desde Connect, contraseña codificada, driver `psycopg`, SSL y modo de conexión |
| Supabase no resuelve conexión desde Render | Probar Session Pooler y comprobar host/puerto copiados del panel |
| Render responde lento al primer acceso | Cold start del plan Free; consultar logs y `/health` |
| Cursos desaparecen después de reinicio | Verificar que se usa `DATABASE_URL` y no SQLite/archivos locales |
| Archivo se pierde tras redeploy | No persistir archivos en el disco de Render; solo chunks y metadatos en Supabase |
| MarkItDown no extrae texto | Confirmar que el PDF tiene texto seleccionable y que extras están instalados |
| Gemini devuelve 429 | Revisar cuota/modelo en Google AI Studio; no repetir llamadas automáticamente en bucle |
| Gemini devuelve 404/modelo desconocido | Revisar `GEMINI_MODEL` y disponibilidad real de ese modelo para la clave |
| Fórmula aparece como texto | Confirmar delimitadores `$...$`/`$$...$$`, `remark-math`, `rehype-katex` y CSS KaTeX |
| Login docente funciona en UI pero API responde 401 | Comprobar token, expiración, cabecera Bearer y secreto JWT coincidente |
| Vercel no toma cambio de API URL | Revisar variable en el proyecto y volver a desplegar el frontend |

## 12. Ruta de evolución posterior al MVP

No implementar ahora. Mantener los módulos listos para incorporar por etapas:

1. **Cuentas reales:** Supabase Auth o proveedor equivalente, usuarios docentes, cuentas de estudiantes y roles por institución.
2. **Archivos originales:** Supabase Storage, rutas firmadas y políticas de acceso.
3. **Búsqueda semántica:** embeddings y pgvector en Supabase, manteniendo una interfaz `retrieval_service` intercambiable.
4. **Mejora de conversación:** guardar conversaciones solo con consentimiento, reglas de retención, privacidad y control de acceso.
5. **Respuestas en streaming:** Server-Sent Events cuando el chat básico esté probado.
6. **Procesamiento asíncrono:** worker/cola si el tamaño o tiempo de conversión supera lo razonable para una petición web.
7. **Más modelos:** conectores alternativos compatibles con la interfaz `TutorProvider`; comparar calidad, privacidad y coste antes de activar un proveedor de pago.
8. **Moodle:** integración por API/LTI o mecanismo compatible, sin mezclar Moodle dentro del núcleo del tutor.
9. **Observabilidad y límites:** métricas, límites por usuario, control de cuotas y alertas.
10. **Producción:** hosting sin cold start, backups, autenticación robusta, pruebas de carga y revisión de seguridad/privacidad.

## 13. Instrucción inicial lista para entregar a Codex

Copiar este mensaje en Codex junto con el repositorio abierto en su carpeta raíz:

```text
Lee completos los cuatro archivos Markdown de la carpeta GUIA antes de tocar el código:
01_ARQUITECTURA_Y_ALCANCE.md
02_BACKEND_FASTAPI.md
03_FRONTEND_REACT.md
04_BASE_DE_DATOS_DESPLIEGUE_Y_COMMITS.md

El repositorio ya está conectado a GitHub y las carpetas backend/ y frontend/ ya existen. Primero inspecciona su contenido, el estado de Git, los entornos y las dependencias. No borres ni recrees lo que ya funciona. Respeta las decisiones y el alcance de las guías.

Trabajaremos por fases cortas. En esta primera ejecución realiza solamente la ETAPA 0 y la ETAPA 1 del flujo de commits: diagnostica la estructura real, adapta el plan si hay diferencias, implementa el esqueleto mínimo de FastAPI con configuración por entorno, CORS y endpoint /health, ejecuta las pruebas/build que correspondan y revisa git diff.

Prepara un único commit local de esa etapa con el mensaje sugerido en la guía. No hagas push. Al terminar, detente y entrega un informe con: diagnóstico del repositorio, archivos creados/modificados, decisiones tomadas, comandos ejecutados, pruebas y resultados, hash del commit y pasos manuales que debo verificar. Espera mi aprobación antes de continuar a la siguiente etapa.

No inventes credenciales ni escribas secretos. Cuando necesites Supabase, Gemini, Render o Vercel, indícame exactamente qué debo crear/copiar y en qué variable se configura. No uses servicios de pago ni actives facturación.
```

---

**Principio rector:** el éxito del MVP no es tener muchas tecnologías instaladas. Es que un docente pueda cargar una guía, que sus fragmentos queden guardados en Supabase y que un estudiante pueda recibir una explicación matemática clara y bien presentada sobre ese material.
