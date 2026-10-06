import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.exceptions import DatlyException, datly_exception_handler
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DATLY Backend Starting Up...")
    yield

app = FastAPI(
    title="DATLY API",
    description="Backend API for DATLY - Schema-Agnostic Natural Language Data Analyst",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_exception_handler(DatlyException, datly_exception_handler)

raw_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
)
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
