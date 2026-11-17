import asyncio

import pytest

from app.core.config import Settings
from app.providers.base import TutorProviderError
from app.providers.fallback import TutorProviderManager


class FakeProvider:
    def __init__(self, result):
        self.result = result
        self.calls = []

    async def generate(self, *, system_instruction, contents):
        self.calls.append((system_instruction, contents))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def test_requested_provider_is_first_and_falls_back_in_priority_order():
    openai = FakeProvider("OpenAI")
    claude = FakeProvider("Claude")
    groq = FakeProvider("Groq")
    gemini = FakeProvider("Gemini")
    providers = {"openai": openai, "anthropic": claude, "groq": groq, "gemini": gemini}
    manager = TutorProviderManager(Settings(), providers)

    answer, used = asyncio.run(manager.generate(system_instruction="pedagogía", contents="chunk real", preferred="groq"))

    assert (answer, used) == ("Groq", "groq")
    assert len(groq.calls) == 1 and not openai.calls and not claude.calls and not gemini.calls


def test_selected_failure_uses_general_order_without_repeating_provider():
    failed = FakeProvider(TutorProviderError("timeout", status_code=504, category="timeout"))
    openai = FakeProvider("respuesta")
    groq = FakeProvider("unused")
    manager = TutorProviderManager(Settings(), {"groq": groq, "gemini": failed, "openai": openai})

    answer, used = asyncio.run(manager.generate(system_instruction="I", contents="C", preferred="gemini"))

    assert (answer, used) == ("respuesta", "openai")
    assert not groq.calls
    assert failed.calls == [("I", "C")] and openai.calls == failed.calls


def test_all_providers_fail_with_controlled_response_and_status():
    manager = TutorProviderManager(Settings(), {
        "openai": FakeProvider(TutorProviderError("private", category="authentication")),
        "gemini": FakeProvider(TutorProviderError("private", category="unavailable")),
    })

    with pytest.raises(TutorProviderError) as error:
        asyncio.run(manager.generate(system_instruction="I", contents="C"))

    assert error.value.status_code == 503
    assert "authentication" in str(error.value) and "unavailable" in str(error.value)
    assert "private" not in str(error.value)
    assert manager.availability()[0]["status"] == "requires_configuration"
    assert manager.availability()[3]["status"] == "temporarily_unavailable"


def test_timeout_advances_fallback():
    async def timeout(*, system_instruction, contents):
        await asyncio.sleep(1.1)
    slow = FakeProvider("not used")
    slow.generate = timeout
    fast = FakeProvider("Groq response")
    settings = Settings(openai_timeout_seconds=1)
    manager = TutorProviderManager(settings, {"openai": slow, "groq": fast})

    answer, used = asyncio.run(manager.generate(system_instruction="I", contents="C"))

    assert (answer, used) == ("Groq response", "groq")


def test_provider_availability_does_not_claim_health_without_a_real_call():
    manager = TutorProviderManager(Settings(), {"groq": FakeProvider("ok")})
    statuses = manager.availability()
    assert [item["provider"] for item in statuses] == ["openai", "anthropic", "groq", "gemini"]
    assert statuses[0]["status"] == "requires_configuration"
    assert statuses[2]["status"] == "configured"
    assert statuses[2]["availability_verified"] is False
