from app.models.analysis_plan import AnalysisPlan, Operation
from app.models.analysis_result import VisualizationType
from app.services.visualization.chart_selector import VisualizationSelector


def test_visualization_scalar_none():
    plan = AnalysisPlan(operation=Operation.sum, metric_column="revenue")
    result = {"value": 5000}
    viz = VisualizationSelector.select_visualization(plan, result)
    assert viz.type == VisualizationType.none

def test_visualization_group_by_bar():
    plan = AnalysisPlan(operation=Operation.group_by, group_column="city", metric_column="revenue")
    result = {"data": [{"city": "A", "revenue": 10}]}
    viz = VisualizationSelector.select_visualization(plan, result)
    assert viz.type == VisualizationType.bar
    assert viz.x == "city"
    assert viz.y == "revenue"

def test_visualization_time_series_line():
    plan = AnalysisPlan(operation=Operation.trend, group_column="date", metric_column="revenue")
    result = {"data": [{"date": "2024-01-01", "revenue": 10}]}
    viz = VisualizationSelector.select_visualization(plan, result)
    assert viz.type == VisualizationType.line
    assert viz.x == "date"
    assert viz.y == "revenue"
    
def test_visualization_scatter():
    plan = AnalysisPlan(operation=Operation.comparison, group_column="quantity", metric_column="revenue")
    result = {"data": [{"quantity": 2, "revenue": 10}]}
    viz = VisualizationSelector.select_visualization(plan, result)
    assert viz.type == VisualizationType.scatter
    assert viz.x == "quantity"
    assert viz.y == "revenue"
    
def test_visualization_fallback_table():
    plan = AnalysisPlan(operation=Operation.filter)
    result = {"data": [{"col1": "A", "col2": "B"}]}
    viz = VisualizationSelector.select_visualization(plan, result)
    assert viz.type == VisualizationType.table
