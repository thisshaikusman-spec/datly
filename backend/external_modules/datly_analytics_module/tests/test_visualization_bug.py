import pandas as pd
from analytics.visualization import determine_visualization


def test_determine_visualization_no_metric_col():
    df = pd.DataFrame({"city": ["A", "B", "C"], "count": [1, 2, 3]})
    plan = {
        "operation": "group_by",
        "group_column": "city"
    }
    
    viz = determine_visualization(df, plan)
    assert viz["type"] == "table"
