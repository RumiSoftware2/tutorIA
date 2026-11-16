import logging
from collections.abc import Callable

from app.core.config import Settings
from app.providers.base import TutorProvider, TutorProviderError

logger = logging.getLogger(__name__)


class FallbackTutorProvider:
    """Try Gemini first, then Groq only for transient Gemini failures."""

    def __init__(
        self,
        primary_factory: Callable[[], TutorProvider],
        fallback_factory: Callable[[], TutorProvider] | None = None,
    ) -> None:
        self.primary_factory = primary_factory
        self.fallback_factory = fallback_factory
        self.provider_used: str | None = None

    def generate(self, *, system_instruction: str, contents: str) -> str:
        primary_status: int
        try:
            answer = self.primary_factory().generate(system_instruction=system_instruction, contents=contents)
            self.provider_used = "gemini"
            return answer
        except TutorProviderError as primary_error:
            if not primary_error.retryable or self.fallback_factory is None:
                raise
            primary_status = primary_error.status_code
            logger.warning(
                "Gemini falló temporalmente (HTTP %s); se intentará Groq.",
                primary_status,
            )

        try:
            answer = self.fallback_factory().generate(system_instruction=system_instruction, contents=contents)
            self.provider_used = "groq"
            return answer
        except TutorProviderError as fallback_error:
            logger.error(
                "Fallaron ambos proveedores (Gemini HTTP %s, Groq HTTP %s).",
                primary_status,
                fallback_error.status_code,
            )
            raise TutorProviderError(
                "Ambos proveedores (Gemini y Groq) no pudieron completar la solicitud. Inténtalo de nuevo más tarde.",
                status_code=503,
            ) from None


def build_tutor_provider(settings: Settings) -> FallbackTutorProvider:
    # Import lazily so the API can still start when an optional provider is disabled.
    from app.providers.gemini_provider import GeminiProvider

    fallback_factory = None
    if settings.groq_enabled:
        from app.providers.groq_provider import GroqProvider

        fallback_factory = lambda: GroqProvider(settings)
    return FallbackTutorProvider(
        primary_factory=lambda: GeminiProvider(settings),
        fallback_factory=fallback_factory,
    )
