import re


_SENTENCE_BREAKS = re.compile(r"(?<=[.!?;:])\s+|\s+(?=[-*+]\s|\d+[.)]\s)")


def _split_long_paragraph(paragraph: str, chunk_size: int, overlap: int) -> list[str]:
    pieces: list[str] = []
    start = 0
    while len(paragraph) - start > chunk_size:
        limit = start + chunk_size
        lower_bound = start + int(chunk_size * 0.6)
        boundary = -1
        for match in _SENTENCE_BREAKS.finditer(paragraph, lower_bound, limit + 1):
            boundary = match.start()
        if boundary < lower_bound:
            boundary = paragraph.rfind(" ", lower_bound, limit + 1)
        if boundary < lower_bound:
            boundary = limit

        piece = paragraph[start:boundary].strip()
        if not piece:
            piece = paragraph[start:limit].strip()
            boundary = limit
        pieces.append(piece)
        if boundary >= len(paragraph):
            start = len(paragraph)
            break
        next_start = max(start + 1, boundary - overlap)
        next_space = paragraph.find(" ", next_start, min(boundary, next_start + 40))
        if next_space >= 0:
            next_start = next_space + 1
        start = next_start
    remaining = paragraph[start:].strip()
    if remaining:
        pieces.append(remaining)
    return pieces


def _overlap_tail(text: str, overlap: int) -> str:
    if overlap <= 0:
        return ""
    if len(text) <= overlap:
        return text.strip()
    boundary = text.rfind(" ", 0, len(text) - overlap + 1)
    if boundary < 0:
        return ""
    return text[boundary + 1 :].strip()


def split_into_chunks(text: str, chunk_size: int = 1200, overlap: int = 150) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size debe ser mayor que cero.")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap debe estar entre cero y chunk_size - 1.")

    normalized = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    normalized = "\n".join(re.sub(r"[\t \f\v]+", " ", line).strip() for line in normalized.split("\n"))
    normalized = re.sub(r"\n{3,}", "\n\n", normalized).strip()
    if not normalized:
        return []

    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", normalized) if paragraph.strip()]
    units = [
        piece
        for paragraph in paragraphs
        for piece in _split_long_paragraph(paragraph, chunk_size, overlap)
    ]

    chunks: list[str] = []
    current = ""
    for unit in units:
        candidate = f"{current}\n\n{unit}" if current else unit
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
        prefix = _overlap_tail(current, overlap)
        available_prefix = max(0, chunk_size - len(unit) - 2)
        if len(prefix) > available_prefix:
            prefix = ""
        current = f"{prefix}\n\n{unit}" if prefix else unit

    if current:
        chunks.append(current)
    return chunks
