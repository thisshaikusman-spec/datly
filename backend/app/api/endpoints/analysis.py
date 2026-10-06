import logging

from fastapi import APIRouter
from pydantic import BaseModel

from app.models.analysis_result import AnalysisResponse
from app.services.analysis_service import AnalysisService

logger = logging.getLogger("datly.analysis.endpoint")

router = APIRouter()
query_router = APIRouter()

class AnalysisRequest(BaseModel):
    question: str

class QueryAnalysisRequest(BaseModel):
    dataset_id: str
    question: str


@router.post("/{dataset_id}/analyze", response_model=AnalysisResponse)
async def analyze_dataset(dataset_id: str, request: AnalysisRequest):
    logger.info(f"[QUERY] question={request.question}")
    logger.info(f"[QUERY] dataset_id={dataset_id}")
    return await AnalysisService.analyze(dataset_id, request.question)


@query_router.post("/query", response_model=AnalysisResponse)
async def query_analysis(request: QueryAnalysisRequest):
    logger.info(f"[QUERY] question={request.question}")
    logger.info(f"[QUERY] dataset_id={request.dataset_id}")
    return await AnalysisService.analyze(request.dataset_id, request.question)
