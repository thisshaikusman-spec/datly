import pandas as pd
import pytest
from analytics.filters import apply_filters


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "city": ["Coimbatore", "Chennai", "Pollachi"],
        "revenue": [8250000, 6500000, 3200000],
        "date": ["2023-01-01", "2023-06-01", "2023-12-01"]
    })

def test_filter_operators(sample_df):
    # equals
    res = apply_filters(sample_df, [{"column": "city", "operator": "equals", "value": "Chennai"}])
    assert len(res) == 1
    
    # not_equals
    res = apply_filters(sample_df, [{"column": "city", "operator": "not_equals", "value": "Chennai"}])
    assert len(res) == 2
    
    # greater_than
    res = apply_filters(sample_df, [{"column": "revenue", "operator": "greater_than", "value": 5000000}])
    assert len(res) == 2
    
    # less_than
    res = apply_filters(sample_df, [{"column": "revenue", "operator": "less_than", "value": 5000000}])
    assert len(res) == 1
    
    # greater_than_or_equal
    res = apply_filters(sample_df, [{"column": "revenue", "operator": "greater_than_or_equal", "value": 6500000}])
    assert len(res) == 2
    
    # less_than_or_equal
    res = apply_filters(sample_df, [{"column": "revenue", "operator": "less_than_or_equal", "value": 6500000}])
    assert len(res) == 2
    
    # contains
    res = apply_filters(sample_df, [{"column": "city", "operator": "contains", "value": "batore"}])
    assert len(res) == 1
    
    # date_before
    res = apply_filters(sample_df, [{"column": "date", "operator": "date_before", "value": "2023-05-01"}])
    assert len(res) == 1
    
    # date_after
    res = apply_filters(sample_df, [{"column": "date", "operator": "date_after", "value": "2023-05-01"}])
    assert len(res) == 2
    
    # date_between
    res = apply_filters(sample_df, [{"column": "date", "operator": "date_between", "value": "2023-05-01", "value_end": "2023-11-01"}])
    assert len(res) == 1
