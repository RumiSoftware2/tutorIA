import pytest

from app.services.text_chunker import split_into_chunks


def test_chunker_returns_no_empty_chunks_for_empty_text() -> None:
    assert split_into_chunks("") == []
    assert split_into_chunks("  \r\n\t ") == []


def test_chunker_keeps_short_text_and_markdown_content() -> None:
    text = "# Fracciones\r\n\r\n- Numerador\r\n- Denominador\r\n\r\nLa fórmula es $a/b$."

    chunks = split_into_chunks(text)

    assert chunks == ["# Fracciones\n\n- Numerador\n- Denominador\n\nLa fórmula es $a/b$."]


def test_chunker_respects_size_and_overlaps_long_paragraphs() -> None:
    text = " ".join(f"palabra{i}" for i in range(300))

    chunks = split_into_chunks(text, chunk_size=240, overlap=50)

    assert len(chunks) > 1
    assert all(0 < len(chunk) <= 240 for chunk in chunks)
    assert all(chunks[index - 1][-25:] in chunks[index] for index in range(1, len(chunks)))


def test_chunker_prefers_paragraph_boundaries_and_validates_options() -> None:
    chunks = split_into_chunks("Primero.\n\nSegundo párrafo.", chunk_size=20, overlap=2)

    assert chunks == ["Primero.", "Segundo párrafo."]
    with pytest.raises(ValueError):
        split_into_chunks("texto", chunk_size=10, overlap=10)
