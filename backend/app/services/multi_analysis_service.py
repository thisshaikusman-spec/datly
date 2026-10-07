import json
import logging
from typing import Any

from app.core.exceptions import DatlyException
from app.models.analysis_plan import AnalysisPlan
from app.models.analysis_result import AnalysisResponse, VisualizationSpec
from app.repositories.workspace_store import workspace_store
from app.services.ai.nvidia_client import nvidia_client
from app.services.ai.planner import (
    _detect_explicit_chart,
    _normalize_question,
    _sanitize_plan_dict,
)
from app.services.ai.prompts import SYSTEM_PROMPT, build_multi_dataset_user_prompt
from app.services.analytics.answer_formatter import format_answer
from app.services.analytics.multi_engine import execute_multi_plan
from app.services.schema.detector import detect_schema
from app.services.visualization.chart_selector import VisualizationSelector

logger = logging.getLogger("datly.multi_analysis_service")


class MultiDatasetAnalysisService:
    @staticmethod
    def _build_workspace_catalog(workspace_id: str, target_dataset_ids: list[str] | None = None) -> tuple[dict[str, Any], dict[str, list[str]], list[str]]:
        """
        Builds a compact catalog of datasets in the workspace.
        Returns (catalog_dict, alias_to_columns, all_column_names).
        """
        metas = workspace_store.list_workspace_datasets(workspace_id)
        if target_dataset_ids:
            metas = [m for m in metas if m.dataset_id in target_dataset_ids]

        if not metas:
            raise DatlyException(
                code="NO_DATASET_SELECTED",
                message="No dataset available in the workspace. Please upload a dataset first.",
                status_code=400,
            )

        catalog: dict[str, Any] = {}
        alias_to_cols: dict[str, list[str]] = {}
        all_cols: list[str] = []

        for m in metas:
            df = workspace_store.get_dataset(m.dataset_id)
            if df is None:
                continue
            schema = detect_schema(m.dataset_id, df)
            alias = m.alias or m.filename

            cols_info = []
            col_names = []
            for col in schema.column_details:
                col_names.append(col.name)
                all_cols.append(col.name)
                cols_info.append({
                    "name": col.name,
                    "inferred_type": col.inferred_type,
                    "semantic_role": col.semantic_role,
                    "sample_values": col.sample_values[:5] if col.sample_values else [],
                })

            alias_to_cols[alias] = col_names
            catalog[alias] = {
                "dataset_id": m.dataset_id,
                "filename": m.filename,
                "rows": m.rows,
                "columns": cols_info,
            }

        return catalog, alias_to_cols, all_cols

    @staticmethod
    def _validate_multi_plan(plan: AnalysisPlan, alias_to_cols: dict[str, list[str]]) -> str | None:
        """
        Validates that datasets, join columns, and metric/group columns exist.
        Returns an error string if invalid, or None if valid.
        """
        if plan.clarification_needed:
            return None

        # Check joins
        if plan.joins:
            for j in plan.joins:
                if j.left not in alias_to_cols:
                    return f"Unknown dataset alias '{j.left}'. Available: {list(alias_to_cols.keys())}"
                if j.right not in alias_to_cols:
                    return f"Unknown dataset alias '{j.right}'. Available: {list(alias_to_cols.keys())}"
                if j.left_on.lower() not in [c.lower() for c in alias_to_cols[j.left]]:
                    return f"Column '{j.left_on}' not found in dataset '{j.left}'"
                if j.right_on.lower() not in [c.lower() for c in alias_to_cols[j.right]]:
                    return f"Column '{j.right_on}' not found in dataset '{j.right}'"

            # In joined datasets, metric and group can come from any joined dataset
            joined_cols = []
            for j in plan.joins:
                joined_cols.extend(alias_to_cols.get(j.left, []))
                joined_cols.extend(alias_to_cols.get(j.right, []))
            lower_joined = [c.lower() for c in joined_cols]

            if plan.metric_column and plan.metric_column.lower() not in lower_joined:
                return f"Metric column '{plan.metric_column}' not found in joined datasets."
            if plan.group_column and plan.group_column.lower() not in lower_joined:
                return f"Group column '{plan.group_column}' not found in joined datasets."

        else:
            # Single dataset plan
            ds = plan.dataset
            if ds and ds not in alias_to_cols:
                # If only 1 dataset in workspace, auto-correct alias
                if len(alias_to_cols) == 1:
                    plan.dataset = next(iter(alias_to_cols.keys()))
                else:
                    return f"Unknown dataset alias '{ds}'. Available: {list(alias_to_cols.keys())}"

            target_cols = alias_to_cols.get(plan.dataset, []) if plan.dataset else []
            if not target_cols and len(alias_to_cols) == 1:
                target_cols = next(iter(alias_to_cols.values()))

            lower_target = [c.lower() for c in target_cols]
            if plan.metric_column and plan.metric_column.lower() not in lower_target:
                return f"Metric column '{plan.metric_column}' not found in dataset '{plan.dataset}'."
            if plan.group_column and plan.group_column.lower() not in lower_target:
                return f"Group column '{plan.group_column}' not found in dataset '{plan.dataset}'."

        return None

    @classmethod
    async def analyze(
        cls,
        workspace_id: str,
        question: str,
        target_dataset_ids: list[str] | None = None,
    ) -> AnalysisResponse:
        logger.info(f"[MULTI_ANALYZE] Workspace: {workspace_id}, Question: {question!r}")

        catalog, alias_to_cols, all_cols = cls._build_workspace_catalog(workspace_id, target_dataset_ids)

        # Pre-process question
        normalized_q = _normalize_question(question)
        explicit_chart = _detect_explicit_chart(normalized_q)

        # Detect multiple chart requests in query
        explicit_charts: list[str] = []
        for chart_type in ["line", "pie", "bar", "histogram", "scatter", "area", "box"]:
            if chart_type in normalized_q.lower():
                explicit_charts.append(chart_type)

        user_prompt = build_multi_dataset_user_prompt(normalized_q, catalog)

        # 1. First LLM planning attempt
        raw_response = await nvidia_client.get_structured_response(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            schema_columns=all_cols,
        )

        plan: AnalysisPlan | None = None
        try:
            plan_dict = json.loads(raw_response)
            cleaned_dict = _sanitize_plan_dict(plan_dict, normalized_q, all_cols)
            if explicit_charts and len(explicit_charts) > 1:
                cleaned_dict["visualizations"] = explicit_charts
                cleaned_dict["explicit_visualization"] = True
            elif explicit_chart:
                cleaned_dict["visualization"] = explicit_chart
                cleaned_dict["visualizations"] = [explicit_chart]
                cleaned_dict["explicit_visualization"] = True

            plan = AnalysisPlan.model_validate(cleaned_dict)
            val_err = cls._validate_multi_plan(plan, alias_to_cols)
        except Exception as e:  # noqa: BLE001
            val_err = str(e)

        # 2. Automatic Repair Retry if validation error
        if val_err:
            logger.warning(f"[MULTI_ANALYZE] Plan validation failed ({val_err}). Starting 1x automatic repair retry...")
            repair_prompt = f"""{user_prompt}

PREVIOUS FAILED PLAN:
{raw_response}

VALIDATION ERROR:
{val_err}

Please fix the error above. Propose a plan using ONLY the exact aliases and columns from the workspace catalog:"""

            repair_response = await nvidia_client.get_structured_response(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=repair_prompt,
                schema_columns=all_cols,
            )

            try:
                repaired_dict = json.loads(repair_response)
                cleaned_repaired = _sanitize_plan_dict(repaired_dict, normalized_q, all_cols)
                if explicit_charts and len(explicit_charts) > 1:
                    cleaned_repaired["visualizations"] = explicit_charts
                    cleaned_repaired["explicit_visualization"] = True
                elif explicit_chart:
                    cleaned_repaired["visualization"] = explicit_chart
                    cleaned_repaired["visualizations"] = [explicit_chart]
                    cleaned_repaired["explicit_visualization"] = True

                plan = AnalysisPlan.model_validate(cleaned_repaired)
                second_err = cls._validate_multi_plan(plan, alias_to_cols)
                if second_err:
                    raise DatlyException(
                        code="INVALID_ANALYSIS_PLAN",
                        message=f"I couldn't generate a valid plan for your question: {second_err}",
                        status_code=400,
                    )
            except DatlyException:
                raise
            except Exception:  # noqa: BLE001
                raise DatlyException(
                    code="INVALID_ANALYSIS_PLAN",
                    message="Could not generate a valid analysis plan across the datasets.",
                    status_code=400,
                )

        assert plan is not None

        from app.services.ai.sarvam.language import detect_language, translate_answer
        detected_lang = detect_language(question)

        # 3. Handle Clarification
        if plan.clarification_needed and plan.clarification_question:
            clarif_q = plan.clarification_question
            if detected_lang and not detected_lang.startswith("en"):
                clarif_q = translate_answer(clarif_q, detected_lang)
            logger.info(f"[CLARIFICATION] {clarif_q}")
            return AnalysisResponse(
                workspace_id=workspace_id,
                question=question,
                answer=clarif_q,
                result={"clarification_needed": True},
                visualization=VisualizationSpec(type="none"),
                visualizations=[VisualizationSpec(type="none")],
                analysis_plan=plan,
                clarification_needed=True,
                clarification_question=clarif_q,
                language_code=detected_lang,
            )

        # 4. Execute Multi-Dataset Plan
        exec_res, verification = execute_multi_plan(
            workspace_or_frames=workspace_id,
            plan=plan,
            target_dataset_ids=target_dataset_ids,
        )

        # 5. Format Answer
        answer = format_answer(plan, exec_res)
        if detected_lang and not detected_lang.startswith("en"):
            answer = translate_answer(answer, detected_lang)

        # 6. Build Visualizations
        viz_specs = VisualizationSelector.select_visualizations(plan, exec_res, None)

        primary_ds_id = None
        if plan.dataset and plan.dataset in catalog:
            primary_ds_id = catalog[plan.dataset].get("dataset_id")

        return AnalysisResponse(
            workspace_id=workspace_id,
            dataset_id=primary_ds_id,
            question=question,
            answer=answer,
            result=exec_res,
            visualization=viz_specs[0],
            visualizations=viz_specs,
            analysis_plan=plan,
            verification=verification,
            language_code=detected_lang,
        )

    # Alias for compatibility
    analyze_workspace = analyze


MultiAnalysisService = MultiDatasetAnalysisService

