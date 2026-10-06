
import pandas as pd

from .aggregations import get_aggregation
from .filters import apply_filters
from .models import AnalyticsError


def _check_column_exists(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        raise AnalyticsError("MISSING_COLUMN", f"Column '{column}' does not exist in the dataset.")

def _check_numeric_column(df: pd.DataFrame, column: str, operation: str) -> None:
    _check_column_exists(df, column)
    if not pd.api.types.is_numeric_dtype(df[column]):
        raise AnalyticsError("INCOMPATIBLE_OPERATION", f"Column '{column}' must be numeric for the {operation} operation.")

def _prepare_df(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    filters = plan.get("filters")
    if filters and isinstance(filters, list):
        return apply_filters(df, filters)
    return df


def calculate_sum(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    df = _prepare_df(df, plan)
    metric = plan.get("metric_column")
    if not metric:
        raise AnalyticsError("MISSING_METRIC", "metric_column is required for sum.")
    _check_numeric_column(df, metric, "sum")
    
    val = df[metric].sum()
    if pd.isna(val):
        val = 0
    return pd.DataFrame([{metric: float(val)}])

def calculate_average(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    df = _prepare_df(df, plan)
    metric = plan.get("metric_column")
    if not metric:
        raise AnalyticsError("MISSING_METRIC", "metric_column is required for average.")
    _check_numeric_column(df, metric, "average")
    
    val = df[metric].mean()
    if pd.isna(val):
        val = 0
    return pd.DataFrame([{metric: float(val)}])

def calculate_min(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    df = _prepare_df(df, plan)
    metric = plan.get("metric_column")
    if not metric:
        raise AnalyticsError("MISSING_METRIC", "metric_column is required for min.")
    _check_column_exists(df, metric)
    
    val = df[metric].min()
    if pd.isna(val):
        val = None
    return pd.DataFrame([{metric: val}])

def calculate_max(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    df = _prepare_df(df, plan)
    metric = plan.get("metric_column")
    if not metric:
        raise AnalyticsError("MISSING_METRIC", "metric_column is required for max.")
    _check_column_exists(df, metric)
    
    val = df[metric].max()
    if pd.isna(val):
        val = None
    return pd.DataFrame([{metric: val}])

def calculate_count(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    df = _prepare_df(df, plan)
    metric = plan.get("metric_column")
    if metric:
        _check_column_exists(df, metric)
        val = df[metric].count()
    else:
        val = len(df)
    return pd.DataFrame([{"count": int(val)}])

def apply_filter_op(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    filters = plan.get("filters", [])
    if not isinstance(filters, list):
        raise AnalyticsError("INVALID_FILTERS", "filters must be a list.")
    return apply_filters(df, filters)

def group_by(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    df = _prepare_df(df, plan)
    group_col = plan.get("group_column")
    metric = plan.get("metric_column")
    agg = plan.get("aggregation") or "sum"
    sort_dir = plan.get("sort")
    limit = plan.get("limit")
    
    # Defensive fallbacks if columns were omitted in plan
    if not group_col or group_col not in df.columns:
        cat_cols = [c for c in df.columns if df[c].dtype == "object" or str(df[c].dtype) == "category"]
        if cat_cols:
            group_col = cat_cols[0]
            
    if not metric or metric not in df.columns:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if num_cols:
            metric = num_cols[0]

    if not group_col or not metric or not agg:
        raise AnalyticsError("INVALID_GROUP_BY", "group_column, metric_column, and aggregation are required.")
        
    _check_column_exists(df, group_col)
    _check_column_exists(df, metric)
    
    agg_func = get_aggregation(agg)
    
    if agg_func in ["sum", "mean", "median"] and not pd.api.types.is_numeric_dtype(df[metric]):
        raise AnalyticsError("INCOMPATIBLE_OPERATION", f"Column '{metric}' must be numeric for the {agg_func} operation.")
    
    grouped = df.groupby(group_col, as_index=False).agg({metric: agg_func})
    
    if sort_dir:
        if sort_dir not in ["asc", "desc"]:
            raise AnalyticsError("INVALID_SORT", "sort must be 'asc' or 'desc'.")
        grouped = grouped.sort_values(by=metric, ascending=(sort_dir == "asc"))
        
    if limit is not None:
        if not isinstance(limit, int) or limit < 0:
            raise AnalyticsError("INVALID_LIMIT", "limit must be a positive integer.")
        grouped = grouped.head(limit)
        
    return grouped

def sort_dataframe(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    df = _prepare_df(df, plan)
    sort_col = plan.get("sort_column")
    sort_dir = plan.get("sort", "asc")
    limit = plan.get("limit")
    
    if not sort_col:
        raise AnalyticsError("MISSING_SORT_COLUMN", "sort_column is required.")
        
    _check_column_exists(df, sort_col)
    
    if sort_dir not in ["asc", "desc"]:
        raise AnalyticsError("INVALID_SORT", "sort must be 'asc' or 'desc'.")
        
    result = df.sort_values(by=sort_col, ascending=(sort_dir == "asc"))
    
    if limit is not None:
        if not isinstance(limit, int) or limit < 0:
            raise AnalyticsError("INVALID_LIMIT", "limit must be a positive integer.")
        result = result.head(limit)
        
    return result

def top_n(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    df = _prepare_df(df, plan)
    metric = plan.get("metric_column")
    n = plan.get("n") if plan.get("n") is not None else plan.get("limit")
    sort_dir = plan.get("sort", "desc")
    group_col = plan.get("group_column")
    agg = plan.get("aggregation") or "sum"
    
    if not metric:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if num_cols:
            metric = num_cols[0]
            
    if not metric:
        raise AnalyticsError("INVALID_TOP_N", "metric_column is required for top_n.")
        
    _check_column_exists(df, metric)
    
    if n is None:
        n = 5
    if not isinstance(n, int) or n < 0:
        raise AnalyticsError("INVALID_N", "n (or limit) must be a positive integer.")
        
    if sort_dir not in ["asc", "desc"]:
        raise AnalyticsError("INVALID_SORT", "sort must be 'asc' or 'desc'.")
        
    if group_col:
        _check_column_exists(df, group_col)
        agg_func = get_aggregation(agg)
        grouped = df.groupby(group_col, as_index=False).agg({metric: agg_func})
        grouped = grouped.sort_values(by=metric, ascending=(sort_dir == "asc"))
        return grouped.head(n)
        
    result = df.sort_values(by=metric, ascending=(sort_dir == "asc"))
    return result.head(n)

def calculate_trend(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    df = _prepare_df(df, plan)
    group_col = plan.get("group_column")
    metric = plan.get("metric_column")
    agg = plan.get("aggregation") or "sum"
    
    # If no group column specified, look for date/time column
    if not group_col:
        for c in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[c]) or any(dk in c.lower() for dk in ["date", "time", "year", "month"]):
                group_col = c
                break
    if not group_col:
        cat_cols = [c for c in df.columns if df[c].dtype == "object" or str(df[c].dtype) == "category"]
        if cat_cols:
            group_col = cat_cols[0]
            
    if not metric or metric not in df.columns:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if num_cols:
            metric = num_cols[0]
            
    if not group_col or not metric:
        raise AnalyticsError("INVALID_TREND", "group_column and metric_column are required for trend.")
        
    _check_column_exists(df, group_col)
    _check_column_exists(df, metric)
    
    agg_func = get_aggregation(agg)
    grouped = df.groupby(group_col, as_index=False).agg({metric: agg_func})
    
    # Trend is always sorted by time/group ascending
    grouped = grouped.sort_values(by=group_col, ascending=True)
    limit = plan.get("limit")
    if limit is not None and isinstance(limit, int) and limit > 0:
        grouped = grouped.head(limit)
    return grouped

def calculate_comparison(df: pd.DataFrame, plan: dict) -> pd.DataFrame:
    df = _prepare_df(df, plan)
    group_col = plan.get("group_column")
    metric = plan.get("metric_column")
    agg = plan.get("aggregation") or "sum"
    sort_col = plan.get("sort_column") or metric
    sort_dir = plan.get("sort", "desc")
    limit = plan.get("limit")
    
    if group_col and metric:
        _check_column_exists(df, group_col)
        _check_column_exists(df, metric)
        agg_func = get_aggregation(agg)
        grouped = df.groupby(group_col, as_index=False).agg({metric: agg_func})
        if sort_col in grouped.columns:
            grouped = grouped.sort_values(by=sort_col, ascending=(sort_dir == "asc"))
        if limit is not None and isinstance(limit, int) and limit > 0:
            grouped = grouped.head(limit)
        return grouped
    elif sort_col and sort_col in df.columns:
        return sort_dataframe(df, plan)
    else:
        num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
        if num_cols:
            return df[num_cols].head(limit or 10)
        return df.head(limit or 10)

# Mapping dictionary for strict execution
OPERATION_MAP = {
    "sum": calculate_sum,
    "average": calculate_average,
    "min": calculate_min,
    "max": calculate_max,
    "count": calculate_count,
    "filter": apply_filter_op,
    "group_by": group_by,
    "trend": calculate_trend,
    "sort": sort_dataframe,
    "top_n": top_n,
    "comparison": calculate_comparison,
}
