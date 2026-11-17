import asyncio
import logging
import time
from collections.abc import Callable

from app.core.config import Settings
from app.providers.base import TutorProvider, TutorProviderError

logger = logging.getLogger(__name__)
PRIORITY = ("openai", "anthropic", "groq", "gemini")
LABELS = {"openai": "OpenAI", "anthropic": "Claude", "groq": "Groq", "gemini": "Gemini"}


def _provider_factories(settings: Settings) -> dict[str, Callable[[], TutorProvider]]:
    factories: dict[str, Callable[[], TutorProvider]] = {}
    if settings.openai_api_key and settings.openai_model:
        from app.providers.openai_provider import OpenAIProvider
        factories["openai"] = lambda: OpenAIProvider(settings)
    if settings.anthropic_api_key and settings.anthropic_model:
        from app.providers.anthropic_provider import AnthropicProvider
        factories["anthropic"] = lambda: AnthropicProvider(settings)
    if settings.groq_enabled and settings.groq_api_key:
        from app.providers.groq_provider import GroqProvider
        factories["groq"] = lambda: GroqProvider(settings)
    if settings.gemini_api_key:
        from app.providers.gemini_provider import GeminiProvider
        factories["gemini"] = lambda: GeminiProvider(settings)
    return factories


class TutorProviderManager:
    """Shared async provider clients, bounded fallback and non-probing status."""

    def __init__(self, settings: Settings, providers: dict[str, TutorProvider] | None = None):
        self.settings = settings
        self._initialization_errors: dict[str, str] = {}
        self.providers = providers if providers is not None else {}
        if providers is None:
            for name, factory in _provider_factories(settings).items():
                try:
                    self.providers[name] = factory()
                except TutorProviderError as error:
                    self._initialization_errors[name] = error.category
                    logger.error("No se inicializó el proveedor: proveedor=%s categoría=%s", name, error.category)
        self._unavailable_until: dict[str, float] = {}
        self._last_category: dict[str, str] = {}
        self._verified_available: set[str] = set()

    def availability(self) -> list[dict[str, object]]:
        result = []
        for name in PRIORITY:
            configured = name in self.providers
            cooling_down = self._unavailable_until.get(name, 0) > time.monotonic()
            configuration_problem = name in self._initialization_errors or self._last_category.get(name) in {"authentication", "configuration"}
            if configuration_problem:
                state, message = "requires_configuration", "Revisa la clave, el modelo y la configuración de este proveedor en el backend."
            elif not configured:
                state, message = "requires_configuration", "Requiere configuración en el backend."
            elif cooling_down:
                state, message = "temporarily_unavailable", "Falló recientemente; se volverá a intentar después del periodo de espera."
            elif name in self._verified_available:
                state, message = "available", "Respondió correctamente en una consulta reciente."
            else:
                state, message = "configured", "Tiene configuración; aún no se ha comprobado el servicio con una consulta."
            result.append({"provider": name, "display_name": LABELS[name], "status": state,
                           "message": message, "availability_verified": name in self._verified_available})
        return result

    async def generate(self, *, system_instruction: str, contents: str, preferred: str | None = None) -> tuple[str, str]:
        order = ([preferred] if preferred else []) + [name for name in PRIORITY if name != preferred]
        candidates = [
            name for name in order
            if name in self.providers
            and (name == preferred or self._unavailable_until.get(name, 0) <= time.monotonic())
        ]
        if not candidates:
            if not self.providers:
                raise TutorProviderError("No hay proveedores de IA configurados.", status_code=503, retryable=False,
                                         category="configuration")
            raise TutorProviderError("Los proveedores configurados están temporalmente no disponibles.",
                                     status_code=503, category="unavailable")
        failures = []
        deadline = time.monotonic() + self.settings.provider_fallback_total_timeout_seconds
        for name in candidates:
            provider = self.providers[name]
            timeout = min(getattr(self.settings, f"{name}_timeout_seconds", 30), deadline - time.monotonic())
            if timeout <= 0:
                break
            started = time.perf_counter()
            try:
                answer = await asyncio.wait_for(
                    provider.generate(system_instruction=system_instruction, contents=contents), timeout=timeout
                )
                elapsed_ms = (time.perf_counter() - started) * 1000
                self._unavailable_until.pop(name, None)
                self._last_category.pop(name, None)
                self._verified_available.add(name)
                logger.info("Proveedor IA respondió: proveedor=%s duración_ms=%.1f", name, elapsed_ms)
                return answer, name
            except asyncio.TimeoutError:
                error = TutorProviderError("Tiempo de espera agotado.", status_code=504, category="timeout")
            except TutorProviderError as caught:
                error = caught
            except Exception as caught:
                logger.warning("Error no controlado del adaptador proveedor=%s tipo=%s", name, type(caught).__name__)
                error = TutorProviderError("Error del proveedor.", status_code=502, category="unavailable")
            elapsed_ms = (time.perf_counter() - started) * 1000
            self._last_category[name] = error.category
            self._verified_available.discard(name)
            self._unavailable_until[name] = time.monotonic() + self.settings.provider_unavailable_cooldown_seconds
            logger.warning("Proveedor IA falló: proveedor=%s categoría=%s estado=%s duración_ms=%.1f",
                           name, error.category, error.status_code, elapsed_ms)
            failures.append((name, error))
        details = ", ".join(f"{name} ({error.category})" for name, error in failures)
        raise TutorProviderError(f"Los proveedores configurados no pudieron responder ({details}). Inténtalo más tarde.",
                                 status_code=503, category="unavailable") from None

    async def close(self) -> None:
        closers = [provider.close() for provider in self.providers.values() if hasattr(provider, "close")]
        await asyncio.gather(*closers, return_exceptions=True)


class FallbackTutorProvider:
    """Legacy synchronous Gemini/Groq wrapper retained for integrations importing it."""

    def __init__(self, primary_factory: Callable, fallback_factory: Callable | None = None) -> None:
        self.primary_factory = primary_factory
        self.fallback_factory = fallback_factory
        self.provider_used: str | None = None

    def generate(self, *, system_instruction: str, contents: str) -> str:
        try:
            answer = self.primary_factory().generate(system_instruction=system_instruction, contents=contents)
            self.provider_used = "gemini"
            return answer
        except TutorProviderError as error:
            if not error.retryable or self.fallback_factory is None:
                raise
        try:
            answer = self.fallback_factory().generate(system_instruction=system_instruction, contents=contents)
            self.provider_used = "groq"
            return answer
        except TutorProviderError:
            raise TutorProviderError("Ambos proveedores (Gemini y Groq) no pudieron completar la solicitud.", status_code=503) from None
