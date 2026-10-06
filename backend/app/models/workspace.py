from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WorkspaceDatasetSummary(BaseModel):
    id: str
    name: str
    alias: str
    rows: int
    columns: int
    file_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Workspace(BaseModel):
    id: str
    name: str = "Default Workspace"
    created_at: datetime
    dataset_ids: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class WorkspaceCreateResponse(BaseModel):
    success: bool = True
    workspace_id: str
    created_at: datetime


class WorkspaceAnalyzeRequest(BaseModel):
    question: str
    dataset_ids: list[str] | None = None
