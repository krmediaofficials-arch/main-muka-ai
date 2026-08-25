from chat_engine import prepare_client_context
from ai_response import generate_ai_response


def chat_with_client_ai(
    message,
    project_id="roots_leaves_client_ai"
):

    context = prepare_client_context(
        project_id
    )

    if not context.get("success"):
        return {
            "success": False,
            "reply": "Client AI is not available."
        }

    result = generate_ai_response(
        message,
        context
    )

    return result