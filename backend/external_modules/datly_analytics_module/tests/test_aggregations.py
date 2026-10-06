import pytest
from analytics.aggregations import get_aggregation
from analytics.models import AnalyticsError


def test_get_aggregation():
    assert get_aggregation("sum") == "sum"
    assert get_aggregation("average") == "mean"
    assert get_aggregation("mean") == "mean"
    
    with pytest.raises(AnalyticsError, match="not supported"):
        get_aggregation("invalid_agg")
