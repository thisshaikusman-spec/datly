"""
Repository-Root ASGI Entry-Point for DATLY.
Allows running `uvicorn main:app --host 0.0.0.0 --port $PORT`
if Render Root Directory is left as the default repo root.
"""
import os
import sys

_repo_root = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.join(_repo_root, "backend")
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Import the existing singleton FastAPI app instance
from app.main import app

__all__ = ["app"]
