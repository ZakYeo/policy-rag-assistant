from __future__ import annotations

import unittest
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from app.evals.ragas_runner import (
    build_report_path,
    check_summary_thresholds,
    write_report_payload,
)


class RagasRunnerTests(unittest.TestCase):
    def test_build_report_path_uses_timestamped_filename(self) -> None:
        report_path = build_report_path(
            Path("data/rag-test-reports"),
            datetime(2026, 4, 3, 12, 34, 56, tzinfo=timezone.utc),
        )

        self.assertEqual(
            report_path.as_posix(),
            "data/rag-test-reports/rag-test-run-20260403-123456.json",
        )

    def test_check_summary_thresholds_reports_failures(self) -> None:
        failures = check_summary_thresholds(
            summary_metrics={
                "id_based_context_precision": 0.75,
                "id_based_context_recall": 1.0,
            },
            thresholds={
                "id_based_context_precision": 0.8,
                "id_based_context_recall": 1.0,
            },
        )

        self.assertEqual(
            failures,
            ["id_based_context_precision=0.7500 below threshold 0.8000"],
        )

    def test_write_report_payload_serializes_json_file(self) -> None:
        with TemporaryDirectory() as tempdir:
            report_path = Path(tempdir) / "rag-test-run-20260403-123456.json"

            write_report_payload(
                report_path,
                {
                    "status": "running",
                    "cases": [{"case_id": "example"}],
                },
            )

            content = report_path.read_text(encoding="utf-8")
            self.assertIn('"status": "running"', content)
            self.assertIn('"case_id": "example"', content)
