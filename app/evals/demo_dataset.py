"""Versioned, source-checked benchmark; independent of answers and chunk boundaries."""
from hashlib import sha256
from pathlib import Path

import fitz

DATASET_VERSION = "northstar-18-v1"
AI = "northstar-ai-acceptable-use-policy.pdf"
HR = "northstar-employee-handbook.pdf"
SEC = "northstar-information-security-policy.pdf"
SOURCE_HASHES = {
    AI: "27c0c4d5196c3d9424aca82a4ecaa5901bce4c3fded40d5be265a1cbe7bbd546",
    HR: "3da2c8c67589317e00862f10f7371f364c7a8adcbd5aa5d1e769c1c2506d5aac",
    SEC: "d73500f3fb737b0cf7d501794b8e16997b0fb8d1089ee080ab0cc2b52914d932",
}


def case(id, question, reference, sources, *, group="single-policy", essential=""):
    return dict(id=id, question=question, reference=reference, source_pages=sources,
                group=group, answerable=group != "unanswerable", essential=essential or reference)


CASES = [
    case("public-ai", "Can I paste customer data into a public AI tool?",
         "No. Pasting customer data into a public AI tool is prohibited. Sensitive information must not be entered into unapproved AI tools.", [(AI, 1)]),
    case("ai-review", "What checks are required before using AI output externally?",
         "Verify facts, validate references, and check company policy and tone. Review accuracy and completeness, check for invented sources or unsupported claims, and escalate high-risk matters to Legal, Security, or People. Employees remain accountable.", [(AI, 2)]),
    case("ai-exception", "Who reviews requests for new AI tools or exceptions?",
         "Security and the relevant business owner must review requests. A privacy or supplier review may also be required depending on the tool and intended use.", [(AI, 2)]),
    case("public-summary", "May I use AI to summarise a public article?",
         "Yes. Summarising non-sensitive public content is permitted, provided the user reviews the output and checks accuracy before sharing.", [(AI, 1)]),
    case("core-hours", "What are our core working hours and exceptions?",
         "Employees are expected to be available from 10:00 to 16:00 on normal working days unless approved leave, flexible arrangements, or local time-zone adjustments apply.", [(HR, 1)]),
    case("sickness", "What should I do if I am sick on a working day?",
         "Notify your manager as early as possible, before 09:30 where practical. Same-day sickness requires notification, not approval.", [(HR, 1)]),
    case("probation", "How long is probation and what is reviewed?",
         "New employees normally complete six months of probation unless their contract states otherwise. Performance, conduct, attendance, collaboration, and role suitability are reviewed.", [(HR, 2)]),
    case("concerns", "Where can I raise concerns if going to my manager is inappropriate?",
         "Normally raise concerns with the manager or People team. Where that is inappropriate, employees may use a designated confidential reporting channel.", [(HR, 2)]),
    case("lost-laptop", "How should I report a lost company laptop?",
         "Report it immediately through the Security hotline or incident channel.", [(SEC, 2)]),
    case("passwords", "May I share my password or MFA code with a colleague?",
         "No. Keep passwords secret and do not share accounts, tokens, or MFA codes. Use strong unique credentials.", [(SEC, 1)]),
    case("classifications", "What are our information classifications and handling rules?",
         "Public information may be shared publicly once approved. Internal information is shared only with staff or approved partners who need it. Restricted information is stored only in approved systems with least-privilege access.", [(SEC, 1)]),
    case("personal-email", "Can I email restricted information to my personal account?",
         "No. Restricted information must not be copied to personal storage, personal email, or unapproved collaboration tools, including screenshots, exports, and pasted extracts.", [(SEC, 2)]),
    case("remote-security", "What approvals and security controls apply when working remotely?",
         "Remote work requires a suitable role, manager approval, and compliance with security requirements. Employees remain responsible for confidentiality and secure device use. Use approved devices and managed accounts for restricted data unless Security grants an exception, enable required screen locks, encryption and MFA, and use approved VPN or secure access methods.", [(HR, 1), (SEC, 1)], group="cross-policy"),
    case("ai-incident", "I accidentally pasted sensitive company data into public AI. What should I do?",
         "Sensitive data must not be entered into public or unapproved AI tools. Report the incident immediately to the Security channel and manager, even if unsure a breach occurred; follow the information security incident process.", [(AI, 1), (AI, 2), (SEC, 2)], group="cross-policy"),
    case("source-code", "Can I use company source code in an external AI coding tool?",
         "Only in approved tools, with Security review and an approved environment. Source code is restricted information and must remain in approved systems with least-privilege access. External services require supplier and security review; do not upload source code to public AI tools.", [(AI, 1), (AI, 2), (SEC, 1), (SEC, 2)], group="cross-policy"),
    case("policy-priority", "How should I reconcile the handbook, AI policy, and security policy when using AI with company data?",
         "Follow the more specific policy: the AI policy for AI use and security policy for confidential information. The AI policy supplements the handbook and security policy; where those impose tighter controls, the tighter control applies. Third-party disclosure must be expressly permitted by the AI policy, supplier controls, and information security policy.", [(AI, 1), (HR, 1), (HR, 2), (SEC, 2)], group="cross-policy"),
    case("annual-days", "How many days of paid annual leave do I get each year?",
         "The supplied policies do not specify an annual leave allowance. State that this cannot be determined from them; do not invent a number.", [(HR, 1), (HR, 2)], group="unanswerable"),
    case("approved-vendor", "Which specific AI vendor and subscription plan has Northstar approved?",
         "The supplied policies require approved tools but name no approved AI vendor or subscription plan. State that the documents do not provide this information; do not invent an approved vendor.", [(AI, 1), (AI, 2)], group="unanswerable"),
]


def load_cases(documents_dir: Path):
    pages = {}
    for name, expected in SOURCE_HASHES.items():
        path = documents_dir / name
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Benchmark source changed or missing: {name}. Update reviewed references first.")
        with fitz.open(path) as document:
            pages[name] = [page.get_text() for page in document]
    return [{**item, "document_pages": {name: len(texts) for name, texts in pages.items()}, "reference_contexts": [
        {"document_name": name, "page_number": number, "text": pages[name][number - 1]}
        for name, number in item["source_pages"]
    ]} for item in CASES]
