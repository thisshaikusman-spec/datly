# DATLY Backend

Backend for DATLY — Schema-Agnostic Natural Language Data Analyst with Multi-Dataset Workspace Support.

## Core Principles
1. **Deterministic Execution**: The LLM outputs an `AnalysisPlan` (JSON). All mathematical aggregations, joins, and calculations are computed deterministically by Pandas. The LLM never computes numbers.
2. **Multi-Dataset Workspaces**: Users can upload multiple datasets per chat/workspace (up to 10), query across datasets, join tables, and view multi-chart visualizations.
3. **Transparent Verification**: Every answer returns a `VerificationBlock` detailing row counts before/after, applied filters, and datasets/joins used.
4. **Multilingual Voice**: Integrated with Sarvam AI STT for accurate Indic and English speech transcription.

## Setup

1. **Virtual Environment**:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

2. **Install Dependencies & Local Analytics Module**:
   ```bash
   pip install -r requirements.txt
   pip install -e external_modules/datly_analytics_module
   ```

3. **Configure Environment**:
   Copy `.env.example` to `.env` and configure:
   - `NVIDIA_API_KEY`: NVIDIA NIM API key for LLM planner
   - `SARVAM_API_KEY`: Sarvam AI API key for STT
   - `DATA_DIR`: Disk persistence directory for workspaces (defaults to `./data`)

4. **Run Server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

## Workspace & Dataset Persistence
Datasets are saved on disk as Parquet files with JSON metadata under `data/{workspace_id}/{dataset_id}.parquet`.
Each dataset is given a human-friendly alias (e.g. `sales_2024.csv` -> `sales_2024`) for clean reference in queries and joins.

## Testing & Code Quality
- Run test suite:
  ```bash
  pytest tests/
  ```
- Run linter:
  ```bash
  ruff check .
  ```

