from enum import Enum
from typing import Any

from pydantic import BaseModel


class VisualizationType(str, Enum):
    bar = "bar"
    line = "line"
    scatter = "scatter"
    pie = "pie"
    histogram = "histogram"
    area = "area"
    box = "box"
    table = "table"
    kpi = "kpi"
    none = "none"

class VisualizationSpec(BaseModel):
    type: VisualizationType
    x: str | None = None
    y: str | None = None
    title: str | None = None
    # For pie charts
    labels: list[str] | None = None
    values: list[float] | None = None
    # For histogram
    bins: list[float] | None = None
    frequencies: list[int] | None = None
    # For box plot
    stats: dict[str, float] | None = None

from pydantic import Field, model_validator

from app.models.analysis_plan import AnalysisPlan


class StepVerification(BaseModel):
    step: str
    details: str
    rows_before: int | None = None
    rows_after: int | None = None


class VerificationBlock(BaseModel):
    datasets_used: list[str] = Field(default_factory=list)
    operation: str
    joins: list[dict[str, str]] = Field(default_factory=list)
    filters_applied: list[dict[str, Any]] = Field(default_factory=list)
    initial_rows: int = 0
    final_rows: int = 0
    row_count_before: int | None = None
    row_count_after: int | None = None
    steps: list[StepVerification] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    success: bool = True
    dataset_id: str | None = None
    workspace_id: str | None = None
    question: str
    answer: str
    result: dict[str, Any]
    visualization: VisualizationSpec
    visualizations: list[VisualizationSpec] = Field(default_factory=list)
    analysis_plan: AnalysisPlan
    verification: VerificationBlock | None = None
    clarification_needed: bool = False
    clarification_question: str | None = None
    language_code: str | None = "en-IN"

    @model_validator(mode="after")
    def sync_visualizations(self) -> "AnalysisResponse":
        if self.visualizations and not self.visualization:
            self.visualization = self.visualizations[0]
        elif self.visualization and not self.visualizations:
            self.visualizations = [self.visualization]
        return self
