import logging

from app.core.config import Settings
from app.providers.base import TutorProviderError

logger = logging.getLogger(__name__)


class GroqProvider:
    provider_name = "groq"

    def __init__(self, settings: Settings) -> None:
        if not settings.groq_api_key:
            raise TutorProviderError("Groq no está configurado.", status_code=503, retryable=False, category="configuration")
        try:
            from groq import AsyncGroq
        except ImportError:
            raise TutorProviderError("Falta instalar el SDK de Groq.", status_code=503, retryable=False, category="configuration") from None
        self.client = AsyncGroq(api_key=settings.groq_api_key, timeout=settings.groq_timeout_seconds, max_retries=0)
        self.model = settings.groq_model

    async def generate(self, *, system_instruction: str, contents: str) -> str:
        try:
            response = await self.client.chat.completions.create(model=self.model, messages=[
                {"role": "system", "content": system_instruction}, {"role": "user", "content": contents}],
                temperature=0.4, max_completion_tokens=1200)
        except Exception as error:
            try:
                from groq import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, RateLimitError
            except ImportError:
                raise TutorProviderError("No se pudo completar la solicitud con Groq.", status_code=502) from None
            if isinstance(error, (APITimeoutError,)):
                raise TutorProviderError("Groq agotó el tiempo de espera.", status_code=504, category="timeout") from None
            if isinstance(error, APIConnectionError):
                raise TutorProviderError("No se pudo conectar con Groq.", status_code=503, category="unavailable") from None
            if isinstance(error, AuthenticationError):
                raise TutorProviderError("La autenticación de Groq no es válida.", status_code=503, retryable=False, category="authentication") from None
            if isinstance(error, RateLimitError):
                raise TutorProviderError("Groq alcanzó un límite de uso.", status_code=429, category="quota") from None
            if isinstance(error, APIStatusError):
                logger.warning("Groq respondió con HTTP %s.", error.status_code)
                raise TutorProviderError(f"Groq respondió con HTTP {error.status_code}.", status_code=error.status_code,
                    category="unavailable" if error.status_code >= 500 else "configuration") from None
            logger.warning("Error del SDK Groq: tipo=%s", type(error).__name__)
            raise TutorProviderError("No se pudo obtener una respuesta de Groq.", status_code=502) from None
        answer = response.choices[0].message.content if response.choices else None
        if not answer or not answer.strip():
            raise TutorProviderError("Groq no generó una respuesta.", status_code=502)
        return answer.strip()

    async def close(self) -> None:
        await self.client.close()
