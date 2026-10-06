import pandas as pd


def determine_visualization(df: pd.DataFrame, plan: dict) -> dict:
    """
    Deterministically determines the visualization type based on the result dataframe and plan.
    
    Rules:
    - single scalar result -> none
    - group_by categorical + numeric -> bar
    - time/date + numeric trend -> line
    - two numeric columns -> scatter
    - Unsupported/ambiguous -> table
    """
    if len(df.columns) == 1 and len(df) == 1:
        return {"type": "none"}
        
    op = plan.get("operation")
    
    if op == "group_by":
        group_col = plan.get("group_column")
        metric_col = plan.get("metric_column")
        
        if not group_col or not metric_col:
            return {"type": "table"}
            
        if group_col not in df.columns or metric_col not in df.columns:
            return {"type": "table"}
            
        if pd.api.types.is_datetime64_any_dtype(df[group_col]):
            return {
                "type": "line",
                "x": group_col,
                "y": metric_col,
                "title": f"{metric_col} over {group_col}"
            }
        elif pd.api.types.is_numeric_dtype(df[group_col]):
            return {
                "type": "scatter",
                "x": group_col,
                "y": metric_col,
                "title": f"{metric_col} by {group_col}"
            }
        else:
            return {
                "type": "bar",
                "x": group_col,
                "y": metric_col,
                "title": f"{metric_col} by {group_col}"
            }
            
    if op in ["sort", "top_n", "filter"] and len(df.columns) == 2:
        # If there are exactly two columns, and both are numeric -> scatter
            col1, col2 = df.columns
            if pd.api.types.is_numeric_dtype(df[col1]) and pd.api.types.is_numeric_dtype(df[col2]):
                return {
                    "type": "scatter",
                    "x": col1,
                    "y": col2,
                    "title": f"{col2} vs {col1}"
                }
            elif pd.api.types.is_datetime64_any_dtype(df[col1]) and pd.api.types.is_numeric_dtype(df[col2]):
                 return {
                    "type": "line",
                    "x": col1,
                    "y": col2,
                    "title": f"{col2} over time"
                }
            elif pd.api.types.is_datetime64_any_dtype(df[col2]) and pd.api.types.is_numeric_dtype(df[col1]):
                 return {
                    "type": "line",
                    "x": col2,
                    "y": col1,
                    "title": f"{col1} over time"
                }

    return {"type": "table"}
