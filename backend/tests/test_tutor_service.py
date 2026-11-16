from types import SimpleNamespace
from uuid import uuid4

from app.core.config import Settings
from app.schemas.chat import ChatSource
from app.services import tutor_service
from app.services.retrieval_service import RetrievedChunk


class CaptureProvider:
    def __init__(self) -> None:
        self.system_instruction: str | None = None
        self.contents: str | None = None

    def generate(self, *, system_instruction: str, contents: str) -> str:
        self.system_instruction = system_instruction
        self.contents = contents
        return "Respuesta de prueba"


def test_full_chunk_content_and_source_metadata_reach_provider(monkeypatch) -> None:
    chunk_texts = [
        "EJERCICIO ORIGINAL: Factorice 12x² + 18x. Respuesta indicada: 6x(2x + 3).",
        "EJERCICIO ORIGINAL: Resuelva 3x - 7 = 11 y compruebe el resultado.",
    ]
    chunks = [RetrievedChunk("2 Evaluación final Tercer Trimestre", index, text) for index, text in enumerate(chunk_texts, 2)]
    course = SimpleNamespace(
        title="Factor común", subject="Matemáticas", grade_level="Octavo", topics=["Factorización"]
    )
    monkeypatch.setattr(tutor_service, "get_active_course", lambda db, course_id: course)
    monkeypatch.setattr(tutor_service, "retrieve_course_chunks", lambda *args, **kwargs: chunks)
    provider = CaptureProvider()

    answer, sources = tutor_service.answer_course_question(
        object(),
        Settings(),
        provider,
        course_id=uuid4(),
        message="¿Qué ejercicio aparece en la evaluación?",
        history=[],
    )

    assert answer == "Respuesta de prueba"
    assert provider.contents is not None
    for index, chunk_text in enumerate(chunk_texts, 2):
        assert chunk_text in provider.contents
        assert f"[Documento: 2 Evaluación final Tercer Trimestre; fragmento: {index}]" in provider.contents
    assert sources == [ChatSource(document_title=chunk.document_title, chunk_index=chunk.chunk_index) for chunk in chunks]


def test_material_question_without_chunks_asks_for_clarification_without_calling_model(monkeypatch) -> None:
    course = SimpleNamespace(title="Factor común", subject="Matemáticas", grade_level="Octavo", topics=[])
    monkeypatch.setattr(tutor_service, "get_active_course", lambda db, course_id: course)
    monkeypatch.setattr(tutor_service, "retrieve_course_chunks", lambda *args, **kwargs: [])
    provider = CaptureProvider()

    answer, sources = tutor_service.answer_course_question(
        object(),
        Settings(),
        provider,
        course_id=uuid4(),
        message="¿Qué temas aparecen en mi evaluación?",
        history=[],
    )

    assert "No encuentro esa información" in answer
    assert "¿Puedes indicar la página" in answer
    assert sources == []
    assert provider.contents is None


def test_prompt_requires_document_evidence_and_forbids_inventing_exam_topics() -> None:
    prompt = tutor_service.SYSTEM_INSTRUCTION.casefold()
    assert "fuente de referencia" in prompt
    assert "aparezca explícitamente" in prompt
    assert "no completes vacíos" in prompt
    assert "solicita la página" in prompt
