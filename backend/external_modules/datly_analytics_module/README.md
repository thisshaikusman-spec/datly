# DATLY Analytics Engine Module

## 1. Overview
The **DATLY Analytics Engine** is a standalone, deterministic Python module designed for the DATLY project. It receives a Pandas DataFrame and a validated `AnalysisPlan`, performs operations strictly using Pandas and NumPy, and returns structured, predictable results. 

Crucially, **the LLM NEVER performs any calculations**. The LLM is only responsible for planning the query, while this module executes the deterministic data manipulation.

## 2. Architecture
The module is designed with complete isolation. It contains no external dependencies related to the DATLY backend (no FastAPI, Supabase, LLM SDKs, etc.).

- `engine.py`: The entry point `AnalyticsEngine` that takes a DataFrame and an `AnalysisPlan`, delegating to supported operations.
- `operations.py`: Pure Pandas functions implementing operations like sum, max, average, group_by, filter, sort, etc.
- `aggregations.py`: Maps semantic aggregation names to Pandas functions.
- `filters.py`: Implements deterministic filter operations.
- `visualization.py`: Deterministically selects the optimal visualization format based on the result structure.
- `models.py`: Defines inputs/outputs using Pydantic, ensuring structured responses (`AnalysisResult`, `AnalyticsError`).

## 3. Supported Operations
- `count`
- `sum`
- `average`
- `min`
- `max`
- `filter`
- `group_by`
- `sort`
- `top_n`

## 4. Supported Aggregations
- `sum`
- `mean` (and `average`)
- `count`
- `min`
- `max`
- `median`

## 5. Supported Filters
- `equals`
- `not_equals`
- `greater_than`
- `less_than`
- `greater_than_or_equal`
- `less_than_or_equal`
- `contains`
- `date_before`
- `date_after`
- `date_between`

## 6. Input Format
The engine expects a Pandas DataFrame and a dictionary plan (or Pydantic equivalent):
```json
{
    "operation": "group_by",
    "group_column": "city",
    "metric_column": "revenue",
    "aggregation": "sum",
    "sort": "desc",
    "limit": 1
}
```

## 7. Output Format
Returns an `AnalysisResult` object which serializes into:
```json
{
    "operation": "group_by",
    "columns": ["city", "revenue"],
    "rows": [
        {
            "city": "Coimbatore",
            "revenue": 8250000.0
        }
    ],
    "row_count": 1,
    "visualization": {
        "type": "bar",
        "x": "city",
        "y": "revenue",
        "title": "revenue by city"
    }
}
```

## 8. Security Design
- **No eval/exec/os code**: Operations are strictly routed through an explicit `OPERATION_MAP`.
- **Predefined functions only**: Arbitrary string execution or dynamically generated query strings are explicitly blocked.
- **Type safety**: Extensive validation handles absent columns and invalid types before Pandas applies calculations.

## 9. How to Run Tests
To execute tests and linting:
```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install pytest ruff

# 2. Run tests
pytest tests/

# 3. Run linter
ruff check .
```

## 10. Integration Example
To integrate into DATLY's backend:
```python
import pandas as pd
from analytics.engine import AnalyticsEngine
from analytics.models import AnalyticsError

# 1. Create instance
engine = AnalyticsEngine()

# 2. Prepare data
df = pd.DataFrame({"city": ["Coimbatore"], "revenue": [8250000]})
analysis_plan = {
    "operation": "sum",
    "metric_column": "revenue"
}

# 3. Execute
try:
    result = engine.execute(df, analysis_plan)
    print(result.rows)
except AnalyticsError as e:
    print(f"Error [{e.code}]: {e.message}")
```

---

## Final Handoff Summary
- **Files Created**: `requirements.txt`, `.env.example`, `models.py`, `filters.py`, `aggregations.py`, `operations.py`, `visualization.py`, `engine.py`, and comprehensive `tests/`.
- **Input/Output Contract**: Dicts/Pydantic models mapping to DataFrame inputs and structured JSON/dict outputs.
- **Error Codes**: Missing columns (`MISSING_COLUMN`), incompatible operation (`INCOMPATIBLE_OPERATION`), unsupported formats (`UNSUPPORTED_OPERATION`), etc.
- **Test Results**: 13/13 passing in `pytest` verifying operations, filters, sorting, visualization determinism, and core security constraints.
- **Ruff Result**: Passed format checks and explicit rule validations.
- **Limitations**: The Analytics Engine requires a pre-loaded, pre-cleaned DataFrame (in-memory execution). Does not fetch from a DB directly. 
