import logging
from typing import Any

import pandas as pd
from analytics.engine import AnalyticsEngine
from analytics.models import AnalyticsError

from app.core.exceptions import DatlyException
from app.models.analysis_plan import AnalysisPlan
from app.models.analysis_result import StepVerification, VerificationBlock
from app.repositories.workspace_store import workspace_store

logger = logging.getLogger("datly.analytics.multi_engine")

MAX_JOIN_ROWS = 1_000_000


def _get_dtype_family(series: pd.Series) -> str:
    if pd.api.types.is_integer_dtype(series):
        return "integer"
    if pd.api.types.is_float_dtype(series):
        return "numeric"
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    if pd.api.types.is_bool_dtype(series):
        return "boolean"
    return "string"


def execute_multi_plan(
    workspace_or_frames: str | dict[str, pd.DataFrame] | None = None,
    plan: AnalysisPlan | None = None,
    target_dataset_ids: list[str] | None = None,
    workspace_id: str | None = None,
) -> tuple[dict[str, Any], VerificationBlock]:
    """
    Executes a multi-dataset analysis plan against a workspace or dictionary of DataFrames.
    Handles dataset resolution, joins, type compatibility checks, filters, and operations.
    Returns (result_dict, verification_block).
    """
    target_source = workspace_or_frames if workspace_or_frames is not None else workspace_id
    if target_source is None:
        raise ValueError("Either workspace_or_frames or workspace_id must be provided.")
    if plan is None:
        raise ValueError("AnalysisPlan must be provided.")

    steps: list[StepVerification] = []
    datasets_used: list[str] = []
    joins_info: list[dict[str, str]] = []

    def _resolve_entry(alias: str) -> tuple[Any, pd.DataFrame]:
        if isinstance(target_source, dict):
            if alias not in target_source:
                raise DatlyException(
                    code="DATASET_NOT_FOUND",
                    message=f"Dataset with alias '{alias}' not found in provided frames.",
                    status_code=400,
                )
            df = target_source[alias]
            class MockMeta:
                filename = f"{alias}.csv"
            return MockMeta(), df
        else:
            ws = workspace_store.get_workspace(target_source)
            if not ws:
                raise DatlyException(
                    code="WORKSPACE_NOT_FOUND",
                    message=f"Workspace '{target_source}' not found.",
                    status_code=404,
                )
            entry = workspace_store.get_dataset_by_alias(target_source, alias)
            if not entry:
                raise DatlyException(
                    code="DATASET_NOT_FOUND",
                    message=f"Dataset with alias '{alias}' not found in workspace.",
                    status_code=400,
                )
            return entry

    # 1. Resolve dataset or joins
    if plan.joins:
        # Multi-dataset plan with joins
        current_df: pd.DataFrame | None = None
        current_alias: str | None = None

        for idx, join in enumerate(plan.joins):
            left_alias = join.left
            right_alias = join.right
            left_on = join.left_on
            right_on = join.right_on
            how = join.how.value

            # Resolve left dataframe
            if current_df is None or left_alias != current_alias:
                left_meta, left_df = _resolve_entry(left_alias)
                current_df = left_df.copy()
                current_alias = left_alias
                if left_alias not in datasets_used:
                    datasets_used.append(left_alias)
                steps.append(StepVerification(
                    step=f"Load {left_alias}",
                    details=f"Loaded {len(left_df)} rows from {left_meta.filename}",
                    rows_before=0,
                    rows_after=len(left_df),
                ))

            # Resolve right dataframe
            _right_meta, right_df = _resolve_entry(right_alias)
            if right_alias not in datasets_used:
                datasets_used.append(right_alias)

            # Check column existence
            if left_on not in current_df.columns:
                raise DatlyException(
                    code="MISSING_COLUMN",
                    message=f"Join column '{left_on}' does not exist in dataset '{left_alias}'.",
                    status_code=400,
                )
            if right_on not in right_df.columns:
                raise DatlyException(
                    code="MISSING_COLUMN",
                    message=f"Join column '{right_on}' does not exist in dataset '{right_alias}'.",
                    status_code=400,
                )

            # Check type compatibility
            left_family = _get_dtype_family(current_df[left_on])
            right_family = _get_dtype_family(right_df[right_on])
            # Integer and float/numeric can join; otherwise families must match
            compatible = (
                left_family == right_family or
                (left_family in ("integer", "numeric") and right_family in ("integer", "numeric"))
            )
            if not compatible:
                raise DatlyException(
                    code="JOIN_TYPE_MISMATCH",
                    message=f"Cannot join '{left_on}' ({left_family}) with '{right_on}' ({right_family}): incompatible types.",
                    status_code=400,
                )

            # Perform join
            rows_before = len(current_df)
            try:
                # Suffix overlapping columns
                joined_df = pd.merge(
                    current_df,
                    right_df,
                    left_on=left_on,
                    right_on=right_on,
                    how=how,
                    suffixes=("", f"_{right_alias}"),
                )
            except Exception as e:  # noqa: BLE001
                raise DatlyException(
                    code="JOIN_ERROR",
                    message=f"Failed to join '{left_alias}' and '{right_alias}': {e!s}",
                    status_code=400,
                )

            # Cap row explosion
            if len(joined_df) > MAX_JOIN_ROWS:
                logger.warning(f"Join exceeded {MAX_JOIN_ROWS} rows, capping to {MAX_JOIN_ROWS}")
                joined_df = joined_df.head(MAX_JOIN_ROWS)

            joins_info.append({
                "left": left_alias,
                "right": right_alias,
                "left_on": left_on,
                "right_on": right_on,
                "how": how,
            })
            steps.append(StepVerification(
                step=f"Join {left_alias} ↔ {right_alias}",
                details=f"{how.upper()} join on {left_on} = {right_on}",
                rows_before=rows_before,
                rows_after=len(joined_df),
            ))
            current_df = joined_df

        working_df = current_df

    else:
        # Single dataset plan
        target_alias = plan.dataset
        target_meta: Any = None
        target_df: pd.DataFrame | None = None

        if target_alias:
            try:
                target_meta, target_df = _resolve_entry(target_alias)
            except Exception:  # noqa: BLE001
                target_meta, target_df = None, None
        elif isinstance(target_source, dict) and len(target_source) > 0:
            first_alias = next(iter(target_source.keys()))
            target_meta, target_df = _resolve_entry(first_alias)
        elif target_dataset_ids and len(target_dataset_ids) > 0 and isinstance(target_source, str):
            target_df = workspace_store.get_dataset(target_dataset_ids[0])
            target_meta = workspace_store.get_metadata(target_dataset_ids[0])
        elif isinstance(target_source, str):
            # Pick first dataset in workspace
            metas = workspace_store.list_workspace_datasets(target_source)
            if metas:
                target_meta = metas[0]
                target_df = workspace_store.get_dataset(target_meta.dataset_id)

        if target_df is None or target_meta is None:
            raise DatlyException(
                code="DATASET_NOT_FOUND",
                message="No matching dataset found in workspace.",
                status_code=404,
            )

        alias = target_meta.alias or target_meta.filename
        datasets_used.append(alias)
        steps.append(StepVerification(
            step=f"Load {alias}",
            details=f"Loaded {len(target_df)} rows from {target_meta.filename}",
            rows_before=0,
            rows_after=len(target_df),
        ))
        working_df = target_df.copy()

    if working_df is None:
        raise DatlyException(
            code="ANALYTICS_ERROR",
            message="No active dataset could be constructed for analysis.",
            status_code=500,
        )

    initial_rows = len(working_df)

    # 2. Track Filters
    filters_applied: list[dict[str, Any]] = []
    if plan.filters:
        filters_applied = [f.model_dump() for f in plan.filters]
        steps.append(StepVerification(
            step="Apply Filters",
            details=f"Applied {len(plan.filters)} filter(s)",
            rows_before=initial_rows,
            rows_after=None,  # Will be updated by execution
        ))

    # 3. Execute with AnalyticsEngine
    try:
        engine = AnalyticsEngine()
        plan_dict = plan.model_dump(exclude_none=True)
        exec_res = engine.execute(working_df, plan_dict)

        final_rows = len(exec_res.rows)
        steps.append(StepVerification(
            step=f"Execute {plan.operation.value}",
            details=f"Computed {plan.operation.value} on {plan.metric_column or 'data'}",
            rows_before=initial_rows,
            rows_after=final_rows,
        ))

        # Format result structure
        if exec_res.operation in ["sum", "average", "min", "max", "count"] and len(exec_res.rows) == 1:
            val = next(iter(exec_res.rows[0].values()))
            result_dict = {"value": val, "data": exec_res.rows, "rows": exec_res.rows, "_external_result": exec_res.model_dump()}
        else:
            result_dict = {"data": exec_res.rows, "rows": exec_res.rows, "_external_result": exec_res.model_dump()}

    except AnalyticsError as e:
        logger.error(f"[MULTI_ENGINE] Execution failed: {e.message}")
        raise DatlyException(
            code=e.code,
            message=f"Failed to execute analysis plan: {e.message}",
            status_code=400,
        )
    except Exception as e:  # noqa: BLE001
        logger.error(f"[MULTI_ENGINE] Unexpected error: {e}")
        raise DatlyException(
            code="ANALYTICS_ERROR",
            message=f"Failed to execute analysis plan: {e!s}",
            status_code=500,
        )

    verification = VerificationBlock(
        datasets_used=datasets_used,
        operation=plan.operation.value,
        joins=joins_info,
        filters_applied=filters_applied,
        initial_rows=initial_rows,
        final_rows=final_rows,
        row_count_before=initial_rows,
        row_count_after=final_rows,
        steps=steps,
    )

    return result_dict, verification
