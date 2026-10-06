import logging
import re

import pandas as pd

logger = logging.getLogger("datly.ingestion.cleaner")

# Strict date pattern: e.g. 2024-01-15, 2024/01/15, 15-01-2024, 01/15/2024
DATE_REGEX = re.compile(
    r"^(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})"
    r"(?:[ T]\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)?$"
)


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and infers types for a raw uploaded DataFrame once at ingestion.
    Converts numeric-looking strings and strict date strings to proper dtypes.
    """
    cleaned_df = df.copy()

    for col in cleaned_df.columns:
        series = cleaned_df[col]
        dtype_str = str(series.dtype).lower()

        # Only process object/string columns
        if dtype_str not in ("object", "string", "str") and dtype_str != "o":
            continue

        non_null = series.dropna()
        if len(non_null) == 0:
            continue

        str_vals = non_null.astype(str).str.strip()

        # 1. Try Boolean conversion
        lower_vals = set(str_vals.str.lower().unique())
        if lower_vals.issubset({"true", "false"}):
            cleaned_df[col] = series.map({"true": True, "false": False, True: True, False: False})
            continue

        # 2. Try Numeric conversion (handles "$1,234.50", "42%", "100,000")
        sample = str_vals.head(100)
        cleaned_sample = sample.str.replace(r"[$,€£%]", "", regex=True).str.replace(",", "").str.strip()
        num_converted = pd.to_numeric(cleaned_sample, errors="coerce")
        valid_ratio = num_converted.notna().sum() / len(sample)

        # Do not convert if strings are e.g. "00123" (zip/ID codes where leading zero matters)
        has_leading_zero = any(s.startswith("0") and len(s) > 1 and not s.startswith("0.") for s in sample)

        if valid_ratio >= 0.9 and not has_leading_zero:
            full_cleaned = str_vals.str.replace(r"[$,€£%]", "", regex=True).str.replace(",", "").str.strip()
            full_num = pd.to_numeric(full_cleaned, errors="coerce")
            # If all valid are integers, keep integer (or nullable Int64)
            if (full_num.dropna() % 1 == 0).all():
                cleaned_df[col] = pd.to_numeric(full_cleaned, errors="coerce").astype("Int64")
            else:
                cleaned_df[col] = full_num
            logger.info(f"[INGEST] Converted column '{col}' to numeric")
            continue

        # 3. Try Date conversion (strict pattern match to avoid codes like "2024-1")
        date_matches = sample.apply(lambda v: bool(DATE_REGEX.match(v)))
        if date_matches.mean() >= 0.85:
            try:
                parsed_dates = pd.to_datetime(series, errors="coerce")
                if parsed_dates.notna().sum() / len(non_null) >= 0.8:
                    cleaned_df[col] = parsed_dates
                    logger.info(f"[INGEST] Converted column '{col}' to datetime")
                    continue
            except Exception:  # noqa: BLE001, S110
                pass

    return cleaned_df
