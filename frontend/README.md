# AulaMate — frontend

Interfaz React + Vite en español. La primera entrega muestra la galería de cursos activos desde la API y permite abrir una ficha de curso.

## Ejecutar en local (PowerShell)

```powershell
cd frontend
npm install
Copy-Item .env.example .env
npm run dev
```

Vite inicia normalmente en `http://localhost:5173`. La API base se configura con `VITE_API_URL` en `.env`; por defecto es `http://localhost:8000/api/v1`. El backend debe estar iniciado para cargar cursos reales.

## Comprobaciones

```powershell
npm run build
npm run lint
```

Esta etapa implementa la galería, sus estados de carga/error/vacío, la ficha del curso y el selector de modo. El acceso docente y el chat se conectarán en sus siguientes etapas.
