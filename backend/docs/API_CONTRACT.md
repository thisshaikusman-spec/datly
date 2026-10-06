# DATLY API Contract

This document serves as the official API contract for the DATLY frontend integration.

## 1. Base URL
All API requests should be prefixed with the following base URL:
`http://localhost:8000/api/v1`

## 2. Authentication Status
Currently, the DATLY API does **not** require authentication. All endpoints are publicly accessible for development.

## 3. Endpoint List

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Verify that the backend is running. |
| POST | `/datasets/upload` | Upload a new dataset (CSV, XLSX, JSON). Accepts optional `X-Workspace-Id` header. |
| GET | `/datasets/{dataset_id}` | Retrieve metadata for an uploaded dataset. |
| GET | `/datasets/{dataset_id}/schema` | Retrieve inferred schema information. |
| GET | `/datasets/{dataset_id}/profile` | Retrieve dataset statistical profile. |
| POST | `/datasets/{dataset_id}/analyze` | Submit a natural language question for single-dataset analysis. |
| POST | `/workspaces` | Create or get an analysis workspace. |
| GET | `/workspaces/{workspace_id}/datasets` | List all datasets uploaded in a workspace. |
| DELETE | `/workspaces/{workspace_id}/datasets/{dataset_id}` | Remove a dataset from a workspace. |
| POST | `/workspaces/{workspace_id}/analyze` | Submit a question targeting one, multiple, or joined datasets in a workspace. |
| POST | `/voice/transcribe` | Transcribe an audio file into text using Sarvam AI STT. |
| POST | `/voice/analyze` | Transcribe voice and run single or multi-dataset analysis in a single step. |

---

## 4. Multi-Dataset & Workspace Workflow

1. **Create or Reference Workspace**: Client maintains a `workspace_id` (e.g. `ws_12345678`).
2. **Upload Datasets**: Each `POST /datasets/upload` includes `X-Workspace-Id: <ws_id>`. The backend assigns clean, unique aliases (e.g. `sales`, `customers`).
3. **List Active Datasets**: `GET /workspaces/{ws_id}/datasets` provides all active datasets, aliases, rows, and columns.
4. **Multi-Dataset Query**: `POST /workspaces/{ws_id}/analyze` with question and optional `dataset_ids` filter:
```json
{
    "question": "What is the total revenue by customer segment?",
    "dataset_ids": ["ds_1", "ds_2"]
}
```
5. **Execution & Deterministic Joins**:
   - The LLM outputs an `AnalysisPlan` specifying datasets and join keys (e.g. `joins: [{left: "sales", right: "customers", on: "customer_id", how: "inner"}]`).
   - Pandas performs the join deterministically. The LLM never computes numbers.
   - If join keys have mismatched types or explode rows (>1,000,000), safe errors are returned.

---

## 5. Request & Response Contracts

### POST `/workspaces/{workspace_id}/analyze`
**Request:**
```json
{
    "question": "Show revenue by region as a bar chart and pie chart",
    "dataset_ids": ["ds_sales_2024", "ds_regions"]
}
```
**Response:**
```json
{
    "success": true,
    "workspace_id": "ws_12345678",
    "dataset_id": "ds_sales_2024",
    "question": "Show revenue by region as a bar chart and pie chart",
    "answer": "North region generated 4,500,000 in revenue, followed by South with 3,200,000.",
    "result": {
        "data": [
            {"region": "North", "revenue": 4500000},
            {"region": "South", "revenue": 3200000}
        ]
    },
    "visualization": {
        "type": "bar",
        "x": "region",
        "y": "revenue",
        "title": "Revenue by Region"
    },
    "visualizations": [
        {
            "type": "bar",
            "x": "region",
            "y": "revenue",
            "title": "Revenue by Region"
        },
        {
            "type": "pie",
            "x": "region",
            "y": "revenue",
            "title": "Revenue Distribution by Region"
        }
    ],
    "verification": {
        "row_count_before": 1000,
        "row_count_after": 2,
        "datasets_used": ["sales", "regions"],
        "joins": ["sales ⋈ regions on customer_id"],
        "filters_applied": ["status == 'completed'"],
        "operation": "group_by",
        "metric_column": "revenue",
        "group_column": "region",
        "aggregation": "sum"
    }
}
```

---

## 6. Visualization Contract

The backend **does not** render chart images. It returns a list of strict `VisualizationSpec` objects (`visualizations`) that the frontend maps to UI charting components.

**Supported Types:**
- `bar`: For categorical comparisons or rankings.
- `line`: For temporal/trend analysis.
- `pie`: For part-to-whole distributions (automatically enforced: numeric values positive, <=7 slices, else rolled into "Other").
- `kpi`: For single aggregated summary metrics.
- `scatter`: For numeric vs. numeric comparisons.
- `table`: For tabular data without a direct chart mapping.
- `none`: For scalar values or empty queries.

---

## 7. Error Format & Codes

All structured errors follow this format:
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable explanation of the error."
    }
}
```

**Known Error Codes:**
- `DATASET_NOT_FOUND`: The requested dataset ID does not exist in the workspace.
- `WORKSPACE_LIMIT_EXCEEDED`: Maximum datasets (10) reached in workspace.
- `JOIN_KEY_NOT_FOUND`: Specified join column does not exist on target datasets.
- `JOIN_TYPE_MISMATCH`: Key columns have incompatible types across datasets.
- `ROW_EXPLOSION_ERROR`: Join resulted in >1,000,000 rows.
- `LLM_NOT_CONFIGURED`: NVIDIA API Key is missing.
- `NVIDIA_API_FAILURE`: Upstream failure from the NVIDIA NIM endpoint.
- `INVALID_ANALYSIS_PLAN`: The LLM returned an invalid or malformed schema after repair attempts.
- `ANALYTICS_ERROR`: The execution engine failed to parse or execute the deterministic pandas logic.
