from enum import Enum

from pydantic import BaseModel


class Operation(str, Enum):
    count = "count"
    sum = "sum"
    average = "average"
    min = "min"
    max = "max"
    filter = "filter"
    group_by = "group_by"
    sort = "sort"
    top_n = "top_n"
    comparison = "comparison"
    trend = "trend"

class Aggregation(str, Enum):
    sum = "sum"
    mean = "mean"
    count = "count"
    min = "min"
    max = "max"
    median = "median"

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

class FilterOperator(str, Enum):
    equals = "equals"
    not_equals = "not_equals"
    greater_than = "greater_than"
    less_than = "less_than"
    greater_than_or_equal = "greater_than_or_equal"
    less_than_or_equal = "less_than_or_equal"
    contains = "contains"
    date_before = "date_before"
    date_after = "date_after"
    date_between = "date_between"

class FilterCondition(BaseModel):
    column: str
    operator: FilterOperator
    value: str | int | float | bool
    secondary_value: str | int | float | bool | None = None

from pydantic import ConfigDict, Field, model_validator


class JoinType(str, Enum):
    inner = "inner"
    left = "left"


class JoinCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    left: str
    right: str
    left_on: str
    right_on: str
    how: JoinType = JoinType.inner


class AnalysisPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    operation: Operation
    dataset: str | None = None
    joins: list[JoinCondition] = Field(default_factory=list)
    metric_column: str | None = None
    group_column: str | None = None
    filters: list[FilterCondition] | None = None
    aggregation: Aggregation | None = None
    sort: str | None = None
    sort_column: str | None = None
    limit: int | None = None
    visualization: VisualizationType | None = None
    visualizations: list[VisualizationType] = Field(default_factory=list)
    # Tracks whether the user EXPLICITLY requested a chart type
    explicit_visualization: bool = False
    clarification_needed: bool = False
    clarification_question: str | None = None

    @model_validator(mode="after")
    def sync_visualizations(self) -> "AnalysisPlan":
        # Keep visualization and visualizations list in sync
        if self.visualizations and not self.visualization:
            self.visualization = self.visualizations[0]
        elif self.visualization and not self.visualizations:
            self.visualizations = [self.visualization]
        elif not self.visualization and not self.visualizations:
            self.visualization = VisualizationType.table
            self.visualizations = [VisualizationType.table]
        return self
