from typing import Any

from pydantic import BaseModel


class AnalyticsError(Exception):
    """Exception raised for errors in the analytics engine."""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(message)


class AnalysisResult(BaseModel):
    """The structured result returned by the Analytics Engine."""
    operation: str
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    visualization: dict[str, Any] | None = None
