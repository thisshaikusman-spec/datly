from fastapi import APIRouter

from app.api.endpoints import analysis, datasets, voice, workspaces

api_router = APIRouter()

@api_router.get("/health")
def health_check():
    return {"status": "ok"}

api_router.include_router(datasets.router, prefix="/datasets", tags=["Datasets"])
api_router.include_router(analysis.router, prefix="/datasets", tags=["Analysis"])
api_router.include_router(analysis.query_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(voice.router, prefix="/voice", tags=["Voice"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["Workspaces"])
