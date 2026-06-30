from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend/ root is on sys.path so all internal imports resolve when
# pytest is invoked from the project root or from backend/.
backend_root = Path(__file__).parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))
