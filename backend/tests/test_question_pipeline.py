from datetime import UTC, datetime

import pandas as pd
import pytest

from app.core.exceptions import DatlyException
from app.models.dataset import DatasetMetadata
from app.repositories.dataset_store import dataset_store
from app.services.analysis_service import AnalysisService


@pytest.fixture(autouse=True)
def setup_dataset():
    df = pd.DataFrame({
        "city": ["Coimbatore", "Chennai", "Bangalore", "Madurai"],
        "revenue": [8250000, 5000000, 12000000, 2100000]
    })
    meta = DatasetMetadata(
        dataset_id="ds_test_pipeline",
        filename="sales.csv",
        file_type="csv",
        rows=4,
        columns=2,
        created_at=datetime.now(UTC)
    )
    dataset_store.save_dataset(meta, df)
    yield
    dataset_store._dataframes.pop("ds_test_pipeline", None)
    dataset_store._metadata.pop("ds_test_pipeline", None)


@pytest.mark.asyncio
async def test_pipeline_total_revenue():
    # TEST 1: What is the total revenue?
    res = await AnalysisService.analyze("ds_test_pipeline", "What is the total revenue?")
    assert res.success is True
    # 8250000 + 5000000 + 12000000 + 2100000 = 27,350,000
    assert res.result.get("value") == 27350000.0 or res.result.get("value") == 27350000
    assert "27,350,000" in res.answer


@pytest.mark.asyncio
async def test_pipeline_highest_revenue_city():
    # TEST 2: Which city generated the highest revenue?
    res = await AnalysisService.analyze("ds_test_pipeline", "Which city generated the highest revenue?")
    assert res.success is True
    assert res.analysis_plan.operation.value == "group_by"
    assert res.analysis_plan.group_column == "city"
    assert res.analysis_plan.sort == "desc"
    assert res.analysis_plan.limit == 1
    # Bangalore is highest with 12,000,000
    assert "Bangalore" in res.answer
    assert "12,000,000" in res.answer


@pytest.mark.asyncio
async def test_pipeline_lowest_revenue_city():
    # TEST 3: Which city generated the lowest revenue?
    res = await AnalysisService.analyze("ds_test_pipeline", "Which city generated the lowest revenue?")
    assert res.success is True
    assert res.analysis_plan.operation.value == "group_by"
    assert res.analysis_plan.group_column == "city"
    assert res.analysis_plan.sort == "asc"
    assert res.analysis_plan.limit == 1
    # Madurai is lowest with 2,100,000
    assert "Madurai" in res.answer
    assert "2,100,000" in res.answer


@pytest.mark.asyncio
async def test_pipeline_record_count():
    # TEST 4: How many records are in the dataset?
    res = await AnalysisService.analyze("ds_test_pipeline", "How many records are in the dataset?")
    assert res.success is True
    assert res.analysis_plan.operation.value == "count"
    assert res.result.get("value") == 4
    assert "4" in res.answer


@pytest.mark.asyncio
async def test_pipeline_unrelated_question():
    # Off-topic question like "What is my name?"
    # Must NEVER return "The sum of revenue is 27,350,000"
    with pytest.raises(DatlyException) as exc_info:
        await AnalysisService.analyze("ds_test_pipeline", "What is my name?")
    assert exc_info.value.code in ("UNANSWERABLE_QUESTION", "INVALID_ANALYSIS_PLAN")


@pytest.mark.asyncio
async def test_pipeline_no_dataset_selected():
    # If no dataset selected
    with pytest.raises(DatlyException) as exc_info:
        await AnalysisService.analyze("", "What is the total revenue?")
    assert exc_info.value.code == "NO_DATASET_SELECTED"
    assert exc_info.value.message == "No dataset selected. Please upload a dataset first."


@pytest.mark.asyncio
async def test_pipeline_generic_pie_chart():
    # "Create an pie chart." without explicit columns must succeed and return pie chart
    res = await AnalysisService.analyze("ds_test_pipeline", "Create an pie chart.")
    assert res.success is True
    assert res.visualization is not None
    assert res.visualization.type.value == "pie"
    assert res.analysis_plan.operation.value == "group_by"
    assert res.analysis_plan.aggregation.value == "sum"
    assert res.analysis_plan.group_column == "city"
    assert res.analysis_plan.metric_column == "revenue"


@pytest.mark.asyncio
async def test_pipeline_generic_bar_chart():
    # "Show me a bar chart." without explicit columns must succeed and return bar chart
    res = await AnalysisService.analyze("ds_test_pipeline", "Show me a bar chart.")
    assert res.success is True
    assert res.visualization is not None
    assert res.visualization.type.value == "bar"
    assert res.analysis_plan.operation.value == "group_by"
    assert res.analysis_plan.aggregation.value == "sum"

