import pandas as pd

from app.models.analysis_plan import (
    Aggregation,
    AnalysisPlan,
    Operation,
)
from app.services.analytics.answer_formatter import format_answer
from app.services.analytics.engine import execute_plan


def test_integration_full():
    df = pd.DataFrame({
        "city": ["Coimbatore", "Chennai", "Pollachi", "Coimbatore", "Chennai"],
        "revenue": [8250000, 6500000, 3200000, 1750000, 2100000],
        "units": [1200, 900, 500, 300, 400]
    })
    
    # "What is the total revenue?"
    plan_total = AnalysisPlan(
        operation=Operation.sum,
        metric_column="revenue"
    )
    res_total = execute_plan(df, plan_total)
    assert res_total["value"] == 21800000
    assert format_answer(plan_total, res_total) == "The total revenue is 21,800,000."
    
    # "Which city generated the highest revenue?" (implies group_by sum then top_n, or just group_by top_n)
    # The new engine supports group_by with sort desc limit 1
    plan_highest = AnalysisPlan(
        operation=Operation.group_by,
        group_column="city",
        metric_column="revenue",
        aggregation=Aggregation.sum,
        sort="desc",
        limit=1
    )
    res_highest = execute_plan(df, plan_highest)
    assert res_highest["data"][0]["city"] == "Coimbatore"
    assert res_highest["data"][0]["revenue"] == 10000000
    
    # Test min revenue
    plan_min = AnalysisPlan(
        operation=Operation.min,
        metric_column="revenue"
    )
    res_min = execute_plan(df, plan_min)
    assert res_min["value"] == 1750000
    
    # Test average revenue
    plan_avg = AnalysisPlan(
        operation=Operation.average,
        metric_column="revenue"
    )
    res_avg = execute_plan(df, plan_avg)
    assert res_avg["value"] == 4360000
