from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ragas import SingleTurnSample
from ragas.metrics import (
    NonLLMContextPrecisionWithReference,
    NonLLMContextRecall,
    IDBasedContextPrecision,
    IDBasedContextRecall,
)

from app.evals.cases import RAG_EVAL_CASES
from app.evals.harness import RagIntegrationHarness


DEFAULT_REPORTS_DIR = Path("data") / "rag-test-reports"
SUMMARY_THRESHOLDS = {
    "id_based_context_precision": 0.50,
    "id_based_context_recall": 1.0,
    "nonllm_context_precision": 0.90,
    "nonllm_context_recall": 1.0,
}


@dataclass(frozen=True, slots=True)
class RagasRunResult:
    report_path: Path
    report_payload: dict[str, object]
    threshold_failures: list[str]

    @property
    def meets_thresholds(self) -> bool:
        return not self.threshold_failures


def build_report_path(output_dir: Path, run_started_at: datetime) -> Path:
    timestamp = run_started_at.strftime("%Y%m%d-%H%M%S")
    return output_dir / f"rag-test-run-{timestamp}.json"


def check_summary_thresholds(
    summary_metrics: dict[str, float],
    thresholds: dict[str, float],
) -> list[str]:
    failures: list[str] = []
    for metric_name, threshold in thresholds.items():
        actual_value = summary_metrics.get(metric_name)
        if actual_value is None:
            failures.append(f"Missing summary metric: {metric_name}")
            continue
        if actual_value < threshold:
            failures.append(
                f"{metric_name}={actual_value:.4f} below threshold {threshold:.4f}"
            )
    return failures


def run_ragas_evaluation(
    documents_dir: Path,
    output_dir: Path | None = None,
) -> RagasRunResult:
    run_started_at = datetime.now().astimezone()
    report_dir = output_dir or DEFAULT_REPORTS_DIR
    report_dir.mkdir(parents=True, exist_ok=True)

    harness = RagIntegrationHarness(documents_dir)
    try:
        chunks_by_id = {chunk.chunk_id: chunk for chunk in harness.chunks}
        metrics = {
            "id_based_context_precision": IDBasedContextPrecision(),
            "id_based_context_recall": IDBasedContextRecall(),
            "nonllm_context_precision": NonLLMContextPrecisionWithReference(),
            "nonllm_context_recall": NonLLMContextRecall(),
        }
        case_reports: list[dict[str, object]] = []

        for case in RAG_EVAL_CASES:
            response = harness.run_question(case.question)
            retrieved_context_ids = [
                str(chunk["chunk_id"]) for chunk in response.retrieved_chunks
            ]
            retrieved_contexts = [str(chunk["text"]) for chunk in response.retrieved_chunks]
            reference_contexts = [
                chunks_by_id[chunk_id].text for chunk_id in case.reference_context_ids
            ]
            sample = SingleTurnSample(
                user_input=case.question,
                response=response.answer,
                reference=case.reference_answer,
                retrieved_contexts=retrieved_contexts,
                reference_contexts=reference_contexts,
                retrieved_context_ids=retrieved_context_ids,
                reference_context_ids=list(case.reference_context_ids),
            )

            metric_scores = {
                metric_name: float(metric.single_turn_score(sample))
                for metric_name, metric in metrics.items()
            }
            case_reports.append(
                {
                    "case_id": case.case_id,
                    "question": case.question,
                    "expected_documents": list(case.expected_documents),
                    "retrieved_document_names": [
                        str(document["document_name"]) for document in response.routed_documents
                    ],
                    "expected_answer_snippets": list(case.expected_answer_snippets),
                    "answer": response.answer,
                    "reference_answer": case.reference_answer,
                    "retrieved_context_ids": retrieved_context_ids,
                    "reference_context_ids": list(case.reference_context_ids),
                    "metrics": metric_scores,
                }
            )

        summary_metrics = {
            metric_name: sum(
                float(case_report["metrics"][metric_name]) for case_report in case_reports
            )
            / len(case_reports)
            for metric_name in metrics
        }
        threshold_failures = check_summary_thresholds(summary_metrics, SUMMARY_THRESHOLDS)
        report_payload = {
            "run_started_at": run_started_at.isoformat(),
            "documents_dir": str(documents_dir),
            "report_version": 1,
            "metrics": list(metrics.keys()),
            "summary_thresholds": SUMMARY_THRESHOLDS,
            "summary_metrics": summary_metrics,
            "passed": not threshold_failures,
            "threshold_failures": threshold_failures,
            "cases": case_reports,
        }
        report_path = build_report_path(report_dir, run_started_at)
        report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
        return RagasRunResult(
            report_path=report_path,
            report_payload=report_payload,
            threshold_failures=threshold_failures,
        )
    finally:
        harness.close()
