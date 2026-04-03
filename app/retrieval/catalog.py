from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PolicyDocument:
    document_id: str
    document_name: str
    title: str
    summary: str


POLICY_DOCUMENTS = [
    PolicyDocument(
        document_id="northstar-ai-acceptable-use-policy",
        document_name="northstar-ai-acceptable-use-policy.pdf",
        title="AI Acceptable Use Policy",
        summary=(
            "Rules for approved and prohibited generative AI usage, including restrictions on "
            "customer data, confidential information, review requirements, and governance."
        ),
    ),
    PolicyDocument(
        document_id="northstar-employee-handbook",
        document_name="northstar-employee-handbook.pdf",
        title="Employee Handbook",
        summary=(
            "Core working expectations, conduct, attendance, remote work, probation, and company "
            "systems usage guidance for employees."
        ),
    ),
    PolicyDocument(
        document_id="northstar-information-security-policy",
        document_name="northstar-information-security-policy.pdf",
        title="Information Security and Data Handling Policy",
        summary=(
            "Rules for information classification, storage, device security, authentication, "
            "external services, incident reporting, and restricted data handling."
        ),
    ),
]
