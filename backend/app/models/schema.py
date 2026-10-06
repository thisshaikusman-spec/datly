from typing import Any

from pydantic import BaseModel


class ColumnSchema(BaseModel):
    name: str
    pandas_dtype: str
    inferred_type: str
    semantic_role: str
    nullable: bool
    missing_count: int
    missing_percentage: float
    unique_count: int
    unique_percentage: float
    sample_values: list[Any]

class DatasetSchema(BaseModel):
    success: bool = True
    dataset_id: str
    rows: int
    columns: int
    column_details: list[ColumnSchema]

class NumericStatistics(BaseModel):
    min: float | None = None
    max: float | None = None
    mean: float | None = None
    median: float | None = None
    std_dev: float | None = None

class CategoricalStatistics(BaseModel):
    unique_count: int
    top_values: list[str]
    frequencies: dict[str, int]

class DatetimeStatistics(BaseModel):
    min_date: str | None = None
    max_date: str | None = None

class ColumnProfile(BaseModel):
    name: str
    missing_count: int
    numeric_stats: NumericStatistics | None = None
    categorical_stats: CategoricalStatistics | None = None
    datetime_stats: DatetimeStatistics | None = None

class DatasetProfile(BaseModel):
    success: bool = True
    dataset_id: str
    rows: int
    columns: int
    column_profiles: list[ColumnProfile]
