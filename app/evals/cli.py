from __future__ import annotations

import sys
import unittest
from pathlib import Path

from app.evals.ragas_runner import run_ragas_evaluation


def main() -> int:
    suite = unittest.defaultTestLoader.discover(
        start_dir=str(Path("integration_tests")),
        pattern="test_*.py",
        top_level_dir=".",
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1

    ragas_result = run_ragas_evaluation(documents_dir=Path("documents"))
    print(f"RAGAS report written to {ragas_result.report_path}")
    if ragas_result.threshold_failures:
        for failure in ragas_result.threshold_failures:
            print(f"RAGAS threshold failure: {failure}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
