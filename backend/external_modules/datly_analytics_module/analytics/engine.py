from typing import Any

import pandas as pd

from .models import AnalysisResult, AnalyticsError
from .operations import OPERATION_MAP
from .visualization import determine_visualization


class AnalyticsEngine:
    """
    A standalone, deterministic Analytics Engine that performs operations
    on Pandas DataFrames based on a structured AnalysisPlan.
    """
    
    def execute(self, df: pd.DataFrame, plan: dict[str, Any]) -> AnalysisResult:
        """
        Executes an analysis plan against a DataFrame.
        
        Args:
            df (pd.DataFrame): The input dataset.
            plan (dict): The structured analysis plan.
            
        Returns:
            AnalysisResult: The structured result.
        """
        if not isinstance(df, pd.DataFrame):
            raise AnalyticsError("INVALID_DATAFRAME", "Input must be a Pandas DataFrame.")
            
        if df.empty:
            # Handle empty gracefully where possible or return empty result.
            pass
            
        operation = plan.get("operation")
        if not operation:
            raise AnalyticsError("MISSING_OPERATION", "Analysis plan must contain an 'operation' field.")
            
        if operation not in OPERATION_MAP:
            raise AnalyticsError("UNSUPPORTED_OPERATION", f"Operation '{operation}' is not supported. Engine strictly prohibits arbitrary execution.")
            
        # Execute the mapped function deterministically
        try:
            target_df = df
            if plan.get("filters") and operation != "filter":
                from .filters import apply_filters
                target_df = apply_filters(df, plan["filters"])
            func = OPERATION_MAP[operation]
            result_df = func(target_df, plan)
        except AnalyticsError:
            raise
        except Exception as e:  # noqa: BLE001
            raise AnalyticsError("EXECUTION_ERROR", f"An error occurred during execution: {e!s}")
            
        # Replace NaNs/Infs with None for JSON serializability
        result_df = result_df.replace([float('inf'), float('-inf')], None)
        result_df = result_df.where(pd.notnull(result_df), None)
        
        # Prepare result
        columns = result_df.columns.tolist()
        rows = result_df.to_dict(orient="records")
        row_count = len(rows)
        
        viz = determine_visualization(result_df, plan)
        
        return AnalysisResult(
            operation=operation,
            columns=columns,
            rows=rows,
            row_count=row_count,
            visualization=viz
        )
