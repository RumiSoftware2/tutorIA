from app.core.config import Settings
from app.providers.base import TutorProviderError


class AnthropicProvider:
    provider_name = "anthropic"

    def __init__(self, settings: Settings) -> None:
        if not settings.anthropic_api_key or not settings.anthropic_model:
            raise TutorProviderError("Claude requiere API key y modelo.", status_code=503, retryable=False, category="configuration")
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise TutorProviderError("Falta instalar el SDK oficial de Anthropic.", status_code=503, retryable=False, category="configuration") from None
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key, timeout=settings.anthropic_timeout_seconds, max_retries=0)
        self.model = settings.anthropic_model

    async def generate(self, *, system_instruction: str, contents: str) -> str:
        try:
            result = await self.client.messages.create(model=self.model, system=system_instruction,
                messages=[{"role": "user", "content": contents}], max_tokens=1200)
        except Exception as error:
            self._raise_error(error)
        answer = "\n".join(block.text for block in result.content if getattr(block, "type", None) == "text")
        if not answer.strip():
            raise TutorProviderError("Claude no generó una respuesta.", category="unavailable")
        return answer.strip()

    @staticmethod
    def _raise_error(error: Exception) -> None:
        try:
            from anthropic import APIConnectionError, APIStatusError, APITimeoutError, AuthenticationError, RateLimitError
            if isinstance(error, APITimeoutError):
                raise TutorProviderError("Claude agotó el tiempo de espera.", status_code=504, category="timeout") from None
            if isinstance(error, APIConnectionError):
                raise TutorProviderError("No se pudo conectar con Claude.", status_code=503, category="unavailable") from None
            if isinstance(error, AuthenticationError):
                raise TutorProviderError("La autenticación de Claude no es válida.", status_code=503, retryable=False, category="authentication") from None
            if isinstance(error, RateLimitError):
                raise TutorProviderError("Claude alcanzó un límite de uso.", status_code=429, category="quota") from None
            if isinstance(error, APIStatusError):
                category = "unavailable" if error.status_code >= 500 else "configuration"
                raise TutorProviderError(f"Claude respondió con HTTP {error.status_code}.", status_code=error.status_code, category=category) from None
        except ImportError:
            pass
        raise TutorProviderError("No se pudo completar la solicitud con Claude.", status_code=502, category="unavailable") from None

    async def close(self) -> None:
        await self.client.close()
