import pandas as pd
from analytics.visualization import determine_visualization


def test_visualization():
    # scalar
    df_scalar = pd.DataFrame([{"sum": 100}])
    plan_scalar = {"operation": "sum"}
    assert determine_visualization(df_scalar, plan_scalar) == {"type": "none"}
    
    # group_by categorical -> bar
    df_cat = pd.DataFrame({"city": ["A", "B"], "revenue": [10, 20]})
    plan_cat = {"operation": "group_by", "group_column": "city", "metric_column": "revenue"}
    assert determine_visualization(df_cat, plan_cat)["type"] == "bar"
    
    # group_by numeric -> scatter
    df_num = pd.DataFrame({"age": [20, 30], "revenue": [10, 20]})
    plan_num = {"operation": "group_by", "group_column": "age", "metric_column": "revenue"}
    assert determine_visualization(df_num, plan_num)["type"] == "scatter"
    
    # group_by date -> line
    df_date = pd.DataFrame({"date": pd.to_datetime(["2023-01-01", "2023-02-01"]), "revenue": [10, 20]})
    plan_date = {"operation": "group_by", "group_column": "date", "metric_column": "revenue"}
    assert determine_visualization(df_date, plan_date)["type"] == "line"
    
    # unsupported -> table
    df_multi = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    plan_multi = {"operation": "sort"}
    assert determine_visualization(df_multi, plan_multi) == {"type": "table"}
