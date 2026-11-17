import asyncio
import sys
from types import ModuleType, SimpleNamespace

import pytest

from app.core.config import Settings
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.base import TutorProviderError
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.providers.openai_provider import OpenAIProvider


def test_openai_async_adapter_passes_same_instructions_and_rag_context(monkeypatch):
    captured = {}
    class FakeClient:
        def __init__(self, **kwargs): captured["client"] = kwargs; self.responses = self
        async def create(self, **kwargs): captured.update(kwargs); return SimpleNamespace(output_text="respuesta OpenAI")
        async def close(self): pass
    module = ModuleType("openai"); module.AsyncOpenAI = FakeClient
    monkeypatch.setitem(sys.modules, "openai", module)
    provider = OpenAIProvider(Settings(openai_api_key="mock", openai_model="configured-model"))
    context = "CONTENIDO REAL DEL CHUNK 12x² + 18x"; instruction = "Instrucciones pedagógicas exactas"
    assert asyncio.run(provider.generate(system_instruction=instruction, contents=context)) == "respuesta OpenAI"
    assert captured["instructions"] == instruction and captured["input"] == context
    assert captured["model"] == "configured-model" and captured["client"]["max_retries"] == 0


def test_anthropic_async_adapter_passes_same_instructions_and_rag_context(monkeypatch):
    captured = {}
    class FakeClient:
        def __init__(self, **kwargs): captured["client"] = kwargs; self.messages = self
        async def create(self, **kwargs): captured.update(kwargs); return SimpleNamespace(content=[SimpleNamespace(type="text", text="respuesta Claude")])
        async def close(self): pass
    module = ModuleType("anthropic"); module.AsyncAnthropic = FakeClient
    monkeypatch.setitem(sys.modules, "anthropic", module)
    provider = AnthropicProvider(Settings(anthropic_api_key="mock", anthropic_model="configured-model"))
    context = "CONTENIDO REAL DEL CHUNK 12x² + 18x"; instruction = "Instrucciones pedagógicas exactas"
    assert asyncio.run(provider.generate(system_instruction=instruction, contents=context)) == "respuesta Claude"
    assert captured["system"] == instruction and captured["messages"][0]["content"] == context
    assert captured["model"] == "configured-model" and captured["client"]["max_retries"] == 0


def test_groq_async_adapter_receives_identical_instruction_and_chunk(monkeypatch):
    captured = {}
    class FakeClient:
        def __init__(self, **kwargs): self.chat = SimpleNamespace(completions=self)
        async def create(self, **kwargs): captured.update(kwargs); return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Groq"))])
        async def close(self): pass
    module = ModuleType("groq"); module.AsyncGroq = FakeClient
    monkeypatch.setitem(sys.modules, "groq", module)
    provider = GroqProvider(Settings(groq_api_key="mock"))
    assert asyncio.run(provider.generate(system_instruction="REGLAS", contents="CHUNK ENTERO")) == "Groq"
    assert captured["messages"] == [{"role": "system", "content": "REGLAS"}, {"role": "user", "content": "CHUNK ENTERO"}]


def test_gemini_async_adapter_receives_full_context_and_instruction(monkeypatch):
    captured = {}
    class Model:
        async def generate_content(self, **kwargs): captured.update(kwargs); return SimpleNamespace(text="Gemini")
    class Aio:
        models = Model()
        async def aclose(self): pass
    fake = ModuleType("google.genai")
    fake.Client = lambda **kwargs: SimpleNamespace(aio=Aio())
    fake.errors = SimpleNamespace(APIError=type("FakeAPIError", (Exception,), {}))
    fake.types = SimpleNamespace(HttpOptions=lambda **kwargs: kwargs, HttpRetryOptions=lambda **kwargs: kwargs,
        GenerateContentConfig=lambda **kwargs: SimpleNamespace(**kwargs))
    google = ModuleType("google"); google.__path__ = []; google.genai = fake
    monkeypatch.setitem(sys.modules, "google", google); monkeypatch.setitem(sys.modules, "google.genai", fake)
    provider = GeminiProvider(Settings(gemini_api_key="mock"))
    assert asyncio.run(provider.generate(system_instruction="REGLAS", contents="CHUNK ENTERO")) == "Gemini"
    assert captured["contents"] == "CHUNK ENTERO" and captured["config"].system_instruction == "REGLAS"
    assert captured["config"].system_instruction == "REGLAS"


def test_openai_missing_credentials_does_not_import_sdk():
    with pytest.raises(TutorProviderError) as error:
        OpenAIProvider(Settings())
    assert error.value.category == "configuration"
