from client_ai_manager import (
    get_client_ai,
    get_all_client_ais,
    create_client_ai
)


def list_client_ais():
    return get_all_client_ais()


def open_client_ai(project_id):
    return get_client_ai(project_id)


def create_new_client_ai(
    project_id,
    name,
    client_name
):
    return create_client_ai(
        project_id=project_id,
        name=name,
        client_name=client_name
    )


def client_ai_exists(project_id):
    result = get_client_ai(project_id)

    return result.get(
        "success",
        False
    )


def get_client_ai_summary(project_id):
    result = get_client_ai(project_id)

    if not result.get("success"):
        return result

    ai = result["client_ai"]

    return {
        "project_id": ai["project_id"],
        "name": ai["name"],
        "client_name": ai["client_name"],
        "status": ai["status"],
        "website": ai["business"]["website"],
        "products": ai["business"]["products"],
        "faqs": len(ai["faqs"]),
        "knowledge_items": len(ai["knowledge"])
    }