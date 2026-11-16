import pytest

from app.providers.base import TutorProviderError
from app.providers.fallback import FallbackTutorProvider


class FakeProvider:
    def __init__(self, result: str | Exception) -> None:
        self.result = result
        self.calls: list[tuple[str, str]] = []

    def generate(self, *, system_instruction: str, contents: str) -> str:
        self.calls.append((system_instruction, contents))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


@pytest.mark.parametrize("status_code", [429, 502, 503])
def test_transient_gemini_error_uses_groq_with_identical_prompt(status_code: int) -> None:
    gemini = FakeProvider(TutorProviderError("Gemini temporalmente no disponible", status_code=status_code))
    groq = FakeProvider("Respuesta desde Groq")
    chain = FallbackTutorProvider(lambda: gemini, lambda: groq)

    shared_instructions = "Responde solo con evidencia; pide aclaración si falta información."
    shared_context = (
        "<contexto_documental>\nEJERCICIO ORIGINAL: Factorice 12x² + 18x.\n"
        "</contexto_documental>\nPregunta: ¿Qué ejercicio aparece en la evaluación?"
    )
    answer = chain.generate(system_instruction=shared_instructions, contents=shared_context)

    assert answer == "Respuesta desde Groq"
    assert chain.provider_used == "groq"
    assert gemini.calls == [(shared_instructions, shared_context)]
    assert groq.calls == gemini.calls


def test_gemini_success_does_not_call_groq() -> None:
    gemini = FakeProvider("Respuesta desde Gemini")
    groq = FakeProvider("No debe ejecutarse")
    chain = FallbackTutorProvider(lambda: gemini, lambda: groq)

    assert chain.generate(system_instruction="I", contents="C") == "Respuesta desde Gemini"
    assert chain.provider_used == "gemini"
    assert len(groq.calls) == 0


def test_non_transient_gemini_error_does_not_call_groq() -> None:
    gemini = FakeProvider(TutorProviderError("Configuración inválida", status_code=503, retryable=False))
    groq = FakeProvider("No debe ejecutarse")
    chain = FallbackTutorProvider(lambda: gemini, lambda: groq)

    with pytest.raises(TutorProviderError, match="Configuración inválida"):
        chain.generate(system_instruction="I", contents="C")
    assert len(groq.calls) == 0


def test_both_providers_failing_returns_controlled_error() -> None:
    gemini = FakeProvider(TutorProviderError("Detalle privado de Gemini", status_code=503))
    groq = FakeProvider(TutorProviderError("Detalle privado de Groq", status_code=502))
    chain = FallbackTutorProvider(lambda: gemini, lambda: groq)

    with pytest.raises(TutorProviderError) as exc_info:
        chain.generate(system_instruction="I", contents="C")

    assert exc_info.value.status_code == 503
    assert "ambos proveedores" in str(exc_info.value).lower()
    assert "Detalle privado" not in str(exc_info.value)
