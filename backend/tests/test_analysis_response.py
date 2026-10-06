from app.models.analysis_plan import AnalysisPlan, Operation
from app.models.analysis_result import (
    AnalysisResponse,
    VisualizationSpec,
    VisualizationType,
)
from app.services.analytics.answer_formatter import format_answer, format_number


def test_numeric_formatting():
    assert format_number(1000) == "1,000"
    assert format_number(152500.50) == "152,500.5"
    assert format_number(8250000) == "8,250,000"

def test_scalar_answer():
    plan = AnalysisPlan(operation=Operation.sum, metric_column="revenue")
    result = {"value": 1124000}
    answer = format_answer(plan, result)
    assert answer == "The total revenue is 1,124,000."

def test_top_n_answer():
    plan = AnalysisPlan(operation=Operation.top_n, group_column="city", metric_column="revenue")
    result = {"data": [{"city": "Coimbatore", "revenue": 8250000}]}
    answer = format_answer(plan, result)
    assert answer == "Coimbatore has the highest revenue with a value of 8,250,000."

def test_empty_result_answer():
    plan = AnalysisPlan(operation=Operation.filter, metric_column="revenue")
    result = {"data": []}
    answer = format_answer(plan, result)
    assert answer == "No matching records were found."

def test_grouped_result_answer():
    plan = AnalysisPlan(operation=Operation.group_by, group_column="city", metric_column="revenue")
    result = {"data": [{"city": "A", "revenue": 10}, {"city": "B", "revenue": 20}]}
    answer = format_answer(plan, result)
    # Multi-row grouped result: should include breakdown info, not generic fallback
    assert "revenue" in answer.lower() and "city" in answer.lower()

def test_analysis_response_serialization():
    plan = AnalysisPlan(operation=Operation.sum, metric_column="revenue")
    viz = VisualizationSpec(type=VisualizationType.none)
    resp = AnalysisResponse(
        dataset_id="ds_123",
        question="What is the total revenue?",
        answer="Total is 100",
        result={"value": 100},
        visualization=viz,
        analysis_plan=plan
    )
    assert resp.success is True
    assert resp.dataset_id == "ds_123"
    assert resp.answer == "Total is 100"
