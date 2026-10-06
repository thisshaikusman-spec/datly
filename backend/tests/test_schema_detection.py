import pandas as pd

from app.models.schema import DatasetProfile, DatasetSchema
from app.services.schema.detector import detect_schema
from app.services.schema.profiler import profile_dataset


def test_schema_detection():
    data = {
        "id": [1001, 1002, 1003, 1004],
        "name": ["Alice", "Bob", "Charlie", "David"],
        "age": [30, 25, 35, 28],
        "city": ["NY", "LA", "CHI", "NY"],
        "revenue": [100.5, 200.0, 150.75, 300.2],
        "is_active": [True, False, True, True],
        "created_at": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04"],
        "description": ["Long text a" * 10, "Long text b" * 10, "Long text c" * 10, "Long text d" * 10]
    }
    df = pd.DataFrame(data)
    
    schema = detect_schema("ds_test", df)
    
    assert isinstance(schema, DatasetSchema)
    assert schema.rows == 4
    assert schema.columns == 8
    
    cols = {c.name: c for c in schema.column_details}
    
    assert cols["id"].inferred_type == "integer"
    assert cols["id"].semantic_role == "identifier"
    
    assert cols["age"].inferred_type == "integer"
    assert cols["age"].semantic_role == "numeric_measure"
    
    assert cols["revenue"].inferred_type == "float"
    assert cols["revenue"].semantic_role == "numeric_metric"
    
    assert cols["is_active"].inferred_type == "boolean"
    assert cols["is_active"].semantic_role == "boolean"
    
    assert cols["created_at"].inferred_type == "datetime"
    
    assert cols["city"].inferred_type == "categorical"
    assert cols["city"].semantic_role == "categorical"
    
    assert cols["description"].inferred_type == "text"
    assert cols["description"].semantic_role == "text"

def test_profile_dataset():
    data = {
        "age": [30, 25, 35, 28],
        "city": ["NY", "LA", "NY", "NY"]
    }
    df = pd.DataFrame(data)
    
    profile = profile_dataset("ds_test", df)
    
    assert isinstance(profile, DatasetProfile)
    assert profile.rows == 4
    assert profile.columns == 2
    
    cols = {c.name: c for c in profile.column_profiles}
    
    assert cols["age"].numeric_stats is not None
    assert cols["age"].numeric_stats.min == 25
    assert cols["age"].numeric_stats.max == 35
    
    assert cols["city"].categorical_stats is not None
    assert cols["city"].categorical_stats.unique_count == 2
    assert "NY" in cols["city"].categorical_stats.top_values
