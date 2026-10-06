import shutil
import tempfile
from datetime import UTC
from pathlib import Path

import pandas as pd
import pytest

from app.core.exceptions import DatlyException
from app.models.analysis_plan import (
    AnalysisPlan,
    JoinCondition,
    Operation,
    VisualizationType,
)
from app.models.dataset import DatasetMetadata
from app.repositories.workspace_store import WorkspaceStore, generate_unique_alias
from app.services.analytics.multi_engine import execute_multi_plan
from app.services.visualization.chart_selector import select_visualizations


@pytest.fixture
def sample_frames():
    sales_df = pd.DataFrame({
        "date": ["2026-01-01", "2026-01-02", "2026-01-03", "2026-01-04", "2026-01-05"],
        "customer_id": ["C101", "C102", "C101", "C103", "C102"],
        "region": ["South", "North", "South", "South", "North"],
        "revenue": [250000, 180000, 144000, 200000, 350000]
    })
    cust_df = pd.DataFrame({
        "customer_id": ["C101", "C102", "C103"],
        "customer_name": ["Acme Corp", "Beta Labs", "Gamma Inc"],
        "tier": ["Enterprise", "SMB", "Enterprise"]
    })
    return {"sales": sales_df, "customers": cust_df}


def test_two_dataset_join(sample_frames):
    """Test joining sales and customers on customer_id and computing top customers by revenue."""
    plan = AnalysisPlan(
        operation=Operation.top_n,
        dataset="sales",
        joins=[
            JoinCondition(
                left="sales",
                right="customers",
                left_on="customer_id",
                right_on="customer_id",
                how="inner"
            )
        ],
        group_column="customer_name",
        metric_column="revenue",
        aggregation="sum",
        limit=5,
        visualizations=[VisualizationType.bar]
    )

    result_dict, verif = execute_multi_plan(sample_frames, plan)

    rows = result_dict.get("rows", [])
    assert len(rows) > 0
    assert "customer_name" in rows[0]
    assert "revenue" in rows[0]
    # Top customer should be Beta Labs (180000 + 350000 = 530000)
    assert rows[0]["customer_name"] == "Beta Labs"
    assert rows[0]["revenue"] == 530000

    # Verification block checks
    assert verif.datasets_used == ["sales", "customers"]
    assert len(verif.joins) == 1
    assert verif.joins[0]["left"] == "sales"
    assert verif.joins[0]["right"] == "customers"
    assert verif.row_count_after == len(rows)


def test_join_on_mismatched_types():
    """Test join with incompatible data types (e.g. numeric ID vs string ID) raises clear error."""
    sales_df = pd.DataFrame({
        "customer_id": [101, 102, 103],
        "revenue": [100, 200, 300]
    })
    cust_df = pd.DataFrame({
        "customer_id": ["ABC", "DEF", "GHI"],
        "customer_name": ["A", "B", "C"]
    })
    frames = {"sales": sales_df, "customers": cust_df}

    plan = AnalysisPlan(
        operation=Operation.sum,
        dataset="sales",
        joins=[
            JoinCondition(
                left="sales",
                right="customers",
                left_on="customer_id",
                right_on="customer_id",
                how="inner"
            )
        ],
        metric_column="revenue"
    )

    with pytest.raises(DatlyException) as exc_info:
        execute_multi_plan(frames, plan)

    assert exc_info.value.code == "JOIN_TYPE_MISMATCH"
    assert "incompatible types" in exc_info.value.message


def test_pie_chart_rule():
    """Test pie chart rule: pie only when <= 8 categories and values >= 0; otherwise fallback to bar."""
    # <= 8 categories and all positive -> pie allowed
    small_df = pd.DataFrame({
        "region": ["North", "South", "East", "West"],
        "revenue": [100, 200, 300, 400]
    })
    specs = select_visualizations(small_df, [VisualizationType.pie], "region", "revenue")
    assert len(specs) == 1
    assert specs[0].type == "pie"

    # > 8 categories -> falls back to bar
    large_df = pd.DataFrame({
        "category": [f"Cat_{i}" for i in range(12)],
        "revenue": [10 * i for i in range(12)]
    })
    specs_large = select_visualizations(large_df, [VisualizationType.pie], "category", "revenue")
    assert len(specs_large) == 1
    assert specs_large[0].type == "bar"

    # Negative values -> falls back to bar
    neg_df = pd.DataFrame({
        "region": ["North", "South"],
        "profit": [-50, 100]
    })
    specs_neg = select_visualizations(neg_df, [VisualizationType.pie], "region", "profit")
    assert len(specs_neg) == 1
    assert specs_neg[0].type == "bar"


def test_two_charts_selection():
    """Test that multiple visualization types (e.g. line and pie) return multiple specs."""
    df = pd.DataFrame({
        "month": ["Jan", "Feb", "Mar", "Apr"],
        "revenue": [1000, 1500, 2000, 2500]
    })
    specs = select_visualizations(
        df,
        [VisualizationType.line, VisualizationType.pie],
        group_col="month",
        metric_col="revenue"
    )
    assert len(specs) == 2
    types = [s.type for s in specs]
    assert "line" in types
    assert "pie" in types


def test_workspace_persistence_across_restart():
    """Test that datasets persist to disk (Parquet + JSON metadata) and reload across store restarts."""
    temp_dir = tempfile.mkdtemp()
    try:
        storage_path = Path(temp_dir)
        store1 = WorkspaceStore(data_dir=storage_path)
        ws = store1.create_workspace()
        ws_id = ws.id

        df = pd.DataFrame({
            "col_a": [1, 2, 3],
            "col_b": ["x", "y", "z"]
        })
        from datetime import datetime
        meta = DatasetMetadata(
            dataset_id="test_ds_1",
            filename="sales_test.csv",
            file_type="csv",
            rows=3,
            columns=2,
            workspace_id=ws_id,
            created_at=datetime.now(UTC),
        )
        store1.save_dataset(meta, df, ws_id)

        assert meta.alias.startswith("sales_test")
        assert meta.rows == 3
        assert meta.columns == 2

        # Verify physical files exist on disk
        parquet_file = storage_path / ws_id / f"{meta.dataset_id}.parquet"
        json_file = storage_path / ws_id / f"{meta.dataset_id}.json"
        assert parquet_file.exists()
        assert json_file.exists()

        # Simulate app restart by initializing a brand new store
        store2 = WorkspaceStore(data_dir=storage_path)
        reloaded_datasets = store2.list_workspace_datasets(ws_id)
        assert len(reloaded_datasets) == 1
        assert reloaded_datasets[0].dataset_id == meta.dataset_id
        assert reloaded_datasets[0].alias == meta.alias

        reloaded_df = store2.get_dataset(meta.dataset_id)
        assert reloaded_df is not None
        assert len(reloaded_df) == 3
        assert list(reloaded_df["col_a"]) == [1, 2, 3]

        # Test dataset delete
        deleted = store2.delete_dataset(ws_id, meta.dataset_id)
        assert deleted is True
        assert len(store2.list_workspace_datasets(ws_id)) == 0
        assert not parquet_file.exists()
        assert not json_file.exists()
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_unique_alias_generator():
    """Test alias generation handles duplicates with numerical suffixes."""
    existing = {"sales", "sales_1"}
    alias = generate_unique_alias("sales.csv", existing)
    assert alias == "sales_2"
