import io
import re
import zipfile
from pathlib import PurePosixPath

from markitdown import MarkItDown, StreamInfo


MIME_TYPES = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
}
MAX_ARCHIVE_ENTRIES = 2_000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 100 * 1024 * 1024
MAX_ARCHIVE_CONTENT_TYPES_BYTES = 1024 * 1024


class DocumentInputError(ValueError):
    """Base exception for a rejected or unreadable upload."""


class UnsupportedDocumentError(DocumentInputError):
    pass


class DocumentTooLargeError(DocumentInputError):
    pass


class NoExtractableTextError(DocumentInputError):
    pass


class DocumentConversionError(DocumentInputError):
    pass


def _validate_zip_document(data: bytes, extension: str) -> None:
    required_file = "word/document.xml" if extension == "docx" else "ppt/presentation.xml"
    expected_type = (
        b"wordprocessingml.document.main+xml"
        if extension == "docx"
        else b"presentationml.presentation.main+xml"
    )
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ARCHIVE_ENTRIES:
                raise UnsupportedDocumentError("El documento contiene demasiados elementos.")
            total_uncompressed = sum(entry.file_size for entry in entries)
            if total_uncompressed > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise DocumentTooLargeError("El contenido descomprimido supera el límite permitido.")
            for entry in entries:
                path = PurePosixPath(entry.filename.replace("\\", "/"))
                if path.is_absolute() or ".." in path.parts:
                    raise UnsupportedDocumentError("La estructura del documento no es válida.")

            names = {entry.filename for entry in entries}
            if "[Content_Types].xml" not in names or required_file not in names:
                raise UnsupportedDocumentError("El archivo no es un documento Office válido.")
            content_types_info = archive.getinfo("[Content_Types].xml")
            if content_types_info.file_size > MAX_ARCHIVE_CONTENT_TYPES_BYTES:
                raise UnsupportedDocumentError("La estructura del documento no es válida.")
            content_types = archive.read("[Content_Types].xml")
            if expected_type not in content_types:
                raise UnsupportedDocumentError("La extensión no coincide con el contenido del archivo.")
    except (zipfile.BadZipFile, KeyError, OSError, RuntimeError):
        raise UnsupportedDocumentError("El archivo Office está dañado o no es válido.") from None


def validate_document_bytes(file_bytes: bytes, extension: str, max_bytes: int) -> str:
    normalized_extension = extension.lower().lstrip(".")
    if normalized_extension not in MIME_TYPES:
        raise UnsupportedDocumentError("Formato no permitido. Usa PDF, DOCX o PPTX.")
    if not file_bytes:
        raise NoExtractableTextError("El archivo está vacío.")
    if len(file_bytes) > max_bytes:
        raise DocumentTooLargeError("El archivo supera el tamaño máximo permitido.")

    if normalized_extension == "pdf":
        if b"%PDF-" not in file_bytes[:1024]:
            raise UnsupportedDocumentError("El archivo no parece ser un PDF válido.")
    else:
        _validate_zip_document(file_bytes, normalized_extension)
    return normalized_extension


def _clean_markdown(markdown: str) -> str:
    cleaned = markdown.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    cleaned = "\n".join(line.rstrip() for line in cleaned.split("\n"))
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def convert_to_markdown(
    file_bytes: bytes,
    extension: str,
    *,
    filename: str = "documento",
    max_bytes: int = 10 * 1024 * 1024,
    max_extracted_chars: int = 250_000,
) -> str:
    normalized_extension = validate_document_bytes(file_bytes, extension, max_bytes)
    try:
        result = MarkItDown(enable_plugins=False).convert_stream(
            io.BytesIO(file_bytes),
            stream_info=StreamInfo(extension=f".{normalized_extension}", filename=filename),
        )
    except Exception:
        raise DocumentConversionError("No se pudo convertir el documento.") from None

    markdown = _clean_markdown(result.markdown or "")
    if not markdown:
        raise NoExtractableTextError(
            "No se pudo extraer texto del documento. Comprueba que el PDF permita seleccionar y copiar texto; el OCR no está incluido."
        )
    if len(markdown) > max_extracted_chars:
        raise DocumentTooLargeError("El texto extraído supera el límite permitido.")
    return markdown
