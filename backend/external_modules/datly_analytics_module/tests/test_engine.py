import pandas as pd
import pytest
from analytics.engine import AnalyticsEngine
from analytics.models import AnalyticsError


@pytest.fixture
def sample_df():
    return pd.DataFrame({
        "city": ["Coimbatore", "Chennai", "Pollachi"],
        "revenue": [8250000, 6500000, 3200000]
    })

def test_engine_execution(sample_df):
    engine = AnalyticsEngine()
    
    # Valid execution
    plan = {
        "operation": "group_by",
        "group_column": "city",
        "metric_column": "revenue",
        "aggregation": "sum",
        "sort": "desc",
        "limit": 1
    }
    
    res = engine.execute(sample_df, plan)
    assert res.operation == "group_by"
    assert res.row_count == 1
    assert res.rows[0]["city"] == "Coimbatore"
    assert res.rows[0]["revenue"] == 8250000
    assert "city" in res.columns
    assert "revenue" in res.columns

def test_engine_security(sample_df):
    engine = AnalyticsEngine()
    
    # Test eval/exec rejection
    with pytest.raises(AnalyticsError, match="is not supported"):
        engine.execute(sample_df, {"operation": "eval", "code": "import os; os.system('echo hacked')"})
        
    with pytest.raises(AnalyticsError, match="is not supported"):
        engine.execute(sample_df, {"operation": "execute_python", "code": "print('test')"})
        
    with pytest.raises(AnalyticsError, match="must contain an 'operation'"):
        engine.execute(sample_df, {})
        
def test_engine_invalid_df():
    engine = AnalyticsEngine()
    with pytest.raises(AnalyticsError, match="Pandas DataFrame"):
        engine.execute("not_a_df", {"operation": "sum", "metric_column": "revenue"})
