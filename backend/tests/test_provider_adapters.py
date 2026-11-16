import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.core.config import Settings
from app.providers.base import TutorProviderError
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider


def test_gemini_sdk_receives_full_chunk_context_and_system_instruction(monkeypatch) -> None:
    captured: dict = {}

    class FakeModel:
        def generate_content(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(text="Respuesta Gemini")

    fake_genai = ModuleType("google.genai")
    fake_genai.Client = lambda **kwargs: SimpleNamespace(models=FakeModel())
    fake_genai.errors = SimpleNamespace(APIError=type("FakeAPIError", (Exception,), {}))
    fake_genai.types = SimpleNamespace(
        HttpOptions=lambda **kwargs: SimpleNamespace(**kwargs),
        GenerateContentConfig=lambda **kwargs: SimpleNamespace(**kwargs),
    )
    fake_google = ModuleType("google")
    fake_google.__path__ = []
    fake_google.genai = fake_genai
    monkeypatch.setitem(sys.modules, "google", fake_google)
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)

    provider = GeminiProvider(Settings(gemini_api_key="test-key"))
    context = "[Documento: Evaluación; fragmento: 3]\nCONTENIDO REAL: Factorice 12x² + 18x."
    instructions = "Responde solo con evidencia documental y pide aclaración si falta."
    assert provider.generate(system_instruction=instructions, contents=context) == "Respuesta Gemini"

    assert captured["contents"] == context
    assert captured["config"].system_instruction == instructions


def test_groq_sdk_receives_same_instructions_and_full_chunk_context(monkeypatch) -> None:
    captured: dict = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Respuesta Groq"))])

    class FakeGroqClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=FakeCompletions())

    fake_groq = ModuleType("groq")
    fake_groq.Groq = FakeGroqClient
    monkeypatch.setitem(sys.modules, "groq", fake_groq)

    provider = GroqProvider(Settings(groq_api_key="test-key"))
    context = "[Documento: Evaluación; fragmento: 3]\nCONTENIDO REAL: Factorice 12x² + 18x."
    instructions = "Responde solo con evidencia documental y pide aclaración si falta."
    assert provider.generate(system_instruction=instructions, contents=context) == "Respuesta Groq"

    sent_message = captured["messages"][0]["content"]
    assert instructions in sent_message
    assert context in sent_message
    assert captured["model"] == "openai/gpt-oss-20b"


def test_groq_http_failure_logs_status_without_exposing_error_body(monkeypatch, caplog) -> None:
    private_error_text = "private-provider-error-text"

    class FakeAPIStatusError(Exception):
        status_code = 502

    class FakeCompletions:
        def create(self, **kwargs):
            raise FakeAPIStatusError(private_error_text)

    class FakeGroqClient:
        def __init__(self, **kwargs):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=FakeCompletions().create))

    fake_groq = ModuleType("groq")
    fake_groq.Groq = FakeGroqClient
    fake_groq.APIConnectionError = type("APIConnectionError", (Exception,), {})
    fake_groq.APIStatusError = FakeAPIStatusError
    monkeypatch.setitem(sys.modules, "groq", fake_groq)
    provider = GroqProvider(Settings(groq_api_key="test-key"))

    with pytest.raises(TutorProviderError) as exc_info:
        provider.generate(system_instruction="I", contents="C")

    assert exc_info.value.status_code == 502
    assert "código HTTP 502" in caplog.text
    assert private_error_text not in caplog.text
    assert private_error_text not in str(exc_info.value)
