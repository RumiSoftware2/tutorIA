import io
import zipfile
from types import SimpleNamespace

import pytest

from app.services import document_converter
from app.services.document_converter import (
    DocumentTooLargeError,
    NoExtractableTextError,
    UnsupportedDocumentError,
    convert_to_markdown,
    validate_document_bytes,
)


def make_office_file(extension: str) -> bytes:
    if extension == "docx":
        main_part = "word/document.xml"
        content_type = b"application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"
    else:
        main_part = "ppt/presentation.xml"
        content_type = b"application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("[Content_Types].xml", b"<Types>" + content_type + b"</Types>")
        archive.writestr(main_part, b"<document/>")
    return buffer.getvalue()


def make_minimal_pdf() -> bytes:
    content = b"BT /F1 18 Tf 30 100 Td (Arithmetic guide 2 plus 2) Tj ET"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 144] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n" + content + b"\nendstream",
    ]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(offsets)}\n".encode())
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
    )
    return bytes(pdf)


def make_minimal_docx() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(
            "[Content_Types].xml",
            b'<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            b'<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            b'<Default Extension="xml" ContentType="application/xml"/>'
            b'<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            b"</Types>",
        )
        archive.writestr(
            "_rels/.rels",
            b'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            b'<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            b"</Relationships>",
        )
        archive.writestr(
            "word/document.xml",
            b'<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            b"<w:body><w:p><w:r><w:t>Algebra guide</w:t></w:r></w:p><w:sectPr/></w:body></w:document>",
        )
    return buffer.getvalue()


def make_minimal_pptx() -> bytes:
    from pptx import Presentation

    presentation = Presentation()
    slide = presentation.slides.add_slide(presentation.slide_layouts[6])
    text_box = slide.shapes.add_textbox(100, 100, 4_000_000, 500_000)
    text_box.text = "Geometry guide"
    buffer = io.BytesIO()
    presentation.save(buffer)
    return buffer.getvalue()


@pytest.mark.parametrize("extension", ["docx", "pptx"])
def test_office_container_is_validated(extension: str) -> None:
    assert validate_document_bytes(make_office_file(extension), extension, 1024 * 1024) == extension


def test_unsupported_extension_empty_and_mismatched_files_are_rejected() -> None:
    with pytest.raises(UnsupportedDocumentError):
        validate_document_bytes(b"content", "txt", 1024)
    with pytest.raises(NoExtractableTextError):
        validate_document_bytes(b"", "pdf", 1024)
    with pytest.raises(UnsupportedDocumentError):
        validate_document_bytes(b"not a pdf", "pdf", 1024)
    with pytest.raises(UnsupportedDocumentError):
        validate_document_bytes(b"not a zip", "docx", 1024)


def test_size_limit_is_enforced() -> None:
    with pytest.raises(DocumentTooLargeError):
        validate_document_bytes(b"%PDF-1.7" + b"x" * 20, "pdf", 10)


def test_converter_uses_stream_without_plugins_and_cleans_text(monkeypatch: pytest.MonkeyPatch) -> None:
    class StubMarkItDown:
        def __init__(self, *, enable_plugins: bool) -> None:
            assert enable_plugins is False

        def convert_stream(self, stream: io.BytesIO, *, stream_info: object) -> SimpleNamespace:
            assert stream.read(5) == b"%PDF-"
            assert getattr(stream_info, "extension") == ".pdf"
            return SimpleNamespace(markdown="# Tema\r\n\r\n\r\nTexto. \x00")

    monkeypatch.setattr(document_converter, "MarkItDown", StubMarkItDown)

    result = convert_to_markdown(b"%PDF-1.7 fake", "pdf", max_extracted_chars=100)

    assert result == "# Tema\n\nTexto."


def test_converter_rejects_empty_extraction_and_excessive_text(monkeypatch: pytest.MonkeyPatch) -> None:
    class StubMarkItDown:
        def __init__(self, *, enable_plugins: bool) -> None:
            pass

        def convert_stream(self, stream: io.BytesIO, *, stream_info: object) -> SimpleNamespace:
            return SimpleNamespace(markdown=" \n " if mode[0] == "empty" else "x" * 101)

    mode = ["empty"]
    monkeypatch.setattr(document_converter, "MarkItDown", StubMarkItDown)
    with pytest.raises(NoExtractableTextError):
        convert_to_markdown(b"%PDF-1.7 fake", "pdf", max_extracted_chars=100)

    mode[0] = "large"
    with pytest.raises(DocumentTooLargeError):
        convert_to_markdown(b"%PDF-1.7 fake", "pdf", max_extracted_chars=100)


@pytest.mark.parametrize(
    ("file_bytes", "extension", "expected_text"),
    [
        (make_minimal_pdf(), "pdf", "Arithmetic guide 2 plus 2"),
        (make_minimal_docx(), "docx", "Algebra guide"),
        (make_minimal_pptx(), "pptx", "Geometry guide"),
    ],
    ids=["pdf", "docx", "pptx"],
)
def test_markitdown_extracts_text_from_supported_formats(
    file_bytes: bytes,
    extension: str,
    expected_text: str,
) -> None:
    markdown = convert_to_markdown(file_bytes, extension)

    assert expected_text in markdown
