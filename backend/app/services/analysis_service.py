import logging

from app.core.exceptions import DatlyException
from app.models.analysis_result import AnalysisResponse
from app.repositories.dataset_store import dataset_store
from app.services.ai.planner import generate_analysis_plan
from app.services.analytics.answer_formatter import format_answer
from app.services.analytics.engine import execute_plan
from app.services.schema.detector import detect_schema
from app.services.schema.profiler import profile_dataset
from app.services.visualization.chart_selector import VisualizationSelector

logger = logging.getLogger("datly.analysis")


class AnalysisService:
    @staticmethod
    async def analyze(dataset_id: str, question: str) -> AnalysisResponse:
        # ── Validation ──────────────────────────────────────────────────────────
        if not dataset_id or dataset_id.strip() in ("", "null", "undefined"):
            raise DatlyException(
                code="NO_DATASET_SELECTED",
                message="No dataset selected. Please upload a dataset first.",
                status_code=400
            )

        if not question or not question.strip():
            raise DatlyException(
                code="EMPTY_QUESTION",
                message="Question cannot be empty.",
                status_code=400
            )

        # ── Load dataset ─────────────────────────────────────────────────────────
        df = dataset_store.get_dataset(dataset_id)
        if df is None:
            raise DatlyException(
                code="DATASET_NOT_FOUND",
                message="No dataset selected. Please upload a dataset first.",
                status_code=404
            )

        logger.info("=" * 60)
        logger.info(f"[QUERY] question={question}")
        logger.info(f"[QUERY] dataset_id={dataset_id}")
        logger.info(f"[DATASET] Shape: {df.shape}, Columns: {list(df.columns)}")

        # ── Schema + profile ─────────────────────────────────────────────────────
        schema = detect_schema(dataset_id, df)
        profile = profile_dataset(dataset_id, df)

        # ── Plan generation ──────────────────────────────────────────────────────
        plan = await generate_analysis_plan(question, schema, profile)
        logger.info(f"[PLAN]   AnalysisPlan: {plan.model_dump(exclude_none=True)}")
        logger.info(f"[PLAN]   Operation: {plan.operation.value}, Explicit viz: {plan.explicit_visualization}")

        # ── Execution ────────────────────────────────────────────────────────────
        result = execute_plan(df, plan)
        result_summary = result.get("value") if "value" in result else result.get("data", [])[:3]
        logger.info(f"[RESULT] {result_summary}")

        # ── Answer ───────────────────────────────────────────────────────────────
        from app.services.ai.sarvam.language import detect_language, translate_answer
        detected_lang = detect_language(question)

        answer = format_answer(plan, result)
        if detected_lang and not detected_lang.startswith("en"):
            answer = translate_answer(answer, detected_lang)
        logger.info(f"[ANSWER] length={len(answer)} (lang={detected_lang})")

        # ── Visualization ─────────────────────────────────────────────────────────
        viz_specs = VisualizationSelector.select_visualizations(plan, result, schema)
        viz_spec = viz_specs[0]
        logger.info(f"[VIZ]    Types: {[v.type.value for v in viz_specs]}")
        logger.info("=" * 60)

        return AnalysisResponse(
            dataset_id=dataset_id,
            question=question,
            answer=answer,
            result=result,
            visualization=viz_spec,
            visualizations=viz_specs,
            analysis_plan=plan,
            language_code=detected_lang,
        )
