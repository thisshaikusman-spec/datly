import logging

from fastapi import APIRouter

from app.core.exceptions import DatlyException
from app.models.analysis_result import AnalysisResponse
from app.models.workspace import (
    WorkspaceAnalyzeRequest,
    WorkspaceCreateResponse,
    WorkspaceDatasetSummary,
)
from app.repositories.workspace_store import workspace_store

logger = logging.getLogger("datly.workspaces")

router = APIRouter()


@router.post("", response_model=WorkspaceCreateResponse)
def create_workspace():
    """Create a new workspace session for multi-dataset analysis."""
    ws = workspace_store.create_workspace()
    logger.info(f"[WORKSPACE] Created workspace {ws.id}")
    return WorkspaceCreateResponse(workspace_id=ws.id, created_at=ws.created_at)


@router.get("/{workspace_id}/datasets", response_model=list[WorkspaceDatasetSummary])
def list_workspace_datasets(workspace_id: str):
    """List all datasets in the workspace."""
    ws = workspace_store.get_workspace(workspace_id)
    if not ws:
        raise DatlyException(
            code="WORKSPACE_NOT_FOUND",
            message=f"Workspace '{workspace_id}' not found.",
            status_code=404,
        )

    metas = workspace_store.list_workspace_datasets(workspace_id)
    summaries: list[WorkspaceDatasetSummary] = []
    for m in metas:
        summaries.append(
            WorkspaceDatasetSummary(
                id=m.dataset_id,
                name=m.filename,
                alias=m.alias or m.filename,
                rows=m.rows,
                columns=m.columns,
                file_type=m.file_type,
                created_at=m.created_at,
            )
        )
    return summaries


@router.delete("/{workspace_id}/datasets/{dataset_id}")
def delete_workspace_dataset(workspace_id: str, dataset_id: str):
    """Remove a dataset from the workspace."""
    ws = workspace_store.get_workspace(workspace_id)
    if not ws:
        raise DatlyException(
            code="WORKSPACE_NOT_FOUND",
            message=f"Workspace '{workspace_id}' not found.",
            status_code=404,
        )

    deleted = workspace_store.delete_dataset(workspace_id, dataset_id)
    if not deleted:
        raise DatlyException(
            code="DATASET_NOT_FOUND",
            message=f"Dataset '{dataset_id}' not found in workspace.",
            status_code=404,
        )
    return {"success": True, "message": f"Dataset '{dataset_id}' deleted from workspace."}


@router.post("/{workspace_id}/analyze", response_model=AnalysisResponse)
async def analyze_workspace(workspace_id: str, request: WorkspaceAnalyzeRequest):
    """Analyze across one or more datasets in the workspace."""
    ws = workspace_store.get_workspace(workspace_id)
    if not ws:
        raise DatlyException(
            code="WORKSPACE_NOT_FOUND",
            message=f"Workspace '{workspace_id}' not found.",
            status_code=404,
        )

    from app.services.multi_analysis_service import MultiDatasetAnalysisService
    return await MultiDatasetAnalysisService.analyze(
        workspace_id=workspace_id,
        question=request.question,
        target_dataset_ids=request.dataset_ids,
    )
