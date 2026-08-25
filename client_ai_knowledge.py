import json
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent
KNOWLEDGE_FILE = BASE_DIR / "roots_leaves_client_ai_500_cleaned.json"

_cache: Dict[str, Any] | None = None


def load_client_knowledge() -> Dict[str, Any]:
    global _cache

    if _cache is not None:
        return _cache

    if not KNOWLEDGE_FILE.exists():
        raise FileNotFoundError(
            f"Client AI knowledge file not found: {KNOWLEDGE_FILE}"
        )

    with KNOWLEDGE_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("project_id") != "roots_leaves_client_ai":
        raise ValueError("Wrong client AI knowledge file/project_id")

    if int(data.get("faq_count", 0)) != len(data.get("qa_pairs", [])):
        raise ValueError("FAQ count does not match qa_pairs length")

    _cache = data
    return data


def get_client_facts() -> Dict[str, Any]:
    return load_client_knowledge().get("verified_facts", {})


def get_qa_pairs() -> List[Dict[str, Any]]:
    return load_client_knowledge().get("qa_pairs", [])


def build_knowledge_text(max_chars: int = 50000) -> str:
    data = load_client_knowledge()

    lines = [
        "CLIENT: Roots & Leaves Collection",
        "PROJECT: roots_leaves_client_ai",
        "SOURCE PRIORITY: LIVE OFFICIAL WEBSITE > APPROVED Q&A > OFFICIAL WEB SEARCH",
        "",
        "VERIFIED FACTS:",
        json.dumps(
            data.get("verified_facts", {}),
            ensure_ascii=False,
            indent=2,
        ),
        "",
        "APPROVED USAGE:",
        data.get("usage_approved", ""),
        "",
        "APPROVED CUSTOMER Q&A:",
    ]

    for item in data.get("qa_pairs", []):
        question = item.get("question", "").strip()
        answer = item.get("answer", "").strip()

        if not question or not answer:
            continue

        lines.append(f"Q: {question}")
        lines.append(f"A: {answer}")

        if sum(len(x) + 1 for x in lines) >= max_chars:
            break

    return "\n".join(lines)[:max_chars]
