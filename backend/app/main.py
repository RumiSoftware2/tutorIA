from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.api.routes.courses import router as courses_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Tutor Matemático IA API",
    description="API del tutor educativo de matemáticas.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(courses_router, prefix=settings.api_prefix)
