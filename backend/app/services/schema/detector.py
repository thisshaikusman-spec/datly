import numpy as np
import pandas as pd

from app.models.schema import ColumnSchema, DatasetSchema
from app.services.schema.semantic_roles import detect_semantic_role
from app.services.schema.type_detector import detect_inferred_type

SCHEMA_SAMPLE_SIZE = 5

def sanitize_value(val):
    if pd.isna(val) or val is None:
        return None
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        return float(val)
    if isinstance(val, (np.bool_, bool)):
        return bool(val)
    if isinstance(val, pd.Timestamp):
        return val.isoformat()
    return str(val)

def detect_schema(dataset_id: str, df: pd.DataFrame) -> DatasetSchema:
    rows = len(df)
    columns = len(df.columns)
    column_details = []
    
    for col_name in df.columns:
        series = df[col_name]
        
        pandas_dtype = str(series.dtype)
        inferred_type = detect_inferred_type(series)
        semantic_role = detect_semantic_role(col_name, inferred_type, series)
        
        missing_count = int(series.isna().sum())
        missing_percentage = float(missing_count / rows * 100) if rows > 0 else 0.0
        
        unique_count = int(series.nunique())
        unique_percentage = float(unique_count / rows * 100) if rows > 0 else 0.0
        
        nullable = missing_count > 0
        
        raw_samples = series.dropna().unique()[:SCHEMA_SAMPLE_SIZE]
        sample_values = [sanitize_value(val) for val in raw_samples]
        
        column_details.append(ColumnSchema(
            name=str(col_name),
            pandas_dtype=pandas_dtype,
            inferred_type=inferred_type,
            semantic_role=semantic_role,
            nullable=nullable,
            missing_count=missing_count,
            missing_percentage=missing_percentage,
            unique_count=unique_count,
            unique_percentage=unique_percentage,
            sample_values=sample_values
        ))
        
    return DatasetSchema(
        dataset_id=dataset_id,
        rows=rows,
        columns=columns,
        column_details=column_details
    )
