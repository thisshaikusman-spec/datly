import pandas as pd

from app.models.schema import (
    CategoricalStatistics,
    ColumnProfile,
    DatasetProfile,
    DatetimeStatistics,
    NumericStatistics,
)
from app.services.schema.type_detector import detect_inferred_type


def profile_dataset(dataset_id: str, df: pd.DataFrame) -> DatasetProfile:
    rows = len(df)
    columns = len(df.columns)
    column_profiles = []
    
    for col_name in df.columns:
        series = df[col_name]
        inferred_type = detect_inferred_type(series)
        missing_count = int(series.isna().sum())
        
        numeric_stats = None
        categorical_stats = None
        datetime_stats = None
        
        if inferred_type in ("integer", "float", "numeric") and not series.empty:
            s_drop = series.dropna()
            if not s_drop.empty:
                try:
                    s_num = pd.to_numeric(s_drop, errors="coerce").dropna()
                    if not s_num.empty:
                        numeric_stats = NumericStatistics(
                            min=float(s_num.min()),
                            max=float(s_num.max()),
                            mean=float(s_num.mean()),
                            median=float(s_num.median()),
                            std_dev=float(s_num.std()) if len(s_num) > 1 else 0.0
                        )
                except Exception:  # noqa: BLE001, S110
                    pass
                    
        elif inferred_type in ("categorical", "boolean", "text", "identifier") and not series.empty:
            s_drop = series.dropna()
            if not s_drop.empty:
                vc = s_drop.value_counts().head(10)
                frequencies = {str(k): int(v) for k, v in vc.items()}
                categorical_stats = CategoricalStatistics(
                    unique_count=int(s_drop.nunique()),
                    top_values=list(frequencies.keys()),
                    frequencies=frequencies
                )
                
        elif inferred_type in ("datetime", "date") and not series.empty:
            s_drop = series.dropna()
            if not s_drop.empty:
                try:
                    s_dt = pd.to_datetime(s_drop, errors="coerce", format="mixed").dropna()
                    if not s_dt.empty:
                        datetime_stats = DatetimeStatistics(
                            min_date=s_dt.min().isoformat(),
                            max_date=s_dt.max().isoformat()
                        )
                except Exception:  # noqa: BLE001, S110
                    pass
                    
        column_profiles.append(ColumnProfile(
            name=str(col_name),
            missing_count=missing_count,
            numeric_stats=numeric_stats,
            categorical_stats=categorical_stats,
            datetime_stats=datetime_stats
        ))
        
    return DatasetProfile(
        dataset_id=dataset_id,
        rows=rows,
        columns=columns,
        column_profiles=column_profiles
    )
