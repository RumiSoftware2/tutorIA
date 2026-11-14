# 03. Guía de implementación del frontend (React + Vite + CSS)

> Leer también `01_ARQUITECTURA_Y_ALCANCE.md` antes de implementar.

## 1. Objetivo

Construir dentro de `frontend/` una aplicación React responsive, en español, con una interfaz visual cálida y pedagógica. La aplicación permite alternar entre Estudiante y Docente. El estudiante ve una galería y conversa con un tutor de matemáticas; el docente se autentica con una clave y administra cursos y documentos.

El frontend no contiene lógica de negocio sensible. La seguridad, validación real y comunicación con Gemini pertenecen al backend.

## 2. Inspección inicial obligatoria

Antes de modificar:

1. Revisar la estructura de `frontend/` y el `package.json`.
2. Ejecutar `git status --short` desde la raíz.
3. Comprobar la versión instalada de Node y el gestor de paquetes ya usado (`npm`, `pnpm` o `yarn`).
4. Conservar el proyecto React existente si ya funciona.
5. No recrear Vite ni sobrescribir `package.json` si el ambiente ya está configurado correctamente.
6. Probar `npm run dev` y `npm run build` antes y después de las modificaciones cuando sea posible.

## 3. Stack y dependencias

- React con JavaScript.
- Vite.
- CSS puro, variables CSS y media queries.
- `react-markdown` para respuestas en Markdown.
- `remark-gfm` para tablas, listas y elementos GitHub Markdown.
- `remark-math` y `rehype-katex` para fórmulas.
- `katex` para estilos de notación matemática.

Instalar solo estas dependencias y las que ya tenga el proyecto. No añadir Tailwind, Bootstrap, Material UI, Ant Design ni otra librería visual.

No usar TypeScript si el proyecto actual es JavaScript. Respetar la tecnología que ya existe.

## 4. Estructura propuesta

Adaptarse al proyecto actual. Una opción compacta:

```text
frontend/
├── public/
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── styles/
│   │   ├── global.css
│   │   └── components.css
│   ├── services/
│   │   └── api.js
│   ├── context/              # Solo si compartir estado lo justifica
│   ├── components/
│   │   ├── RoleSwitcher.jsx
│   │   ├── CourseCard.jsx
│   │   ├── CourseGallery.jsx
│   │   ├── TeacherLoginModal.jsx
│   │   ├── CourseForm.jsx
│   │   ├── DocumentUploader.jsx
│   │   ├── DocumentList.jsx
│   │   ├── ChatWindow.jsx
│   │   ├── ChatMessage.jsx
│   │   ├── ChatInput.jsx
│   │   ├── MathMarkdown.jsx
│   │   ├── EmptyState.jsx
│   │   └── LoadingState.jsx
│   └── utils/
│       └── formatters.js
├── .env.example
├── .gitignore
└── package.json
```

No crear todos los componentes como archivos separados si eso produce abstracciones vacías. La prioridad es claridad, reutilización real y facilidad de lectura.

## 5. Lenguaje visual

### Estilo

- Educativo, amigable, moderno y tranquilo.
- Paleta pastel, con buen contraste y texto legible.
- Tarjetas limpias, esquinas redondeadas moderadas y sombras suaves.
- Botones claros, estados de carga visibles y mensajes de error amables.
- La interfaz debe dar sensación de acompañamiento, no de red social ni de panel empresarial complejo.

Paleta de referencia (puede ajustarse durante la implementación):

```css
:root {
  --color-bg: #f6f7fb;
  --color-surface: #ffffff;
  --color-primary: #6274d8;
  --color-primary-soft: #e4e9ff;
  --color-lavender: #eee8ff;
  --color-blue-soft: #e3f0ff;
  --color-mint: #e1f4e8;
  --color-peach: #fff0e5;
  --color-text: #27324a;
  --color-muted: #68748b;
  --color-border: #e4e8f0;
  --color-danger: #b94755;
  --radius-card: 18px;
  --shadow-card: 0 8px 24px rgba(45, 57, 90, 0.07);
}
```

No sacrificar contraste por usar tonos pastel. Texto principal oscuro, botones accesibles y foco visible.

## 6. Diseño de las vistas

### 6.1 Encabezado superior

En todas las vistas mostrar:

- Nombre temporal del producto, por ejemplo **AulaMate** o un nombre configurable visualmente. No inventar marca institucional ni logotipo oficial.
- Subtítulo pequeño: “Tu espacio para aprender matemáticas”.
- Selector de modo **Estudiante / Docente** en la parte superior.
- En móvil, el encabezado debe reorganizarse sin desbordarse.

Al iniciar, modo Estudiante. Cambiar a Docente debe abrir el formulario de acceso, no desbloquear el panel por un cambio de estado solamente.

### 6.2 Galería del estudiante

- Título: “¿Qué quieres aprender hoy?”.
- Texto breve invitando a escoger un curso.
- Tarjetas responsivas para cursos activos.
- Cada tarjeta muestra nombre, nivel/grado, descripción corta y hasta 3 temas como etiquetas.
- Botón o acción de tarjeta: “Entrar al curso”.
- Estado vacío si todavía no hay cursos: explicación sencilla de que el docente debe publicar material.
- Estado de carga tipo skeleton o indicador discreto.
- Error visible con botón de reintento.

Al escoger un curso, guardar el `courseId` en estado local y abrir la vista del chat. Incluir una acción clara para regresar a la galería.

### 6.3 Vista de chat

Debe sentirse como un espacio de aprendizaje con un profesor virtual:

- Encabezado del curso con nombre, nivel y temas.
- Mensaje inicial: el tutor se presenta y pregunta qué tema o ejercicio quiere trabajar el estudiante.
- Burbuja de estudiante diferenciada de la burbuja del tutor.
- Mensajes del tutor en Markdown y LaTeX.
- Referencias debajo de la respuesta, con el nombre del documento cuando el backend devuelva `sources`. No mostrar IDs internos.
- Caja de texto fija al pie, con botón de enviar.
- Envío con Enter y salto de línea con Shift+Enter, si es posible sin complicar accesibilidad.
- Desactivar el botón mientras se espera respuesta.
- Mostrar un estado de “El tutor está pensando...” y evitar respuestas duplicadas por doble clic.
- Mantener el scroll cerca del último mensaje al enviar/recibir.
- Mensajes de error amables cuando el servicio gratuito alcance su cuota o el backend esté dormido.
- Historial solo en memoria de la sesión actual. No escribirlo en localStorage ni en la base de datos.

No implementar streaming en esta fase: una respuesta JSON normal es suficiente para validar el flujo.

### 6.4 Acceso docente

Al seleccionar Docente sin token válido, mostrar un modal o pantalla compacta con:

- Título: “Acceso docente”.
- Campo de clave.
- Botón “Ingresar”.
- Botón para cancelar/regresar a Estudiante.
- Mensaje genérico si la clave no es válida.

Enviar la clave a `POST /api/v1/auth/teacher/login`. No guardar ni imprimir la clave. Al recibir el token, guardarlo en `sessionStorage`; borrar el token al cerrar sesión o cambiar a Estudiante.

El token no es equivalente a un sistema robusto de identidad. Es una barrera inicial para un prototipo.

### 6.5 Panel docente

El panel debe ofrecer dos secciones simples:

**Cursos**

- Listado de cursos existentes.
- Botón “Crear curso”.
- Formulario con título, descripción, nivel/grado y temas clave.
- Los temas se pueden introducir uno por línea o con un control simple de etiquetas. Elegir la solución más sencilla y usable.
- Editar los datos de un curso.
- Activar/desactivar publicación del curso.
- Validar campos obligatorios antes de enviar.

**Material de estudio**

- Seleccionar primero un curso.
- Carga de PDF, DOCX y PPTX.
- Permitir seleccionar un archivo, mostrar nombre y tamaño.
- Indicar el máximo permitido (10 MB inicial).
- Enviar `multipart/form-data`.
- Mostrar procesando/éxito/error.
- Listar documento, fecha, estado y número de fragmentos.
- Permitir eliminar un documento desde el panel, con confirmación.
- Mostrar aviso sobre PDFs escaneados: el OCR no está incluido.

No guardar el archivo original en el navegador ni intentar subir el archivo directamente a Supabase desde React.

## 7. LaTeX y contenido del tutor

Crear un componente reutilizable `MathMarkdown.jsx` para las respuestas.

Comportamiento esperado:

- Procesar Markdown con `react-markdown`.
- Habilitar `remark-gfm`.
- Habilitar matemáticas con `remark-math` y `rehype-katex`.
- Importar el CSS oficial de KaTeX, por ejemplo `katex/dist/katex.min.css`.
- Aceptar fórmulas en línea `$x^2$` y en bloque `$$x^2 + 2x + 1$$`.
- Manejar respuestas sin fórmulas sin romper el diseño.
- Mostrar tablas grandes con scroll horizontal en móvil.
- No renderizar HTML arbitrario proveniente del modelo. No habilitar `rehype-raw`.
- Si una fórmula está mal formada, evitar que se rompa todo el chat; mostrar una representación legible o manejar el error.

En las respuestas, preservar listas numeradas, negritas, tablas y bloques de código si se usan.

## 8. Servicio de API

Crear `src/services/api.js` como único punto de comunicación con backend.

Funciones orientativas:

- `getCourses()`
- `getCourse(courseId)`
- `teacherLogin(accessCode)`
- `createCourse(data, token)`
- `updateCourse(courseId, data, token)`
- `setCourseActive(courseId, isActive, token)`
- `getDocuments(courseId, token)`
- `uploadDocument(courseId, file, token)`
- `deleteDocument(documentId, token)`
- `sendChatMessage(payload)`

Configurar la URL base mediante `import.meta.env.VITE_API_URL`. No escribir la URL de producción en varios componentes.

El servicio debe:

- Añadir `Authorization: Bearer ...` solo en rutas docentes.
- No añadir manualmente `Content-Type: multipart/form-data` al cargar archivos: permitir que el navegador agregue el boundary.
- Parsear errores JSON y convertirlos en mensajes utilizables.
- Manejar respuestas no JSON o errores de red.
- Usar `fetch` o la librería HTTP que ya exista en el proyecto; no incorporar Axios sin necesidad.

Archivo `.env.example`:

```dotenv
VITE_API_URL=http://localhost:8000/api/v1
```

En Vercel, configurar la variable con la URL pública de Render más `/api/v1`. Las variables `VITE_` quedan incluidas en el bundle público; solamente colocar allí información que pueda ser visible en el navegador.

## 9. Estado de aplicación

Evitar instalar Redux o una librería global para este MVP.

Estado mínimo:

- `mode`: `student` o `teacher`.
- `teacherToken`: token temporal en sesión.
- `courses`: catálogo cargado.
- `selectedCourse`: curso abierto.
- `messages`: historial en memoria del chat.
- `isSending`, `isLoading`, `error`.

Se puede manejar con `useState` y componentes padre. Añadir Context solo cuando varias ramas necesiten compartir estado de forma real.

Al cambiar de curso, limpiar el historial del curso anterior. Al salir del modo docente, borrar el token de `sessionStorage` y volver al modo Estudiante.

## 10. Responsive y accesibilidad

### Breakpoints de referencia

- Móvil: hasta 640 px.
- Tableta: 641–1024 px.
- Escritorio: más de 1024 px.

No diseñar para un ancho fijo. Usar `minmax`, `flex-wrap`, `max-width`, `clamp()` y media queries.

### Accesibilidad mínima

- Formularios con `label` asociados.
- Botones con texto comprensible; no depender solo de iconos.
- Navegación con teclado.
- `:focus-visible` claro.
- Contraste suficiente.
- Errores anunciables y vinculados al campo cuando sea posible.
- Atributos `aria-label` para controles cuyo propósito no esté escrito.
- Áreas de toque cómodas en móvil.

## 11. Manejo de errores y estados

La interfaz debe contemplar explícitamente:

| Situación | Presentación |
|---|---|
| Catálogo vacío | Mensaje de bienvenida y explicación |
| API Render dormida | “El servidor está despertando; vuelve a intentarlo en unos segundos” sin prometer un tiempo fijo |
| Sin conexión | Mensaje de red y botón reintentar |
| Clave docente incorrecta | Mensaje genérico, sin detalles internos |
| Token vencido | Cerrar sesión docente y pedir acceso de nuevo |
| Archivo no permitido | Mostrar extensiones aceptadas |
| Archivo demasiado grande | Mostrar el límite configurado |
| PDF sin texto | Aviso de PDF escaneado/OCR no incluido |
| Gemini sin cuota | Mensaje temporal; no presentar un error técnico crudo |
| Respuesta vacía | Mensaje de recuperación, no burbuja vacía |

Nunca mostrar trazas, variables de entorno, contraseñas ni contenido completo de errores internos.

## 12. Pruebas y validación del frontend

Codex debe ejecutar como mínimo:

```bash
npm run dev
npm run build
```

Agregar pruebas automatizadas solo si el proyecto ya tiene una infraestructura de tests sencilla o si una parte crítica lo justifica. Para el MVP, una lista manual de aceptación también es obligatoria.

### Lista de aceptación manual

- [ ] En móvil, tableta y escritorio no hay scroll horizontal inesperado.
- [ ] El selector alterna a Estudiante sin pedir clave.
- [ ] El selector Docente solicita clave.
- [ ] Sin token no es posible completar acciones docentes.
- [ ] El estudiante ve la galería de cursos activos.
- [ ] Las tarjetas muestran descripción y temas.
- [ ] Abrir y cerrar un curso funciona.
- [ ] Enviar una pregunta muestra carga y una respuesta.
- [ ] Las expresiones LaTeX en línea y bloque se renderizan correctamente.
- [ ] El chat conserva el contexto durante la sesión y se reinicia al cambiar de curso.
- [ ] El docente puede crear y editar un curso.
- [ ] El docente puede seleccionar un curso y subir un PDF/DOCX/PPTX.
- [ ] El docente ve estado y número de fragmentos.
- [ ] Los errores de red, archivo y cuota se entienden.
- [ ] `npm run build` termina sin errores.

## 13. Criterios de diseño para no sobredimensionar

- No crear un sistema de diseño completo; definir unas pocas variables CSS y componentes reutilizables.
- No añadir animaciones complejas. Transiciones suaves de 150–220 ms son suficientes.
- No añadir música, videos, imágenes externas ni dependencias innecesarias.
- Priorizar legibilidad del contenido matemático sobre decoración.
- No agregar panel de administración avanzado, analítica ni perfiles estudiantiles.
- El foco visual es la galería y el chat, no una pantalla de métricas.

## 14. Criterios de aceptación del frontend

El frontend se considera integrado cuando consume la API real, no cuando funciona solo con datos ficticios. Los mocks pueden usarse temporalmente para diseñar, pero deben retirarse o quedar claramente aislados antes del commit de integración.
