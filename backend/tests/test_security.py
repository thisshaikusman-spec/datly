import pytest

from app.models.analysis_plan import AnalysisPlan


def test_analysis_plan_prevents_arbitrary_code():
    with pytest.raises(ValueError):
        AnalysisPlan(operation="execute_python", metric_column="revenue")

def test_analysis_plan_prevents_eval():
    with pytest.raises(ValueError):
        AnalysisPlan(operation="eval", metric_column="revenue")
