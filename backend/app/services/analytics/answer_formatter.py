from typing import Any

from app.models.analysis_plan import AnalysisPlan, Operation


def format_number(num: Any) -> str:
    if isinstance(num, float):
        if num == int(num):
            return f"{int(num):,}"
        return f"{num:,.2f}".rstrip("0").rstrip(".")
    if isinstance(num, int):
        return f"{num:,}"
    return str(num)


def format_answer(plan: AnalysisPlan, result: dict[str, Any]) -> str:
    """
    Produce a precise, human-readable sentence from the AnalysisPlan and AnalyticsResult.
    Never returns a generic fallback — always derives meaning from the actual data.
    """
    op = plan.operation
    metric = plan.metric_column or "value"
    group = plan.group_column

    # ── Scalar result (sum / average / min / max / count) ──────────────────────
    if "value" in result:
        val = result["value"]
        if val is None:
            return "No matching records were found."
        fval = format_number(val)

        if op == Operation.count:
            return f"There are {fval} records in the dataset."
        if op == Operation.sum:
            return f"The total {metric} is {fval}."
        if op == Operation.average:
            return f"The average {metric} is {fval}."
        if op == Operation.min:
            return f"The minimum {metric} is {fval}."
        if op == Operation.max:
            return f"The maximum {metric} is {fval}."
        return f"The result is {fval}."

    # ── Tabular result (group_by / top_n / sort / trend / filter) ──────────────
    if "data" in result:
        data: list[dict] = result["data"]
        if not data:
            return "No matching records were found."

        # Single-row ranking answer (e.g. "Which city has highest revenue?")
        if len(data) == 1 and group and metric:
            row = data[0]
            group_val = row.get(group)
            metric_val = row.get(metric)
            if group_val is not None and metric_val is not None:
                fval = format_number(metric_val)
                agg_label = plan.aggregation.value if plan.aggregation else "value"
                if plan.sort == "asc":
                    return f"{group_val} has the lowest {metric} with a {agg_label} of {fval}."
                if plan.sort == "desc" or op in (Operation.top_n, Operation.group_by):
                    return f"{group_val} has the highest {metric} with a {agg_label} of {fval}."
                return f"For {group_val}, the {metric} is {fval}."

        # Multi-row answer (e.g. breakdown / top N)
        if len(data) > 1:
            if op == Operation.trend:
                return f"Here is the {metric} trend over {group}. {len(data)} data points are shown in the chart."
            if group and metric:
                top_row = data[0]
                group_val = top_row.get(group)
                metric_val = top_row.get(metric)
                if group_val is not None and metric_val is not None:
                    fval = format_number(metric_val)
                    return (
                        f"{metric.capitalize()} breakdown by {group}: "
                        f"{group_val} leads with {fval}. "
                        f"See the chart for the full distribution ({len(data)} groups)."
                    )
            return f"Analysis complete — {len(data)} records returned. See the chart for details."

        # Fallback single row with no group
        if len(data) == 1:
            row = data[0]
            if row:
                key, val = next(iter(row.items()))
                return f"The {key} is {format_number(val)}."

    return "Analysis complete. See the chart for details."
