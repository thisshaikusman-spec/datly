"""App module."""
import os
import sys

_ext_module_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../external_modules/datly_analytics_module"))
if os.path.exists(_ext_module_path) and _ext_module_path not in sys.path:
    sys.path.insert(0, _ext_module_path)
