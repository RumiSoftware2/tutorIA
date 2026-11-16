import logging

from app.core.config import Settings
from app.providers.base import TutorProviderError

logger = logging.getLogger(__name__)


class GroqProvider:
    provider_name = "groq"

    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise TutorProviderError("El proveedor Groq no está configurado.", status_code=503, retryable=False)
        try:
            from groq import Groq
        except ImportError:
            raise TutorProviderError("La dependencia del proveedor Groq no está instalada.", status_code=503, retryable=False) from None
        self.client = Groq(api_key=settings.groq_api_key, timeout=60.0)
        self.model = settings.groq_model

    def generate(self, *, system_instruction: str, contents: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": (
                            f"Instrucciones pedagógicas del tutor:\n{system_instruction}\n\n"
                            f"Contexto documental, curso e historial:\n{contents}"
                        ),
                    },
                ],
                temperature=0.5,
                max_completion_tokens=1200,
            )
        except Exception as error:
            try:
                from groq import APIConnectionError, APIStatusError
            except ImportError:
                raise TutorProviderError("No se pudo completar la solicitud al proveedor Groq.", status_code=502) from None
            if isinstance(error, APIConnectionError):
                logger.warning("No se pudo conectar con Groq (error de conexión %s).", type(error).__name__)
                raise TutorProviderError("No se pudo conectar con Groq.", status_code=503) from None
            if isinstance(error, APIStatusError):
                logger.warning("Groq API respondió con código HTTP %s.", error.status_code)
                if error.status_code == 429:
                    raise TutorProviderError("Groq alcanzó su límite temporal.", status_code=429) from None
                if error.status_code >= 500:
                    raise TutorProviderError("Groq no está disponible temporalmente.", status_code=502) from None
                raise TutorProviderError("La configuración de Groq no es válida.", status_code=503, retryable=False) from None
            logger.warning(
                "Error SDK/proveedor Groq: %s.%s.",
                type(error).__module__,
                type(error).__name__,
            )
            raise TutorProviderError("No se pudo obtener una respuesta de Groq.", status_code=502) from None

        answer = response.choices[0].message.content if response.choices else None
        if not answer or not answer.strip():
            raise TutorProviderError("Groq no generó una respuesta.", status_code=502)
        return answer.strip()
