"""App module."""
import os
import sys

_backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

_ext_module_path = os.path.join(_backend_dir, "external_modules/datly_analytics_module")
if os.path.exists(_ext_module_path) and _ext_module_path not in sys.path:
    sys.path.insert(0, _ext_module_path)

