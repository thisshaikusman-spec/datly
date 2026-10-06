from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DatasetMetadata(BaseModel):
    success: bool = True
    dataset_id: str
    filename: str
    file_type: str
    rows: int
    columns: int
    created_at: datetime
    workspace_id: str | None = None
    alias: str | None = None
    
    model_config = ConfigDict(from_attributes=True)
