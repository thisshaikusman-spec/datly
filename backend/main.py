"""
Render / Production ASGI Entry-Point for DATLY.
Allows running `uvicorn main:app --host 0.0.0.0 --port $PORT`
directly from the backend directory without module path confusion.
"""
import os
import sys

# Ensure backend root is on sys.path
_backend_root = os.path.dirname(os.path.abspath(__file__))
if _backend_root not in sys.path:
    sys.path.insert(0, _backend_root)

# Import the existing singleton FastAPI app instance from app.main
from app.main import app

__all__ = ["app"]
