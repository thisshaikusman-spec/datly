import logging
import re
from typing import Any

import numpy as np
import pandas as pd

from app.models.analysis_plan import AnalysisPlan, Operation
from app.models.analysis_result import VisualizationSpec
from app.models.analysis_result import VisualizationType as ResultVisualizationType
from app.models.schema import DatasetSchema

logger = logging.getLogger("datly.visualization")


def _build_histogram_data(rows: list[dict], x_col: str) -> tuple[list[float], list[int]]:
    """Compute histogram bins/frequencies from raw rows for a numeric column."""
    values = [r[x_col] for r in rows if r.get(x_col) is not None and isinstance(r[x_col], (int, float))]
    if not values:
        return [], []
    arr = np.array(values, dtype=float)
    bin_count = min(20, max(5, int(len(arr) ** 0.5)))
    frequencies, bin_edges = np.histogram(arr, bins=bin_count)
    # Return left edge of each bin and corresponding frequency
    bins = [round(float(b), 4) for b in bin_edges[:-1]]
    freqs = [int(f) for f in frequencies]
    return bins, freqs


class VisualizationSelector:
    @staticmethod
    def select_visualization(
        plan: AnalysisPlan,
        result: dict[str, Any],
        schema: DatasetSchema | None = None,
    ) -> VisualizationSpec:
        """
        Determine the VisualizationSpec for the given analysis result.

        Priority:
          1. User's explicit chart request (plan.explicit_visualization == True)
          2. External engine suggestion (when no explicit request)
          3. Automatic chart selection based on data types
          4. Default: table
        """
        # ── Extract data rows ────────────────────────────────────────────────────
        rows: list[dict] = []
        if "data" in result and isinstance(result["data"], list):
            rows = result["data"]
        elif "_external_result" in result and isinstance(result["_external_result"].get("rows"), list):
            rows = result["_external_result"]["rows"]

        # ── Scalar result (single value) ─────────────────────────────────────────
        if "value" in result:
            # If user explicitly asked for a chart on a scalar result, explain
            if plan.explicit_visualization:
                logger.info(
                    f"[VIZ] Explicit {plan.visualization.value} requested but result is a scalar — "
                    "returning none (scalar result)."
                )
            return VisualizationSpec(type=ResultVisualizationType.none)

        if not rows:
            return VisualizationSpec(type=ResultVisualizationType.none)

        # ── Determine requested/target chart type ────────────────────────────────
        # Start with whatever is in the plan (may be explicit or LLM-suggested)
        plan_viz: str = plan.visualization.value  # e.g. "bar", "line", "pie"

        # 1. EXPLICIT USER REQUEST — always honour it
        if plan.explicit_visualization:
            logger.info(f"[VIZ] Honouring explicit chart request: {plan_viz!r}")
            return VisualizationSelector._build_spec(
                viz_type=plan_viz,
                plan=plan,
                rows=rows,
                schema=schema,
                explicit=True,
            )

        # 2. External engine suggestion (non-explicit)
        ext_viz: dict | None = None
        if "_external_result" in result:
            ext = result["_external_result"].get("visualization")
            if isinstance(ext, dict) and ext.get("type") not in (None, "none", "table"):
                ext_viz = ext
                logger.info(f"[VIZ] External engine suggests: {ext_viz!r}")

        if ext_viz:
            viz_type = ext_viz.get("type", "table")
            x = ext_viz.get("x") or plan.group_column
            y = ext_viz.get("y") or plan.metric_column
            title = ext_viz.get("title")
            try:
                enum_type = ResultVisualizationType(viz_type)
            except ValueError:
                enum_type = ResultVisualizationType.table
            return VisualizationSpec(type=enum_type, x=x, y=y, title=title)

        # 3. Automatic selection based on plan + data types
        return VisualizationSelector._auto_select(plan, rows, schema)

    @staticmethod
    def select_visualizations(
        plan: AnalysisPlan,
        result: dict[str, Any],
        schema: DatasetSchema | None = None,
    ) -> list[VisualizationSpec]:
        target_types = plan.visualizations if plan.visualizations else ([plan.visualization] if plan.visualization else [])
        if len(target_types) <= 1:
            return [VisualizationSelector.select_visualization(plan, result, schema)]

        rows: list[dict] = []
        if "data" in result and isinstance(result["data"], list):
            rows = result["data"]
        elif "_external_result" in result and isinstance(result["_external_result"].get("rows"), list):
            rows = result["_external_result"]["rows"]

        if "value" in result or not rows:
            return [VisualizationSpec(type=ResultVisualizationType.none)]

        specs: list[VisualizationSpec] = []
        for vt in target_types:
            spec = VisualizationSelector._build_spec(
                viz_type=vt.value,
                plan=plan,
                rows=rows,
                schema=schema,
                explicit=plan.explicit_visualization,
            )
            specs.append(spec)
        return specs or [VisualizationSelector.select_visualization(plan, result, schema)]

    # ── internal helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _build_spec(
        viz_type: str,
        plan: AnalysisPlan,
        rows: list[dict],
        schema: DatasetSchema | None,
        explicit: bool = False,
    ) -> VisualizationSpec:
        """Build a VisualizationSpec for the given chart type and data."""
        try:
            enum_type = ResultVisualizationType(viz_type)
        except ValueError:
            logger.warning(f"[VIZ] Unknown viz type {viz_type!r}, falling back to table")
            return VisualizationSpec(type=ResultVisualizationType.table, title="Analysis Result")

        gc = plan.group_column
        mc = plan.metric_column

        if enum_type == ResultVisualizationType.bar:
            return VisualizationSpec(
                type=ResultVisualizationType.bar,
                x=gc,
                y=mc,
                title=f"{(mc or '').capitalize()} by {(gc or '').capitalize()}",
            )

        if enum_type == ResultVisualizationType.line:
            return VisualizationSpec(
                type=ResultVisualizationType.line,
                x=gc,
                y=mc,
                title=f"{(mc or '').capitalize()} Over Time",
            )

        if enum_type == ResultVisualizationType.pie:
            labels: list[str] = []
            values: list[float] = []
            if gc and mc:
                for r in rows:
                    lbl = r.get(gc)
                    val = r.get(mc)
                    if lbl is not None and val is not None:
                        labels.append(str(lbl))
                        values.append(float(val) if isinstance(val, (int, float)) else 0.0)
            # Pie rule: only when <= 8 categories and all values >= 0
            if len(labels) > 8 or (values and any(v < 0 for v in values)):
                logger.info(f"[VIZ] Pie chart ineligible (count={len(labels)}, min={min(values) if values else 0}). Falling back to bar.")
                return VisualizationSpec(
                    type=ResultVisualizationType.bar,
                    x=gc,
                    y=mc,
                    title=f"{(mc or '').capitalize()} by {(gc or '').capitalize()}",
                )
            return VisualizationSpec(
                type=ResultVisualizationType.pie,
                x=gc,
                y=mc,
                labels=labels or None,
                values=values or None,
                title=f"{(mc or '').capitalize()} Distribution by {(gc or '').capitalize()}",
            )

        if enum_type == ResultVisualizationType.histogram:
            # For histogram we need a numeric column — prefer metric_column
            x_col = mc or gc
            if x_col and rows:
                bins, freqs = _build_histogram_data(rows, x_col)
            else:
                bins, freqs = [], []
            return VisualizationSpec(
                type=ResultVisualizationType.histogram,
                x=x_col,
                bins=bins or None,
                frequencies=freqs or None,
                title=f"{(x_col or '').capitalize()} Distribution",
            )

        if enum_type == ResultVisualizationType.scatter:
            return VisualizationSpec(
                type=ResultVisualizationType.scatter,
                x=gc,
                y=mc,
                title=f"{(gc or '').capitalize()} vs {(mc or '').capitalize()}",
            )

        if enum_type == ResultVisualizationType.area:
            return VisualizationSpec(
                type=ResultVisualizationType.area,
                x=gc,
                y=mc,
                title=f"{(mc or '').capitalize()} Area Chart",
            )

        if enum_type == ResultVisualizationType.box:
            x_col = mc or gc
            stats_dict = None
            if x_col and rows:
                vals = [r[x_col] for r in rows if r.get(x_col) is not None and isinstance(r[x_col], (int, float))]
                if vals:
                    s_vals = sorted(vals)
                    n = len(s_vals)
                    stats_dict = {
                        "min": float(s_vals[0]),
                        "q1": float(s_vals[int(n * 0.25)]),
                        "median": float(s_vals[int(n * 0.5)]),
                        "q3": float(s_vals[int(n * 0.75)]),
                        "max": float(s_vals[-1]),
                    }
            return VisualizationSpec(
                type=ResultVisualizationType.box,
                x=x_col,
                y=mc,
                title=f"{(x_col or '').capitalize()} Distribution (Box Plot)",
                stats=stats_dict,
            )

        if enum_type == ResultVisualizationType.table:
            return VisualizationSpec(type=ResultVisualizationType.table, title="Analysis Result")

        # none / unknown
        return VisualizationSpec(type=ResultVisualizationType.none)

    @staticmethod
    def _auto_select(
        plan: AnalysisPlan,
        rows: list[dict],
        schema: DatasetSchema | None,
    ) -> VisualizationSpec:
        """Automatic chart selection based on plan + data shape."""
        gc = plan.group_column
        mc = plan.metric_column

        if not mc and plan.operation != Operation.count:
            return VisualizationSpec(type=ResultVisualizationType.table, title="Analysis Result")

        # group_by / top_n / trend
        if plan.operation in (Operation.group_by, Operation.top_n, Operation.trend) and gc and mc:
            # Is group column a date?
            is_date = False
            if schema:
                for col in schema.columns:
                    if col.name == gc and col.data_type in ("datetime", "date"):
                        is_date = True
                        break
            if not is_date:
                is_date = bool(re.search(r"date|time|year|month|day|period", gc.lower()))
            if is_date or plan.operation == Operation.trend:
                return VisualizationSpec(
                    type=ResultVisualizationType.line,
                    x=gc,
                    y=mc,
                    title=f"{mc.capitalize()} Over Time",
                )
            return VisualizationSpec(
                type=ResultVisualizationType.bar,
                x=gc,
                y=mc,
                title=f"{mc.capitalize()} by {gc.capitalize()}",
            )

        # scatter for numeric vs numeric comparisons
        if plan.operation == Operation.comparison and gc and mc:
            return VisualizationSpec(
                type=ResultVisualizationType.scatter,
                x=gc,
                y=mc,
                title=f"{gc.capitalize()} vs {mc.capitalize()}",
            )

        return VisualizationSpec(type=ResultVisualizationType.table, title="Analysis Result")


def select_visualizations(
    plan_or_df: Any,
    result_or_viz: Any,
    schema_or_group: Any = None,
    metric_col: Any = None,
    *,
    group_col: Any = None,
) -> list[VisualizationSpec]:
    """Top-level helper supporting both (plan, result, schema) and (df, viz_list, group_col, metric_col)."""
    if isinstance(plan_or_df, AnalysisPlan):
        return VisualizationSelector.select_visualizations(plan_or_df, result_or_viz, schema_or_group)

    df = plan_or_df
    viz_types = result_or_viz if isinstance(result_or_viz, list) else [result_or_viz]
    effective_group = group_col if group_col is not None else schema_or_group

    rows = df.to_dict(orient="records") if isinstance(df, pd.DataFrame) else (df.get("data", []) if isinstance(df, dict) else [])
    plan = AnalysisPlan(
        operation=Operation.group_by if effective_group else Operation.sum,
        group_column=effective_group,
        metric_column=metric_col,
        visualizations=viz_types,
        explicit_visualization=True,
    )
    return VisualizationSelector.select_visualizations(plan, {"data": rows})
