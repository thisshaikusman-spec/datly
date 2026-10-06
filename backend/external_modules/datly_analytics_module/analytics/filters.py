import pandas as pd

from .models import AnalyticsError


def apply_filters(df: pd.DataFrame, filters: list[dict]) -> pd.DataFrame:
    """
    Applies deterministic filters to the DataFrame.
    
    Supported operators:
    - equals
    - not_equals
    - greater_than
    - less_than
    - greater_than_or_equal
    - less_than_or_equal
    - contains
    - date_before
    - date_after
    - date_between
    """
    result = df.copy()
    
    for f in filters:
        col = f.get("column")
        op = f.get("operator")
        val = f.get("value")
        
        if not col or not op:
            raise AnalyticsError("INVALID_FILTER", "Filter must contain 'column' and 'operator'.")
            
        if col not in result.columns:
            raise AnalyticsError("MISSING_COLUMN", f"Column '{col}' does not exist in the dataset.")
            
        if op == "equals":
            result = result[result[col] == val]
        elif op == "not_equals":
            result = result[result[col] != val]
        elif op == "greater_than":
            result = result[result[col] > val]
        elif op == "less_than":
            result = result[result[col] < val]
        elif op == "greater_than_or_equal":
            result = result[result[col] >= val]
        elif op == "less_than_or_equal":
            result = result[result[col] <= val]
        elif op == "contains":
            # For contains, treat safely as string
            result = result[result[col].astype(str).str.contains(str(val), na=False)]
        elif op in ("date_before", "date_after", "date_between"):
            col_dates = pd.to_datetime(result[col], errors="coerce")
            parsed_val = pd.to_datetime(val, errors="coerce")
            if pd.isna(parsed_val):
                raise AnalyticsError(
                    "INVALID_DATE_FILTER",
                    f"Invalid date value '{val}' for filter on column '{col}'."
                )

            if op == "date_before":
                result = result[col_dates < parsed_val]
            elif op == "date_after":
                result = result[col_dates > parsed_val]
            elif op == "date_between":
                val_end = f.get("value_end") or f.get("secondary_value")
                if val_end is None:
                    raise AnalyticsError("INVALID_FILTER", "date_between requires 'value_end' or 'secondary_value'.")
                parsed_val_end = pd.to_datetime(val_end, errors="coerce")
                if pd.isna(parsed_val_end):
                    raise AnalyticsError(
                        "INVALID_DATE_FILTER",
                        f"Invalid end date value '{val_end}' for filter on column '{col}'."
                    )
                result = result[(col_dates >= parsed_val) & (col_dates <= parsed_val_end)]
        else:
            raise AnalyticsError("UNSUPPORTED_OPERATOR", f"Filter operator '{op}' is not supported.")
            
    return result
