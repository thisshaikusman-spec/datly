import re

import pandas as pd

DATE_REGEX = re.compile(
    r"^(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})"
    r"(?:[ T]\d{1,2}:\d{2}(?::\d{2})?(?:\.\d+)?)?$"
)


def detect_inferred_type(series: pd.Series) -> str:
    dtype = str(series.dtype).lower()
    
    if "int" in dtype:
        return "integer"
    if "float" in dtype:
        return "float"
    if "bool" in dtype:
        return "boolean"
    if "datetime" in dtype or "date" in dtype:
        return "datetime"
        
    if dtype in ("object", "string", "str") or "str" in dtype or dtype == "o":
        sample = series.dropna().head(20)
        if len(sample) > 0:
            str_sample = sample.astype(str).str.strip()
            lower_sample = str_sample.str.lower()
            if set(lower_sample).issubset({"true", "false", "yes", "no", "y", "n"}):
                return "boolean"
            if all(bool(DATE_REGEX.match(v)) for v in str_sample):
                return "datetime"
                
        unique_count = series.nunique()
        total_count = len(series)
        
        if total_count > 0:
            unique_ratio = unique_count / total_count
            if unique_ratio > 0.5:
                avg_len = series.dropna().astype(str).str.len().mean()
                if avg_len > 30:
                    return "text"
            
        return "categorical"
        
    return "categorical"
