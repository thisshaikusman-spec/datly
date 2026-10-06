import logging
from typing import Any

import pandas as pd

from app.core.exceptions import DatlyException
from app.models.analysis_plan import AnalysisPlan

logger = logging.getLogger("datly.analytics.engine")

import os
import sys

external_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../external_modules/datly_analytics_module"))
if external_path not in sys.path:
    sys.path.insert(0, external_path)

from analytics.engine import AnalyticsEngine
from analytics.models import AnalyticsError


def execute_plan(df: pd.DataFrame, plan: AnalysisPlan) -> dict[str, Any]:
    try:
        engine = AnalyticsEngine()
        
        # 1. Convert plan to dictionary safely
        plan_dict = plan.model_dump(exclude_none=True)
        
        # 2. Execute plan
        result = engine.execute(df, plan_dict)
        
        # 3. Convert external AnalysisResult to existing DATLY format
        # The existing format expects {"value": x} or {"data": [...]}.
        # Wait, the prompt says: "Convert the result into the result format expected by the EXISTING DATLY analysis pipeline."
        # If we look at existing `AnalysisResponse.result` it is `dict[str, Any]`.
        # Previously we returned `{"value": float}` or `{"data": [...]}`.
        # Can we just return the full `result.model_dump()` which has `rows` and `operation` etc?
        # But `answer_formatter.py` expects `data` or `value`. Let's see what `answer_formatter.py` expects.
        # Wait, the instruction says: "The adapter only transforms data structures."
        # Let's map it exactly to what `answer_formatter.py` expects:
        # If it's a single scalar (e.g. sum, min, max, average, count) it expects {"value": ...}
        # If it's multiple rows, it expects {"data": rows}
        
        # Let's check `result.rows` and `result.operation`.
        if result.operation in ["sum", "average", "min", "max", "count"] and len(result.rows) == 1:
            # Try to extract the single scalar value
            row = result.rows[0]
            val = next(iter(row.values()))
            return {"value": val, "_external_result": result.model_dump()}
        else:
            return {"data": result.rows, "_external_result": result.model_dump()}
        
    except AnalyticsError as e:
        logger.error(f"Execution failed: {e.message}")
        
        # Error mapping
        code_map = {
            "MISSING_COLUMN": "MISSING_COLUMN",
            "INVALID_DATAFRAME": "INVALID_ANALYSIS_PLAN",
            "MISSING_OPERATION": "INVALID_ANALYSIS_PLAN",
            "UNSUPPORTED_OPERATION": "INCOMPATIBLE_OPERATION",
            "INCOMPATIBLE_OPERATION": "INCOMPATIBLE_OPERATION",
        }
        datly_code = code_map.get(e.code, "ANALYTICS_ERROR")
        
        err_msg = "I couldn't find the requested column in the uploaded dataset." if datly_code == "MISSING_COLUMN" else f"Failed to execute analysis plan: {e.message}"
        raise DatlyException(
            code=datly_code,
            message=err_msg,
            status_code=500 if datly_code == "ANALYTICS_ERROR" else 400
        )
    except Exception as e: # noqa: BLE001
        logger.error(f"Execution failed: {e}")
        raise DatlyException(
            code="ANALYTICS_ERROR",
            message=f"Failed to execute analysis plan: {e!s}",
            status_code=500
        )
