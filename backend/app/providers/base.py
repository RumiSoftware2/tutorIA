from typing import Protocol


class TutorProvider(Protocol):
    provider_name: str

    async def generate(self, *, system_instruction: str, contents: str) -> str: ...

    async def close(self) -> None: ...


class SyncTutorProvider(Protocol):
    def generate(self, *, system_instruction: str, contents: str) -> str: ...


class TutorProviderError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int = 502,
        retryable: bool | None = None,
        category: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable if retryable is not None else status_code in (408, 429, 502, 503, 504)
        self.category = category or (
            "quota" if status_code == 429 else "authentication" if status_code in (401, 403)
            else "unavailable" if self.retryable else "configuration"
        )
