from typing import Protocol


class TutorProvider(Protocol):
    def generate(self, *, system_instruction: str, contents: str) -> str: ...


class TutorProviderError(Exception):
    def __init__(self, message: str, *, status_code: int = 502, retryable: bool | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable if retryable is not None else status_code in (429, 502, 503)
