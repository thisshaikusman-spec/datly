import os
import sys

import pandas as pd
import pytest

ext_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../external_modules/datly_analytics_module"))
if ext_path not in sys.path:
    sys.path.insert(0, ext_path)

from analytics.operations import (
    OPERATION_MAP,
    calculate_average,
    calculate_count,
    calculate_sum,
    group_by,
    top_n,
)


@pytest.fixture
def sample_sales_df():
    return pd.DataFrame({
        "customer_id": [1, 2, 3, 4, 5, 6],
        "customer_name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank"],
        "region": ["South", "South", "North", "North", "South", "East"],
        "revenue": [100.0, 200.0, 300.0, 400.0, 50.0, 150.0],
        "order_date": pd.to_datetime([
            "2024-01-01", "2024-01-02", "2024-01-01", "2024-01-03", "2024-01-04", "2024-01-02"
        ]),
    })


# ─── BUG A: FILTERS APPLIED TO ALL OPERATIONS ─────────────────────────────────

def test_sum_applies_filters(sample_sales_df):
    plan = {
        "operation": "sum",
        "metric_column": "revenue",
        "filters": [{"column": "region", "operator": "equals", "value": "South"}],
    }
    # South revenue: 100 + 200 + 50 = 350
    res = calculate_sum(sample_sales_df, plan)
    assert res.iloc[0]["revenue"] == 350.0


def test_average_applies_filters(sample_sales_df):
    plan = {
        "operation": "average",
        "metric_column": "revenue",
        "filters": [{"column": "region", "operator": "equals", "value": "North"}],
    }
    # North revenue: (300 + 400) / 2 = 350
    res = calculate_average(sample_sales_df, plan)
    assert res.iloc[0]["revenue"] == 350.0


def test_count_applies_filters(sample_sales_df):
    plan = {
        "operation": "count",
        "filters": [{"column": "region", "operator": "equals", "value": "South"}],
    }
    res = calculate_count(sample_sales_df, plan)
    assert res.iloc[0]["count"] == 3


def test_group_by_applies_filters(sample_sales_df):
    plan = {
        "operation": "group_by",
        "group_column": "region",
        "metric_column": "revenue",
        "aggregation": "sum",
        "filters": [{"column": "region", "operator": "equals", "value": "South"}],
    }
    res = group_by(sample_sales_df, plan)
    assert len(res) == 1
    assert res.iloc[0]["region"] == "South"
    assert res.iloc[0]["revenue"] == 350.0


# ─── BUG B: TREND & COMPARISON IN OPERATION_MAP ───────────────────────────────

def test_trend_operation_exists_and_sorts_asc(sample_sales_df):
    assert "trend" in OPERATION_MAP
    trend_func = OPERATION_MAP["trend"]
    plan = {
        "operation": "trend",
        "group_column": "order_date",
        "metric_column": "revenue",
        "aggregation": "sum",
    }
    res = trend_func(sample_sales_df, plan)
    assert len(res) > 0
    # Dates must be sorted ascending for trend
    dates = pd.to_datetime(res["order_date"]).tolist()
    assert dates == sorted(dates)


def test_comparison_operation_exists(sample_sales_df):
    assert "comparison" in OPERATION_MAP
    comp_func = OPERATION_MAP["comparison"]
    plan = {
        "operation": "comparison",
        "group_column": "region",
        "metric_column": "revenue",
        "aggregation": "sum",
    }
    res = comp_func(sample_sales_df, plan)
    assert len(res) > 0


# ─── BUG C: TOP_N ACCEPTS LIMIT AND RANKS GROUPS ─────────────────────────────

def test_top_n_with_limit_fallback(sample_sales_df):
    plan = {
        "operation": "top_n",
        "metric_column": "revenue",
        "limit": 2,
    }
    # Highest revenues: 400, 300
    res = top_n(sample_sales_df, plan)
    assert len(res) == 2
    assert res.iloc[0]["revenue"] == 400.0
    assert res.iloc[1]["revenue"] == 300.0


def test_top_n_with_group_column(sample_sales_df):
    plan = {
        "operation": "top_n",
        "group_column": "region",
        "metric_column": "revenue",
        "aggregation": "sum",
        "limit": 2,
    }
    # Region sums: North=700, South=350, East=150
    # Top 2 regions: North (700), South (350)
    res = top_n(sample_sales_df, plan)
    assert len(res) == 2
    assert res.iloc[0]["region"] == "North"
    assert res.iloc[0]["revenue"] == 700.0
    assert res.iloc[1]["region"] == "South"
    assert res.iloc[1]["revenue"] == 350.0
