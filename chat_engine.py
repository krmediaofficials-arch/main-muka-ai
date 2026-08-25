from client_ai_manager import get_client_ai


def prepare_client_context(project_id):

    result = get_client_ai(
        project_id
    )

    if not result.get("success"):

        return {
            "success": False,
            "message": "Client AI not found"
        }

    client = result["client_ai"]

    return {
        "success": True,

        "project_id":
            client.get(
                "project_id",
                project_id
            ),

        "client_name":
            client.get(
                "client_name",
                ""
            ),

        "business":
            client.get(
                "business",
                {}
            ),

        "personality":
            client.get(
                "personality",
                {}
            ),

        "rules":
            client.get(
                "rules",
                {}
            ),

        "faqs":
            client.get(
                "faqs",
                []
            ),

        "knowledge":
            client.get(
                "knowledge",
                []
            ),

        "conversation_flow":
            client.get(
                "conversation_flow",
                []
            )
    }


def process_message(
    message,
    project_id="roots_leaves_client_ai"
):

    if not message or not message.strip():

        return {
            "success": False,
            "reply": "Please enter a message."
        }

    context = prepare_client_context(
        project_id
    )

    if not context["success"]:

        return {
            "success": False,
            "reply": "Client AI is not available."
        }

    return {
        "success": True,

        "reply":
            "Message received by MUKA AI.",

        "client":
            context["client_name"],

        "message":
            message
    }