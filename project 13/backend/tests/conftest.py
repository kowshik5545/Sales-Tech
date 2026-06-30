from __future__ import annotations

import sys
from pathlib import Path

# Add backend/tests/ to sys.path so test_helpers can be imported as a
# top-level module by all test files (e.g. `from test_helpers import ...`).
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))
