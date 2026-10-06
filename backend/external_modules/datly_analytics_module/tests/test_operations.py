import pandas as pd
import pytest
from analytics.models import AnalyticsError
from analytics.operations import OPERATION_MAP


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "city": ["Coimbatore", "Chennai", "Pollachi", "Coimbatore", "Chennai"],
        "revenue": [8250000, 6500000, 3200000, 1750000, 2100000],
        "units": [1200, 900, 500, 300, 400],
        "category": ["A", "B", "A", "A", "B"]
    })

def test_sum(sample_df):
    plan = {"operation": "sum", "metric_column": "revenue"}
    res = OPERATION_MAP["sum"](sample_df, plan)
    assert res.iloc[0]["revenue"] == 21800000
    
    # Missing column
    with pytest.raises(AnalyticsError, match="does not exist"):
         OPERATION_MAP["sum"](sample_df, {"operation": "sum", "metric_column": "invalid"})
         
    # Non numeric
    with pytest.raises(AnalyticsError, match="must be numeric"):
         OPERATION_MAP["sum"](sample_df, {"operation": "sum", "metric_column": "city"})

def test_average(sample_df):
    plan = {"operation": "average", "metric_column": "units"}
    res = OPERATION_MAP["average"](sample_df, plan)
    assert res.iloc[0]["units"] == 660.0
    
    with pytest.raises(AnalyticsError, match="must be numeric"):
         OPERATION_MAP["average"](sample_df, {"operation": "average", "metric_column": "city"})

def test_min_max(sample_df):
    plan_min = {"operation": "min", "metric_column": "revenue"}
    res_min = OPERATION_MAP["min"](sample_df, plan_min)
    assert res_min.iloc[0]["revenue"] == 1750000
    
    plan_max = {"operation": "max", "metric_column": "revenue"}
    res_max = OPERATION_MAP["max"](sample_df, plan_max)
    assert res_max.iloc[0]["revenue"] == 8250000
    
    with pytest.raises(AnalyticsError, match="does not exist"):
        OPERATION_MAP["min"](sample_df, {"operation": "min", "metric_column": "invalid"})

def test_count(sample_df):
    plan = {"operation": "count"}
    res = OPERATION_MAP["count"](sample_df, plan)
    assert res.iloc[0]["count"] == 5
    
    # Empty df
    empty_df = pd.DataFrame()
    res_empty = OPERATION_MAP["count"](empty_df, plan)
    assert res_empty.iloc[0]["count"] == 0

def test_group_by(sample_df):
    plan = {
        "operation": "group_by",
        "group_column": "city",
        "metric_column": "revenue",
        "aggregation": "sum",
        "sort": "desc",
        "limit": 1
    }
    res = OPERATION_MAP["group_by"](sample_df, plan)
    assert len(res) == 1
    assert res.iloc[0]["city"] == "Coimbatore"
    assert res.iloc[0]["revenue"] == 10000000
    
    # Missing group column
    plan["group_column"] = "invalid"
    with pytest.raises(AnalyticsError, match="does not exist"):
        OPERATION_MAP["group_by"](sample_df, plan)

def test_sort(sample_df):
    plan = {
        "operation": "sort",
        "sort_column": "revenue",
        "sort": "desc",
        "limit": 2
    }
    res = OPERATION_MAP["sort"](sample_df, plan)
    assert len(res) == 2
    assert res.iloc[0]["city"] == "Coimbatore"
    assert res.iloc[0]["revenue"] == 8250000
    
    # Invalid direction
    plan["sort"] = "invalid"
    with pytest.raises(AnalyticsError, match="must be 'asc' or 'desc'"):
        OPERATION_MAP["sort"](sample_df, plan)

def test_top_n(sample_df):
    plan = {
        "operation": "top_n",
        "metric_column": "revenue",
        "n": 2,
        "sort": "desc"
    }
    res = OPERATION_MAP["top_n"](sample_df, plan)
    assert len(res) == 2
    assert res.iloc[0]["revenue"] == 8250000
    
    # N larger than dataset
    plan["n"] = 100
    res_large = OPERATION_MAP["top_n"](sample_df, plan)
    assert len(res_large) == 5
    
    # Invalid N
    plan["n"] = -1
    with pytest.raises(AnalyticsError, match="positive integer"):
        OPERATION_MAP["top_n"](sample_df, plan)
