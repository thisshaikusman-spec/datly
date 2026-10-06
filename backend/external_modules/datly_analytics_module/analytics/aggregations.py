from .models import AnalyticsError

# Maps allowed string aggregations to Pandas aggregation functions
AGGREGATION_MAP = {
    "sum": "sum",
    "mean": "mean",
    "average": "mean",
    "count": "count",
    "min": "min",
    "max": "max",
    "median": "median"
}

def get_aggregation(agg_name: str) -> str:
    """Returns the corresponding pandas aggregation string, or raises AnalyticsError."""
    if agg_name not in AGGREGATION_MAP:
        raise AnalyticsError("UNSUPPORTED_AGGREGATION", f"Aggregation '{agg_name}' is not supported.")
    return AGGREGATION_MAP[agg_name]
