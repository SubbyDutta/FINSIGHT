from __future__ import annotations

from pathlib import Path
from threading import Lock

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
except Exception:  
    A4 = None
    getSampleStyleSheet = None
    inch = 72
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None

from app.api.ai.vector_store import upsert_policy_document

try:
    from pypdf import PdfReader
except Exception: 
    PdfReader = None


ROOT_DIR = Path(".")
POLICY_FILES = [
    "DEMO_POLICY_01_GOVERNANCE.pdf",
    "DEMO_POLICY_02_RISK_AND_COMPLIANCE.pdf",
    "DEMO_POLICY_03_DATA_AND_PRIVACY.pdf",
    "DEMO_POLICY_04_MODEL_AND_PROMPT_SAFETY.pdf",
    "DEMO_POLICY_05_OPERATIONS_AND_INCIDENTS.pdf",
]

_lock = Lock()
_indexed_fingerprints: dict[str, tuple[int, int]] = {}


def _policy_sections() -> list[tuple[str, str]]:
    return [
        (
            "Corporate Governance",
            "FinSight AI enforces accountable ownership across ingestion, retrieval, model execution, and reporting. "
            "All production systems require clear owners, approval boundaries, and incident escalation protocols.",
        ),
        (
            "Risk and Compliance",
            "Market-facing responses must remain informational and must not present guaranteed outcomes. "
            "When uncertainty exists, the assistant explicitly states evidence limits and avoids fabricated claims.",
        ),
        (
            "Data Quality and Privacy",
            "Data sources must be validated for freshness, relevance, and integrity. "
            "Sensitive information is minimized, and operational logs retain only what is necessary for auditability.",
        ),
        (
            "Model and Prompt Safety",
            "Prompt templates enforce grounding, citation behavior, and refusal behavior for unsupported claims. "
            "Any policy-sensitive response must rely on retrieved chunks and include traceable context references.",
        ),
        (
            "Operations and Incident Response",
            "Production workflows must support reproducibility, rollback, and clear telemetry. "
            "On failure, teams capture retrieval context, model output, and input prompts for root-cause analysis.",
        ),
    ]


def _long_policy_text(title: str, body: str, repeat_index: int) -> str:
    controls = []
    start = repeat_index * 12 + 1
    end = start + 24
    for i in range(start, end):
        controls.append(
            f"Control {i}: Teams must maintain deterministic indexing, chunk lineage, and retrieval observability "
            "for policy and ticker-scoped documents across the FinSight platform."
        )

    return (
        f"{title}\n"
        f"Version: 1.0\n"
        "Applies to: News ingestion, vector indexing, RAG chat, and research report generation.\n\n"
        f"{body}\n\n"
        "Mandatory Rules:\n"
        "1. Ground all claims in retrieved evidence.\n"
        "2. Do not fabricate facts, prices, or events.\n"
        "3. Prefer ticker-scoped context for market analysis.\n"
        "4. Expose source traceability in response payloads.\n"
        "5. State uncertainty when evidence is incomplete.\n\n"
        "Operational Controls:\n"
        + "\n".join(controls)
    ).strip()


def generate_demo_policy_pdfs() -> list[Path]:
    missing = [ROOT_DIR / name for name in POLICY_FILES if not (ROOT_DIR / name).exists()]
    if missing and (A4 is None or getSampleStyleSheet is None or Paragraph is None):
        raise RuntimeError(
            "reportlab is required to generate demo policy PDFs. Install with: pip install reportlab"
        )

    styles = getSampleStyleSheet() if getSampleStyleSheet else None
    generated: list[Path] = []
    sections = _policy_sections()

    for idx, filename in enumerate(POLICY_FILES):
        path = ROOT_DIR / filename
        if path.exists():
            generated.append(path)
            continue

        title, body = sections[idx]
        content = _long_policy_text(title, body, repeat_index=idx)

        doc = SimpleDocTemplate(
            str(path),
            pagesize=A4,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )

        story = [Paragraph(title, styles["Title"]), Spacer(1, 12)]
        for block in content.split("\n\n"):
            if not block.strip():
                continue
            story.append(Paragraph(block.replace("\n", "<br/>"), styles["BodyText"]))
            story.append(Spacer(1, 8))

        doc.build(story)
        generated.append(path)

    return generated


def _discover_policy_pdfs() -> list[Path]:
    pdfs = sorted(ROOT_DIR.glob("*.pdf"), key=lambda p: p.name.lower())
    policy_named = [path for path in pdfs if "policy" in path.stem.lower()]
    return policy_named or pdfs


def _fingerprint(path: Path) -> tuple[int, int]:
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


def _extract_pdf_text(path: Path) -> str:
    if PdfReader is None:
        raise RuntimeError("pypdf is required for PDF ingestion. Install with: pip install pypdf")

    reader = PdfReader(str(path))
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text.strip())
    return "\n".join(pages).strip()


def index_policy_pdfs(paths: list[Path] | None = None) -> int:
    pdf_paths = paths or [ROOT_DIR / name for name in POLICY_FILES]
    indexed = 0

    for path in pdf_paths:
        if not path.exists() or path.suffix.lower() != ".pdf":
            continue
        text = _extract_pdf_text(path)
        if not text:
            continue

        policy_id = path.stem.lower()
        indexed += upsert_policy_document(
            policy_id=policy_id,
            title=path.stem.replace("_", " "),
            text=text,
            source=str(path),
        )

    return indexed


def ensure_policy_pdfs_indexed() -> dict[str, int]:
    global _indexed_fingerprints
    with _lock:
        generated = generate_demo_policy_pdfs()
        discovered = _discover_policy_pdfs()
        pdf_paths = sorted({*generated, *discovered}, key=lambda p: p.name.lower())
        current_keys = {str(path.resolve()) for path in pdf_paths}
        _indexed_fingerprints = {
            key: value for key, value in _indexed_fingerprints.items() if key in current_keys
        }

        indexed_chunks = 0
        for path in pdf_paths:
            key = str(path.resolve())
            fp = _fingerprint(path)
            if _indexed_fingerprints.get(key) == fp:
                continue
            indexed_chunks += index_policy_pdfs([path])
            _indexed_fingerprints[key] = fp

        return {"pdf_count": len(pdf_paths), "indexed_chunks": indexed_chunks}
