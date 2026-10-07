import os
import sys
from contextlib import asynccontextmanager

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001, S110
        pass

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
    "https://datly-xk2f.vercel.app,http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174"
)
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
if "https://datly-xk2f.vercel.app" not in allowed_origins:
    allowed_origins.append("https://datly-xk2f.vercel.app")
is_wildcard = "*" in allowed_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if is_wildcard else allowed_origins,
    allow_credentials=not is_wildcard,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    allow_origin_regex=r"https://.*\.vercel\.app" if not is_wildcard else None,
    expose_headers=["*"],
)


@app.get("/")
@app.get("/health")
async def root_health():
    """Root health check for Render / monitoring services."""
    return {"status": "ok", "service": "datly-backend", "version": "1.0.0"}


app.include_router(api_router, prefix="/api/v1")
