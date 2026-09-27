from client_ai_manager import get_client_ai
from client_ai_knowledge import load_client_knowledge


def _extract_and_normalize_domain(raw_url):
    """Normalize raw URL/domain string by stripping protocols, paths, and www prefixes."""
    if not raw_url or not isinstance(raw_url, str):
        return ""
    
    clean_url = raw_url.strip().lower()
    # Strip protocol
    clean_url = clean_url.replace("https://", "").replace("http://", "")
    # Strip paths / query parameters
    domain = clean_url.split("/")[0].split("?")[0].split("#")[0]
    # Strip www prefix
    if domain.startswith("www."):
        domain = domain[4:]
        
    return domain.strip()


def prepare_client_context(project_id):
    result = get_client_ai(project_id)

    if not result.get("success"):
        return {
            "success": False,
            "message": "Client AI not found"
        }

    ai = result["client_ai"]
    rules = dict(ai.get("rules", {}) or {})
    business = ai.get("business", {}) or {}

    # Domain Extraction Protocol (1. rules.allowed_domain -> 2. business.website)
    allowed_domain = _extract_and_normalize_domain(rules.get("allowed_domain"))
    if not allowed_domain:
        allowed_domain = _extract_and_normalize_domain(business.get("website"))

    # Strict Zero-Trust Enforcement: Reject execution if no authentic domain exists
    if not allowed_domain:
        return {
            "success": False,
            "message": f"CONFIGURATION ERROR: Missing authentic allowed_domain or website for project ({project_id}). Execution halted for security."
        }

    # Lock validated domain back into rules dictionary
    rules["allowed_domain"] = allowed_domain

    # Preserve existing client knowledge
    knowledge = list(ai.get("knowledge", []) or [])

    # Append approved knowledge source with explicit project ownership
    approved_data = load_client_knowledge()
    usage_approved = approved_data.get("usage_approved", "")

    if usage_approved:
        knowledge.append(
            {
                "project_id": ai.get("project_id"),
                "title": "Approved Product Usage",
                "content": usage_approved
            }
        )

    return {
        "success": True,
        "project_id": ai.get("project_id"),
        "name": ai.get("name"),
        "client_name": ai.get("client_name"),
        "status": ai.get("status"),
        "business": business,
        "personality": ai.get("personality", {}),
        "rules": rules,
        "faqs": ai.get("faqs", []),
        "knowledge": knowledge,
        "conversation_flow": ai.get("conversation_flow", [])
    }