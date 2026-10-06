# DATLY

> **Schema-Agnostic Natural Language Data Analyst** with Multi-Dataset Workspace Support & Indic/English Voice Interaction.

DATLY allows users to upload multiple tabular datasets (CSV, Excel, JSON), ask analytical questions in natural language (or via multilingual voice), and receive deterministic answers, interactive visualizations, and complete step-by-step verification blocks.

---

## Key Features

- **Strictly Deterministic Calculation**: The LLM acts solely as a query planner producing structured JSON (`AnalysisPlan`). All math, aggregations, and joins are executed deterministically by Pandas.
- **Multi-Dataset Workspaces**: Upload and manage multiple datasets per chat/workspace (up to 10 datasets), perform cross-dataset joins (inner/left), and query multiple tables.
- **Verification Engine**: Every answer includes full provenance details (row counts before/after, joins performed, filters applied, and operations).
- **Rich Visualizations**: Interactive bar charts, trend line charts, scatter plots, grouped pie charts, summary KPI cards, and raw data tables.
- **Multilingual Voice Analysis**: Integrated with Sarvam AI STT for voice queries in Indic languages (Tamil, Hindi, Telugu, Malayalam) and English.

---

## Project Structure

```
├── backend/
│   ├── app/                    # FastAPI application
│   │   ├── api/                # REST endpoints (datasets, workspaces, voice)
│   │   ├── models/             # Pydantic schemas and analysis plan contracts
│   │   ├── repositories/       # Workspace store with Parquet persistence
│   │   └── services/           # Analytics engine, AI planner, STT/TTS
│   ├── external_modules/       # Local editable Python analytics engine
│   ├── tests/                  # Pytest test suite (53 tests)
│   └── requirements.txt        # Backend dependencies
├── frontend/
│   ├── src/
│   │   ├── components/         # React components (Chat, Charts, Verification)
│   │   ├── pages/              # ChatPage workspace interface
│   │   └── services/           # Axios API client
│   └── package.json            # Frontend dependencies
└── README.md
```

---

## Getting Started

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # On Windows
# source .venv/bin/activate  # On Linux/macOS

pip install -r requirements.txt
pip install -e external_modules/datly_analytics_module

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your NVIDIA_API_KEY and SARVAM_API_KEY

uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to start analyzing datasets.

---

## Testing

```bash
cd backend
pytest tests/
```
