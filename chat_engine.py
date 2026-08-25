from client_ai_manager import get_client_ai
from website_knowledge import get_live_website_knowledge


def prepare_client_context(project_id="roots_leaves_client_ai"):
    result = get_client_ai(project_id)

    if not result.get("success"):
        return {
            "success": False,
            "message": "Client AI not found",
        }

    client = result["client_ai"]
    website = client.get("business", {}).get(
        "website",
        "https://rootsandleavescollection.in",
    )

    live_knowledge = get_live_website_knowledge(website)

    return {
        "success": True,
        "project_id": client.get("project_id", project_id),
        "client_name": client.get(
            "client_name",
            "Roots & Leaves Collection",
        ),
        "business": client.get("business", {}),
        "personality": client.get("personality", {}),
        "rules": client.get("rules", {}),
        "faqs": client.get("faqs", []),
        "knowledge": client.get("knowledge", []),
        "live_website": live_knowledge,
    }
