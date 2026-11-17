from app.core.config import Settings
from app.providers.base import TutorProviderError


class OpenAIProvider:
    provider_name = "openai"

    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key or not settings.openai_model:
            raise TutorProviderError("OpenAI requiere API key y modelo.", status_code=503, retryable=False, category="configuration")
        try:
            from openai import AsyncOpenAI
        except ImportError:
            raise TutorProviderError("Falta instalar el SDK oficial de OpenAI.", status_code=503, retryable=False, category="configuration") from None
        self.client = AsyncOpenAI(api_key=settings.openai_api_key, timeout=settings.openai_timeout_seconds, max_retries=0)
        self.model = settings.openai_model

    async def generate(self, *, system_instruction: str, contents: str) -> str:
        try:
            result = await self.client.responses.create(model=self.model, instructions=system_instruction,
                                                        input=contents, max_output_tokens=1200)
        except Exception as error:
            self._raise_error(error)
        answer = result.output_text
        if not answer or not answer.strip():
            raise TutorProviderError("OpenAI no generó una respuesta.", category="unavailable")
        return answer.strip()

    @staticmethod
    def _raise_error(error: Exception) -> None:
        try:
            from openai import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, RateLimitError
            if isinstance(error, (APITimeoutError,)):
                raise TutorProviderError("OpenAI agotó el tiempo de espera.", status_code=504, category="timeout") from None
            if isinstance(error, APIConnectionError):
                raise TutorProviderError("No se pudo conectar con OpenAI.", status_code=503, category="unavailable") from None
            if isinstance(error, AuthenticationError):
                raise TutorProviderError("La autenticación de OpenAI no es válida.", status_code=503, retryable=False, category="authentication") from None
            if isinstance(error, RateLimitError):
                raise TutorProviderError("OpenAI alcanzó un límite de uso.", status_code=429, category="quota") from None
            if isinstance(error, APIStatusError):
                category = "unavailable" if error.status_code >= 500 else "configuration"
                raise TutorProviderError(f"OpenAI respondió con HTTP {error.status_code}.", status_code=error.status_code, category=category) from None
        except ImportError:
            pass
        raise TutorProviderError("No se pudo completar la solicitud con OpenAI.", status_code=502, category="unavailable") from None

    async def close(self) -> None:
        await self.client.close()
