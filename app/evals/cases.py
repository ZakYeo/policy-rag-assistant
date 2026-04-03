from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RagEvalCase:
    case_id: str
    question: str
    expected_answer_snippets: tuple[str, ...]
    expected_documents: tuple[str, ...]
    reference_answer: str
    reference_context_ids: tuple[str, ...]


RAG_EVAL_CASES = [
    RagEvalCase(
        case_id="public-ai-customer-data",
        question="Can I put customer data into a public AI tool?",
        expected_answer_snippets=(
            "customer data into a public AI tool",
            "No Prohibited",
        ),
        expected_documents=("northstar-ai-acceptable-use-policy.pdf",),
        reference_answer=(
            "No. Customer data must not be pasted into a public AI tool. "
            "Only approved tools may be used for sensitive company data."
        ),
        reference_context_ids=(
            "northstar-ai-acceptable-use-policy-p1-c2",
            "northstar-ai-acceptable-use-policy-p2-c0",
        ),
    ),
    RagEvalCase(
        case_id="core-working-hours",
        question="What are the core working hours?",
        expected_answer_snippets=("between 10:00 and 16:00",),
        expected_documents=("northstar-employee-handbook.pdf",),
        reference_answer=(
            "Employees are expected to be available between 10:00 and 16:00 on "
            "normal working days unless approved arrangements apply."
        ),
        reference_context_ids=(
            "northstar-employee-handbook-p1-c2",
            "northstar-employee-handbook-p1-c1",
        ),
    ),
    RagEvalCase(
        case_id="lost-company-laptop",
        question="How do I report a lost company laptop?",
        expected_answer_snippets=(
            "Lost company laptop Immediately",
            "Security hotline or incident channel",
        ),
        expected_documents=("northstar-information-security-policy.pdf",),
        reference_answer=(
            "A lost company laptop must be reported immediately through the "
            "security hotline or incident channel."
        ),
        reference_context_ids=(
            "northstar-information-security-policy-p2-c1",
            "northstar-information-security-policy-p2-c0",
        ),
    ),
    RagEvalCase(
        case_id="password-sharing",
        question="Can I share passwords?",
        expected_answer_snippets=(
            "keep passwords secret",
            "Do not share accounts, tokens, or MFA codes",
        ),
        expected_documents=("northstar-information-security-policy.pdf",),
        reference_answer=(
            "No. Users must keep passwords secret and must not share accounts, "
            "tokens, or MFA codes."
        ),
        reference_context_ids=(
            "northstar-information-security-policy-p1-c1",
            "northstar-information-security-policy-p1-c0",
        ),
    ),
    RagEvalCase(
        case_id="remote-work",
        question="Is remote work allowed?",
        expected_answer_snippets=("Remote work is allowed only",),
        expected_documents=("northstar-employee-handbook.pdf",),
        reference_answer=(
            "Remote work is allowed only where the employee's role, manager "
            "approval, and security requirements allow it."
        ),
        reference_context_ids=(
            "northstar-employee-handbook-p1-c2",
            "northstar-employee-handbook-p1-c1",
        ),
    ),
]
