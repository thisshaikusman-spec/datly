import json
import logging
import os
import re

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import DatlyException

logger = logging.getLogger("datly.ai")


def _extract_json_from_text(text: str) -> str:
    """
    Extract JSON from LLM response that may contain markdown code fences.
    Handles: ```json {...} ```, ``` {...} ```, or raw {...}
    """
    if not text:
        raise ValueError("Empty response from LLM")

    # Strip markdown code fences
    text = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()

    # Find the first {...} block
    brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace_match:
        return brace_match.group(1).strip()

    # If none found, return as-is and let json.loads fail with a clear error
    return text


def _nlp_fallback_plan(user_prompt: str, schema_columns: list[str] | None = None) -> str:
    """
    Question-aware NLP fallback planner.
    Analyzes the user question and returns a sensible AnalysisPlan JSON.
    This is ONLY used when the LLM API is unavailable.
    Never hardcodes a fixed answer – always derives the plan from the actual question.
    """
    # Extract only the user question if the full prompt was passed
    match = re.search(r'USER QUESTION:\s*"([^"]+)"', user_prompt, re.IGNORECASE)
    raw_question = match.group(1).strip() if match else user_prompt.strip()
    q = raw_question.lower()

    # Detect column from question
    def pick_column(candidates: list[str], keywords: list[str]) -> str | None:
        if schema_columns:
            for kw in keywords:
                for col in schema_columns:
                    if kw in col.lower():
                        return col
        return None

    revenue_kws = ["revenue", "sales", "income", "earnings", "profit", "amount", "price", "cost", "value"]
    city_kws = ["city", "region", "location", "area", "district", "zone", "state", "country"]
    date_kws = ["date", "time", "year", "month", "week", "day", "period"]

    metric_col = pick_column(schema_columns or [], revenue_kws)
    if not metric_col and schema_columns:
        # Find any column mentioned in question
        for col in schema_columns:
            if col.lower() in q:
                metric_col = col
                break
    if not metric_col:
        metric_col = "revenue"

    group_col = pick_column(schema_columns or [], city_kws)
    if not group_col and schema_columns:
        for col in schema_columns:
            if col.lower() in q and col != metric_col:
                group_col = col
                break
    if not group_col and schema_columns:
        for col in schema_columns:
            if col != metric_col and not any(skip in col.lower() for skip in ["id", "date", "time", "year", "revenue", "price", "profit", "cost"]):
                group_col = col
                break

    # Check if question is off-topic (e.g., "What is my name?", "Who are you?", conversational)
    analytics_kws = (
        revenue_kws + city_kws + date_kws + [
            "count", "how many", "total", "sum", "average", "mean", "min", "max",
            "highest", "lowest", "top", "bottom", "least", "most", "breakdown",
            "by", "per", "records", "rows", "entries", "dataset", "data",
            "chart", "histogram", "graph", "plot", "line", "pie", "bar", "area", "box"
        ]
    )
    has_analytics_kw = any(kw in q for kw in analytics_kws)
    has_schema_col = any(col.lower() in q for col in (schema_columns or []))

    if not has_analytics_kw and not has_schema_col:
        return json.dumps({
            "unanswerable": True,
            "reason": f"The question '{raw_question}' cannot be answered from the dataset."
        })

    # ─── PIE CHART ───
    if "pie" in q:
        pie_grp = group_col
        if not pie_grp or any(skip in pie_grp.lower() for skip in ["date", "time", "id"]):
            for col in (schema_columns or []):
                if col != metric_col and any(kw in col.lower() for kw in ["category", "segment", "region", "channel", "method", "priority", "city"]):
                    pie_grp = col
                    break
        return json.dumps({
            "operation": "group_by",
            "group_column": pie_grp or (schema_columns[0] if schema_columns else "category"),
            "metric_column": metric_col,
            "aggregation": "sum",
            "sort": "desc",
            "limit": 8,
            "visualization": "pie",
            "explicit_visualization": True
        })

    # ─── HISTOGRAM & BOX PLOT ───
    if "histogram" in q:
        return json.dumps({
            "operation": "sort",
            "sort_column": metric_col or (schema_columns[0] if schema_columns else "revenue"),
            "sort": "asc",
            "limit": 1000,
            "visualization": "histogram",
            "explicit_visualization": True
        })

    if "box" in q:
        return json.dumps({
            "operation": "sort",
            "sort_column": metric_col or (schema_columns[0] if schema_columns else "revenue"),
            "sort": "asc",
            "limit": 1000,
            "visualization": "box",
            "explicit_visualization": True
        })

    # ─── LINE & AREA CHART ───
    if any(kw in q for kw in ["line chart", "line graph", "trend chart", "area chart", "area graph"]):
        date_col = None
        for col in (schema_columns or []):
            if any(dk in col.lower() for dk in ["date", "time", "year", "month"]):
                date_col = col
                break
        viz = "area" if "area" in q else "line"
        return json.dumps({
            "operation": "trend" if date_col else "group_by",
            "group_column": date_col or group_col or (schema_columns[0] if schema_columns else "order_date"),
            "metric_column": metric_col,
            "aggregation": "sum",
            "visualization": viz,
            "explicit_visualization": True
        })

    # ─── COUNT / HOW MANY ───
    if any(kw in q for kw in ["how many", "count", "total records", "number of records", "rows", "entries"]):
        return json.dumps({"operation": "count", "metric_column": None, "visualization": "table"})

    # ─── GROUP_BY (highest/lowest/top by a category) ───
    if group_col and any(kw in q for kw in ["highest", "top", "most", "maximum", "max", "largest", "biggest", "best"]):
        return json.dumps({
            "operation": "group_by",
            "group_column": group_col,
            "metric_column": metric_col,
            "aggregation": "sum",
            "sort": "desc",
            "limit": 1,
            "visualization": "bar"
        })

    if group_col and any(kw in q for kw in ["lowest", "least", "minimum", "min", "smallest", "worst", "bottom"]):
        return json.dumps({
            "operation": "group_by",
            "group_column": group_col,
            "metric_column": metric_col,
            "aggregation": "sum",
            "sort": "asc",
            "limit": 1,
            "visualization": "bar"
        })

    if group_col and any(kw in q for kw in ["by ", "per ", "breakdown", "each ", "chart", "graph"]):
        viz = "bar"
        if "line" in q:
            viz = "line"
        elif "pie" in q:
            viz = "pie"
        return json.dumps({
            "operation": "group_by",
            "group_column": group_col,
            "metric_column": metric_col,
            "aggregation": "sum",
            "sort": "desc",
            "limit": 10,
            "visualization": viz,
            "explicit_visualization": bool(viz != "bar" or "bar" in q)
        })

    # ─── AVERAGE / MEAN ───
    if any(kw in q for kw in ["average", "mean", "avg"]):
        return json.dumps({"operation": "average", "metric_column": metric_col, "visualization": "table"})

    # ─── MIN ───
    if any(kw in q for kw in ["minimum", "lowest", "least", "smallest", "min"]):
        return json.dumps({"operation": "min", "metric_column": metric_col, "visualization": "table"})

    # ─── MAX ───
    if any(kw in q for kw in ["maximum", "highest", "most", "biggest", "max"]):
        return json.dumps({"operation": "max", "metric_column": metric_col, "visualization": "table"})

    # ─── SUM / TOTAL ───
    if any(kw in q for kw in ["total", "sum", "aggregate", "combined", "overall"]):
        return json.dumps({"operation": "sum", "metric_column": metric_col, "visualization": "table"})

    if has_schema_col:
        return json.dumps({"operation": "sort", "sort_column": metric_col, "sort": "desc", "limit": 10, "visualization": "table"})

    return json.dumps({
        "unanswerable": True,
        "reason": f"The question '{raw_question}' cannot be answered from the dataset."
    })


class NvidiaLLMClient:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.model = settings.NVIDIA_MODEL
        self.base_url = settings.NVIDIA_BASE_URL

    def _get_client(self) -> AsyncOpenAI:
        if not self.api_key:
            raise DatlyException(
                code="LLM_NOT_CONFIGURED",
                message="NVIDIA API Key is missing. Cannot reach LLM.",
                status_code=500
            )
        return AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=60.0
        )

    async def get_structured_response(self, system_prompt: str, user_prompt: str, schema_columns: list[str] | None = None) -> str:
        client = self._get_client()

        logger.info(f"[ANALYSIS] Calling LLM model={self.model}")
        try:
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=512
            )
            raw = str(response.choices[0].message.content)
            logger.info(f"[ANALYSIS] LLM raw response: {raw[:300]}")
            return _extract_json_from_text(raw)

        except DatlyException:
            raise
        except Exception as e:  # noqa: BLE001
            logger.error(f"[ANALYSIS] NVIDIA API Error: {e!s}")
            if os.getenv("DATLY_USE_MOCK_LLM", "").lower() in ("true", "1"):
                logger.warning("[ANALYSIS] Using mock LLM for testing.")
                return _nlp_fallback_plan(user_prompt, schema_columns=schema_columns)
            raise DatlyException(
                code="LLM_UNAVAILABLE",
                message="AI service is currently unavailable. Please check your API key or connection.",
                status_code=503
            )


nvidia_client = NvidiaLLMClient()
