import logging

from app.core.config import Settings
from app.providers.base import TutorProviderError

logger = logging.getLogger(__name__)


def _provider_error_for_api_code(code: int) -> TutorProviderError:
    category = "quota" if code == 429 else "authentication" if code in (401, 403) else "configuration" if code in (400, 404) else "timeout" if code in (408, 504) else "unavailable"
    return TutorProviderError(
        f"Gemini está temporalmente no disponible (HTTP {code}). Espera un minuto y vuelve a intentarlo."
        if code in (500, 502, 503) else f"Gemini respondió con código HTTP {code}.",
        status_code=code, category=category, retryable=category in ("quota", "timeout", "unavailable"),
    )


class GeminiProvider:
    provider_name = "gemini"

    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key:
            raise TutorProviderError("Gemini no está configurado.", status_code=503, retryable=False, category="configuration")
        try:
            from google import genai
            from google.genai import errors, types
        except ImportError:
            raise TutorProviderError("Falta instalar el SDK de Gemini.", status_code=503, retryable=False, category="configuration") from None
        self.client = genai.Client(api_key=settings.gemini_api_key, http_options=types.HttpOptions(
            timeout=int(settings.gemini_timeout_seconds * 1000), retry_options=types.HttpRetryOptions(attempts=1)))
        self.model = settings.gemini_model
        self._api_errors = errors
        self._types = types

    async def generate(self, *, system_instruction: str, contents: str) -> str:
        try:
            response = await self.client.aio.models.generate_content(model=self.model, contents=contents,
                config=self._types.GenerateContentConfig(system_instruction=system_instruction, temperature=0.4,
                                                         max_output_tokens=1200))
        except self._api_errors.APIError as error:
            code = error.code
            category = "quota" if code == 429 else "authentication" if code in (401, 403) else "configuration" if code in (400, 404) else "timeout" if code in (408, 504) else "unavailable"
            logger.warning("Gemini respondió con HTTP %s.", code)
            raise TutorProviderError(f"Gemini respondió con HTTP {code}.", status_code=code, category=category,
                                     retryable=category in ("quota", "timeout", "unavailable")) from None
        except Exception as error:
            logger.warning("Error de transporte Gemini: tipo=%s", type(error).__name__)
            raise TutorProviderError("Gemini no pudo completar la solicitud.", status_code=503,
                                     category="timeout" if "timeout" in type(error).__name__.lower() else "unavailable") from None
        answer = response.text
        if not answer or not answer.strip():
            raise TutorProviderError("Gemini no generó una respuesta.", status_code=502)
        return answer.strip()

    async def close(self) -> None:
        close = getattr(self.client.aio, "aclose", None)
        if close:
            await close()
