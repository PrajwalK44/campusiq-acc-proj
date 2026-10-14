"""CampusIQ app package."""
import sys
from pathlib import Path

# Ensure project root is in sys.path so 'backend.app' can always be resolved
# regardless of whether uvicorn is run from repo root or inside backend/
_ROOT_DIR = str(Path(__file__).resolve().parent.parent.parent)
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
