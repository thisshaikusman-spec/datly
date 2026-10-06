import json
import logging

from app.core.exceptions import DatlyException
from app.models.analysis_plan import AnalysisPlan
from app.models.schema import DatasetProfile, DatasetSchema
from app.services.ai.nvidia_client import _nlp_fallback_plan, nvidia_client

logger = logging.getLogger("datly.ai.planner")


# ─── Tamil / Hindi / Malayalam / Telugu keyword normalizer ──────────────────
_MULTILINGUAL_KEYWORDS: dict[str, str] = {
    # Tamil keywords
    "பை சார்ட்": "pie chart", "பை": "pie", "வட்டம்": "pie",
    "லைன் சார்ட்": "line chart", "லைன்": "line", "வரி": "line", "போக்கு": "line",
    "பார் சார்ட்": "bar chart", "பார்": "bar", "கோல்": "bar",
    "ஹிஸ்டோகிராம்": "histogram",
    "ஸ்கேட்டர் பிளாட்": "scatter plot", "ஸ்கேட்டர்": "scatter",
    "ஏரியா சார்ட்": "area chart", "பாக்ஸ் பிளாட்": "box plot",
    "டேபிள்": "table", "அட்டவணை": "table",
    "அதிகமான": "highest", "அதிகம்": "highest", "மிக அதிகம்": "highest", "அதிகபட்சம்": "highest",
    "குறைவான": "lowest", "குறைவு": "lowest", "மிகக் குறைவு": "lowest", "குறைந்தபட்சம்": "lowest",
    "மொத்தம்": "total", "கூட்டு": "sum",
    "சராசரி": "average", "சராசரியான": "average",
    "எண்ணிக்கை": "count", "எத்தனை": "how many",
    "நகரம்": "city", "ஊர்": "city",

    # Hindi keywords
    "पाई चार्ट": "pie chart", "लाइन चार्ट": "line chart", "बार चार्ट": "bar chart",
    "हिस्टोग्राम": "histogram", "स्कैटर प्लॉट": "scatter plot", "एरिया चार्ट": "area chart", "बॉक्स प्लॉट": "box plot",
    "तालिका": "table", "टेबल": "table",
    "सबसे ज्यादा": "highest", "सबसे अधिक": "highest", "ज्यादा": "highest", "अधिकतम": "highest",
    "सबसे कम": "lowest", "कम": "lowest", "न्यूनतम": "lowest",
    "कुल": "total", "जोड़": "sum", "योग": "sum",
    "औसत": "average", "गिनती": "count", "कितने": "how many", "कितनी": "how many",
    "शहर": "city",

    # Malayalam keywords
    "പൈ ചാർട്ട്": "pie chart", "ലൈൻ ചാർട്ട്": "line chart", "ബാർ ചാർട്ട്": "bar chart",
    "ഹിസ്റ്റോഗ്രാം": "histogram", "സ്കാറ്റർ പ്ലോട്ട്": "scatter plot", "ഏരിയ ചാർട്ട്": "area chart", "ബോക്സ് പ്ലോട്ട്": "box plot",
    "പട്ടിക": "table",
    "ഏറ്റവും കൂടുതൽ": "highest", "കൂടുതൽ": "highest", "പരമാവധി": "highest",
    "ഏറ്റവും കുറവ്": "lowest", "കുറവ്": "lowest", "കുറഞ്ഞ": "lowest",
    "ആകെ": "total", "ശരാശരി": "average", "എണ്ണം": "count", "എത്ര": "how many",
    "നഗരത്തിലാണ്": "city", "നഗരത്തിനാണ്": "city", "നഗരം": "city",

    # Telugu keywords
    "పై చార్ట్": "pie chart", "లైన్ చార్ట్": "line chart", "బార్ చార్ట్": "bar chart",
    "హిస్టోగ్రామ్": "histogram", "స్కాటర్ ప్లాట్": "scatter plot", "ఏరియా చార్ట్": "area chart", "బాక్స్ ప్లాట్": "box plot",
    "పట్టిక": "table",
    "అత్యధిక": "highest", "అత్యధికం": "highest", "ఎక్కువ": "highest", "గరిష్ట": "highest",
    "అత్యల్ప": "lowest", "అత్యల్పం": "lowest", "తక్కువ": "lowest", "కనిష్ట": "lowest",
    "సగటు": "average", "సంఖ్య": "count", "ఎన్ని": "how many",
    "నగరంలో": "city", "నగరానికి": "city", "నగరం": "city",
}

def _normalize_question(question: str) -> str:
    """
    Normalize Tamil, Malayalam, Hindi, Telugu into an analytical form
    that preserves dataset column names while translating analytical intent.
    """
    q = question
    for kw, eng_kw in _MULTILINGUAL_KEYWORDS.items():
        q = q.replace(kw, eng_kw)
    return q


# ─── Explicit chart-type detection from raw question ─────────────────────────
_EXPLICIT_CHART_MAP: list[tuple[list[str], str]] = [
    (["pie chart", "pie graph", "pie"], "pie"),
    (["histogram"], "histogram"),
    (["scatter plot", "scatter chart", "scatter"], "scatter"),
    (["area chart", "area graph"], "area"),
    (["box plot", "box chart", "boxplot"], "box"),
    (["line chart", "line graph", "trend chart"], "line"),
    (["bar chart", "bar graph"], "bar"),
    (["show as table", "show table", "as a table", "table"], "table"),
]

def _detect_explicit_chart(question: str) -> str | None:
    """Return the explicit chart type requested by the user, or None."""
    q = question.lower()
    for keywords, chart_type in _EXPLICIT_CHART_MAP:
        if any(kw in q for kw in keywords):
            return chart_type
    return None


def _pick_metric_col(schema_columns: list[str], question: str = "") -> str | None:
    q = question.lower()
    # 1. Mentioned in question
    for col in schema_columns:
        if col.lower() in q and any(kw in col.lower() for kw in [
            "revenue", "sales", "amount", "price", "cost", "value", "income", "profit",
            "quantity", "units", "rating", "count", "days"
        ]):
            return col
    # 2. Known metric names in schema
    for kw in ["revenue", "sales", "profit", "amount", "price", "cost", "units_sold", "value", "income", "customer_rating"]:
        for col in schema_columns:
            if kw in col.lower():
                return col
    # 3. Any column that doesn't look like an ID or date or string categorical
    for col in schema_columns:
        c_lower = col.lower()
        if not any(skip in c_lower for skip in ["id", "date", "year", "month", "time", "day", "flag", "name", "city", "region", "category", "method", "channel", "priority", "segment"]):
            return col
    return schema_columns[-1] if schema_columns else "revenue"


def _pick_categorical_col(schema_columns: list[str], question: str = "", exclude: list[str] | None = None) -> str | None:
    q = question.lower()
    ex = [e.lower() for e in (exclude or [])]
    # 1. Mentioned in question
    for col in schema_columns:
        if col.lower() in q and col.lower() not in ex:
            return col
    # 2. Top dimension/category columns
    for kw in ["product_category", "category", "region", "city", "customer_segment", "segment", "payment_method", "order_channel", "priority", "product"]:
        for col in schema_columns:
            if kw in col.lower() and col.lower() not in ex:
                return col
    # 3. Any column not in exclude and not date/id/metric
    for col in schema_columns:
        c_lower = col.lower()
        if c_lower not in ex and not any(skip in c_lower for skip in ["id", "date", "year", "month", "revenue", "price", "cost", "profit", "amount", "units"]):
            return col
    return None


def _pick_date_col(schema_columns: list[str]) -> str | None:
    for kw in ["order_date", "date", "created_at", "timestamp", "time", "year", "month", "day"]:
        for col in schema_columns:
            if kw in col.lower():
                return col
    return None


def _sanitize_plan_dict(data: dict, question: str, schema_columns: list[str]) -> dict:
    q = question.lower()

    # 1. Clean string "none" or empty strings into None
    for key in ["aggregation", "sort", "sort_column", "group_column", "metric_column"]:
        if key in data and (data[key] == "none" or data[key] == "" or data[key] is None):
            data[key] = None

    # 2. Normalize operation
    op = data.get("operation")
    if isinstance(op, str):
        op = op.lower().strip()
        data["operation"] = op

    # 3. Handle explicit_visualization — honour user's chart request with highest priority
    explicit_chart = _detect_explicit_chart(question)
    if explicit_chart:
        data["visualization"] = explicit_chart
        data["explicit_visualization"] = True
    elif not data.get("explicit_visualization"):
        data["explicit_visualization"] = False

    # 3a. PIE CHART SPECIAL CASE:
    #     Pie chart is always a categorical breakdown (group_by with aggregation).
    #     Never group by continuous dates or IDs, and ensure aggregation is set.
    if data.get("visualization") == "pie":
        data["operation"] = "group_by"
        if not data.get("aggregation") or data.get("aggregation") not in ("sum", "mean", "count", "min", "max", "median"):
            data["aggregation"] = "sum"
        if not data.get("metric_column"):
            data["metric_column"] = _pick_metric_col(schema_columns, question)
        # Avoid order_date / id columns for pie chart slices
        grp = data.get("group_column")
        if not grp or any(bad in grp.lower() for bad in ["date", "time", "id"]):
            data["group_column"] = _pick_categorical_col(schema_columns, question, exclude=[data.get("metric_column") or ""])
        if not data.get("limit"):
            data["limit"] = 8
        if not data.get("sort"):
            data["sort"] = "desc"
        data["sort_column"] = data.get("metric_column")

    # 3b. HISTOGRAM & BOX PLOT SPECIAL CASE:
    #     Force operation=sort with limit=1000 so the engine returns all rows
    #     needed to compute bins or box statistics from actual data.
    elif data.get("visualization") in ("histogram", "box") and data.get("explicit_visualization"):
        if not data.get("metric_column"):
            data["metric_column"] = _pick_metric_col(schema_columns, question)
        data["operation"] = "sort"
        data["sort_column"] = data.get("metric_column")
        data["sort"] = "asc"
        data["limit"] = 1000
        data["group_column"] = None
        data["aggregation"] = None
        return data

    # 3c. LINE & AREA CHART SPECIAL CASE:
    elif data.get("visualization") in ("line", "area") and data.get("explicit_visualization"):
        if not data.get("metric_column"):
            data["metric_column"] = _pick_metric_col(schema_columns, question)
        if not data.get("group_column"):
            data["group_column"] = _pick_date_col(schema_columns) or _pick_categorical_col(schema_columns, question, exclude=[data.get("metric_column") or ""])
        date_col = _pick_date_col(schema_columns)
        if date_col and data.get("group_column") == date_col:
            data["operation"] = "trend"
        else:
            data["operation"] = "group_by"
        if not data.get("aggregation") or data.get("aggregation") not in ("sum", "mean", "count", "min", "max", "median"):
            data["aggregation"] = "sum"

    # 3d. BAR CHART EXPLICIT REQUEST:
    elif data.get("visualization") == "bar" and data.get("explicit_visualization"):
        if not data.get("metric_column"):
            data["metric_column"] = _pick_metric_col(schema_columns, question)
        if not data.get("group_column"):
            data["group_column"] = _pick_categorical_col(schema_columns, question, exclude=[data.get("metric_column") or ""])
        data["operation"] = "group_by"
        if not data.get("aggregation") or data.get("aggregation") not in ("sum", "mean", "count", "min", "max", "median"):
            data["aggregation"] = "sum"
        if not data.get("limit"):
            data["limit"] = 10
        if not data.get("sort"):
            data["sort"] = "desc"

    # 4. Ranking intent detection
    is_ranking = any(kw in q for kw in ["highest", "lowest", "top", "least", "bottom",
                                         "maximum", "max", "minimum", "min", "best", "worst"])
    is_lowest = any(kw in q for kw in ["lowest", "least", "minimum", "min",
                                        "smallest", "bottom", "worst"])

    if not data.get("group_column") and is_ranking:
        for col in schema_columns:
            if col.lower() in q and col != data.get("metric_column"):
                data["group_column"] = col
                break

    if data.get("group_column") and (op in ("max", "min", "top_n") or
                                      (op == "group_by" and is_ranking) or is_ranking):
        data["operation"] = "group_by"
        if not data.get("aggregation") or data.get("aggregation") not in (
                "sum", "mean", "count", "min", "max", "median"):
            data["aggregation"] = "sum"
        data["sort"] = "asc" if is_lowest else "desc"
        data["limit"] = 1
        # Only set viz if not explicitly requested by user
        if not data.get("explicit_visualization"):
            data["visualization"] = "bar"

    # 5. group_by & trend aggregation and column validation
    if data.get("operation") in ("group_by", "trend"):
        if not data.get("aggregation") or data.get("aggregation") not in (
                "sum", "mean", "count", "min", "max", "median"):
            data["aggregation"] = "sum"
        if not data.get("metric_column"):
            data["metric_column"] = _pick_metric_col(schema_columns, question)
        if not data.get("group_column"):
            data["group_column"] = _pick_categorical_col(schema_columns, question, exclude=[data.get("metric_column") or ""])
        if is_ranking and not data.get("limit"):
            data["limit"] = 1
            data["sort"] = "asc" if is_lowest else "desc"

    # 6. sum operation cleanup
    if data.get("operation") == "sum" and not is_ranking and not any(
            kw in q for kw in ["by ", "per ", "breakdown"]):
        data["group_column"] = None
        data["aggregation"] = None

    # 7. count operation cleanup
    if data.get("operation") == "count":
        data["group_column"] = None
        data["aggregation"] = None
        data["sort"] = None

    # 8. Clean filters
    if "filters" in data:
        valid_ops = {
            "equals", "not_equals", "greater_than", "less_than",
            "greater_than_or_equal", "less_than_or_equal", "contains",
            "date_before", "date_after", "date_between"
        }
        cleaned_filters = []
        for f in data.get("filters") or []:
            if isinstance(f, dict) and f.get("operator") in valid_ops and f.get("value") is not None:
                cleaned_filters.append(f)
        data["filters"] = cleaned_filters

    # 9. Normalize visualization enum
    viz = data.get("visualization", "table")
    valid_viz = {"bar", "line", "pie", "histogram", "scatter", "area", "box", "table", "kpi", "none"}
    if viz not in valid_viz:
        data["visualization"] = "table"

    return data


def _validate_plan_columns(plan: AnalysisPlan, schema_columns: list[str]) -> None:
    """Ensure requested columns actually exist in the uploaded dataset. Never invent or guess columns."""
    if not schema_columns:
        return
    lower_cols = [c.lower() for c in schema_columns]
    if plan.metric_column and plan.metric_column.lower() not in lower_cols:
        raise DatlyException(
            code="MISSING_COLUMN",
            message="I couldn't find the requested column in the uploaded dataset.",
            status_code=400
        )
    if plan.group_column and plan.group_column.lower() not in lower_cols:
        raise DatlyException(
            code="MISSING_COLUMN",
            message="I couldn't find the requested column in the uploaded dataset.",
            status_code=400
        )
    if plan.sort_column and plan.sort_column.lower() not in lower_cols:
        raise DatlyException(
            code="MISSING_COLUMN",
            message="I couldn't find the requested column in the uploaded dataset.",
            status_code=400
        )
    if plan.filters:
        for f in plan.filters:
            if f.column and f.column.lower() not in lower_cols:
                raise DatlyException(
                    code="MISSING_COLUMN",
                    message="I couldn't find the requested column in the uploaded dataset.",
                    status_code=400
                )


async def generate_analysis_plan(
    question: str,
    schema: DatasetSchema,
    profile: DatasetProfile
) -> AnalysisPlan:
    schema_json = schema.model_dump_json(exclude={"success", "dataset_id", "rows"})
    profile_json = profile.model_dump_json(exclude={"success", "dataset_id", "rows"})

    # Build list of schema column names for NLP fallback
    schema_columns = [col.name for col in (schema.column_details or [])] if hasattr(schema, "column_details") else []

    # Normalize Tamil / multilingual question before sending to LLM
    normalized_question = _normalize_question(question)
    # Detect explicit chart request before LLM (always reliable)
    explicit_chart = _detect_explicit_chart(normalized_question)

    from app.services.ai.prompts import SYSTEM_PROMPT, build_user_prompt
    user_prompt = build_user_prompt(normalized_question, schema_json, profile_json)

    logger.info(f"[QUERY] Original user question: {question!r}")
    if normalized_question != question:
        logger.info(f"[QUERY] Normalized question: {normalized_question!r}")
    logger.info(f"[QUERY] Schema columns: {schema_columns}")
    if explicit_chart:
        logger.info(f"[QUERY] Explicit chart request detected: {explicit_chart!r}")

    try:
        response_text = await nvidia_client.get_structured_response(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema_columns=schema_columns
        )

        logger.info(f"[PLAN] LLM raw response: {response_text[:300]}")

        parsed_json = json.loads(response_text)

        # Check for unanswerable question (e.g. "What is my name?")
        if parsed_json.get("unanswerable") or parsed_json.get("clarification_needed"):
            msg = parsed_json.get("clarification_question") or f"I cannot answer '{question}' from the dataset. Please ask a question related to the dataset's columns: {', '.join(schema_columns)}."
            raise DatlyException(
                code="UNANSWERABLE_QUESTION",
                message=msg,
                status_code=400
            )

        # Inject explicit chart if detected from question (overrides LLM)
        if explicit_chart:
            parsed_json["visualization"] = explicit_chart
            parsed_json["explicit_visualization"] = True

        cleaned_json = _sanitize_plan_dict(parsed_json, normalized_question, schema_columns)
        plan = AnalysisPlan.model_validate(cleaned_json)
        _validate_plan_columns(plan, schema_columns)

        logger.info(f"[PLAN] Validated AnalysisPlan: {plan.model_dump(exclude_none=True)}")
        return plan

    except DatlyException:
        raise
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"[PLAN] LLM plan parsing/validation failed ({e!s}) — attempting NLP fallback for: {normalized_question!r}")
        try:
            fallback_json = _nlp_fallback_plan(user_prompt=normalized_question, schema_columns=schema_columns)
            fallback_dict = json.loads(fallback_json)
            if fallback_dict.get("unanswerable"):
                raise DatlyException(
                    code="UNANSWERABLE_QUESTION",
                    message=f"I cannot answer '{question}' from the dataset. Please ask a question related to the dataset's columns: {', '.join(schema_columns)}.",
                    status_code=400
                )
            # Inject explicit chart into fallback too
            if explicit_chart:
                fallback_dict["visualization"] = explicit_chart
                fallback_dict["explicit_visualization"] = True
            cleaned_fallback = _sanitize_plan_dict(fallback_dict, normalized_question, schema_columns)
            plan = AnalysisPlan.model_validate(cleaned_fallback)
            _validate_plan_columns(plan, schema_columns)
            logger.info(f"[PLAN] NLP fallback AnalysisPlan: {plan.model_dump(exclude_none=True)}")
            return plan
        except DatlyException:
            raise
        except Exception as fallback_err:  # noqa: BLE001
            logger.error(f"[PLAN] NLP fallback also failed: {fallback_err!s}")
        raise DatlyException(
            code="INVALID_ANALYSIS_PLAN",
            message="Could not generate a valid analysis plan for the question.",
            status_code=400
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"[PLAN] Unexpected planning error: {e!s}")
        raise DatlyException(
            code="LLM_PLANNING_FAILED",
            message="Unexpected error during LLM planning.",
            status_code=500
        )
