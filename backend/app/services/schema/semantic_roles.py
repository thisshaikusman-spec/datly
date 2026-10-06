import pandas as pd


def detect_semantic_role(name: str, inferred_type: str, series: pd.Series) -> str:
    name_lower = str(name).lower()
    total_count = len(series)
    unique_count = series.nunique()
    
    unique_ratio = unique_count / total_count if total_count > 0 else 0
    
    id_keywords = ["id", "uuid", "guid", "code", "key", "number", "no"]
    is_id_name = any(kw in name_lower for kw in id_keywords)
    if is_id_name and unique_ratio > 0.9 and inferred_type in ("integer", "string", "categorical"):
        return "identifier"
        
    if inferred_type == "datetime":
        if "time" in name_lower or "hour" in name_lower or "minute" in name_lower:
            return "datetime"
        return "date"
        
    if inferred_type == "boolean":
        return "boolean"
        
    if inferred_type == "text":
        return "text"
        
    if inferred_type in ("integer", "float", "numeric"):
        metric_keywords = ["revenue", "sales", "price", "amount", "cost", "profit", "income", "total", "sum", "value", "tax", "discount"]
        measure_keywords = ["quantity", "age", "count", "units", "qty", "size", "weight", "height", "length"]
        
        if any(kw in name_lower for kw in metric_keywords):
            return "numeric_metric"
            
        if any(kw in name_lower for kw in measure_keywords):
            return "numeric_measure"
            
        return "numeric_measure"
        
    if inferred_type == "categorical":
        return "categorical"
        
    return "categorical"
