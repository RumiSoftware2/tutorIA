import logging

from app.core.config import Settings
from app.providers.base import TutorProviderError

logger = logging.getLogger(__name__)


def _provider_error_for_api_code(code: int) -> TutorProviderError:
    if code == 429:
        return TutorProviderError("El tutor alcanzó su límite temporal. Inténtalo más tarde.", status_code=429)
    if code in (401, 403):
        return TutorProviderError("La configuración del tutor no es válida.", status_code=503, retryable=False)
    if code in (400, 404):
        return TutorProviderError(
            f"Gemini rechazó la configuración o la solicitud (código {code}). Revisa GEMINI_MODEL y el acceso de la clave a Gemini API.",
            status_code=503,
            retryable=False,
        )
    if code in (408, 504):
        return TutorProviderError("El tutor tardó demasiado en responder. Inténtalo de nuevo.", status_code=503)
    if code in (500, 502, 503):
        return TutorProviderError(
            f"Gemini está temporalmente no disponible (HTTP {code}). Espera un minuto y vuelve a intentarlo.",
            status_code=503,
        )
    return TutorProviderError(
        f"Gemini respondió con el código HTTP {code}. Revisa la terminal de Uvicorn para el diagnóstico.",
        status_code=502,
    )


class GeminiProvider:
    def __init__(self, settings: Settings) -> None:
        if not settings.gemini_api_key:
            raise TutorProviderError("El tutor no está configurado.", status_code=503, retryable=False)
        try:
            from google import genai
            from google.genai import errors, types
        except ImportError:
            raise TutorProviderError("La dependencia del proveedor Gemini no está instalada.", status_code=503, retryable=False) from None
        self.client = genai.Client(
            api_key=settings.gemini_api_key,
            # Gemini can take longer on larger grounded prompts; 20 seconds
            # caused unnecessary 503s for otherwise successful requests.
            http_options=types.HttpOptions(timeout=60_000),
        )
        self.model = settings.gemini_model
        self._api_errors = errors
        self._types = types

    def generate(self, *, system_instruction: str, contents: str) -> str:
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=self._types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.4,
                    max_output_tokens=1200,
                ),
            )
        except self._api_errors.APIError as error:
            logger.warning("Gemini API respondió con código HTTP %s.", error.code)
            # Keep provider messages and request details private.
            raise _provider_error_for_api_code(error.code) from None
        except Exception as error:
            error_type = f"{type(error).__module__}.{type(error).__name__}"
            logger.warning("Error de transporte/proveedor Gemini: %s.", error_type)
            if error_type.endswith("ConnectError"):
                raise TutorProviderError(
                    "No se pudo conectar con Google Gemini. Revisa la conexión a internet, DNS o el firewall del equipo.",
                    status_code=503,
                ) from None
            if error_type.endswith(("TimeoutException", "ReadTimeout", "ConnectTimeout")):
                raise TutorProviderError("La conexión con Gemini agotó el tiempo de espera. Inténtalo de nuevo.", status_code=503) from None
            raise TutorProviderError("No se pudo obtener una respuesta del tutor.", status_code=502) from None
        answer = response.text
        if not answer or not answer.strip():
            raise TutorProviderError("El tutor no generó una respuesta. Inténtalo de nuevo.", status_code=502)
        return answer.strip()
