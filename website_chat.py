from muka_client_bridge import get_client_ai_summary


def get_website_chat_config():

    client_id = "roots_leaves_client_ai"

    client = get_client_ai_summary(client_id)

    if "project_id" not in client:
        return {
            "success": False,
            "message": "Roots & Leaves Client AI not found."
        }

    return {
        "success": True,

        "chat": {
            "name": "MUKA AI",
            "subtitle": "Roots & Leaves Collection AI Assistant",

            "client_ai": {
                "project_id": client["project_id"],
                "client_name": client["client_name"],
                "status": client["status"]
            },

            "features": {
                "product_questions": True,
                "product_recommendations": True,
                "sales_assistance": True,
                "lead_capture": True
            }
        }
    }


def health_check():

    config = get_website_chat_config()

    if not config["success"]:
        return {
            "status": "error",
            "message": config["message"]
        }

    return {
        "status": "online",
        "name": "MUKA AI",
        "client": "Roots & Leaves Collection"
    }