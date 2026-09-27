import uuid

from chat_engine import prepare_client_context
from ai_response_professional import generate_ai_response
from muka_client_intelligence import MukaClientIntelligence

# =========================================================
# MUKA CLIENT INTELLIGENCE
# =========================================================

_client_intelligence = MukaClientIntelligence()


# =========================================================
# CLIENT AI CHAT
# =========================================================

def chat_with_client_ai(
    message,
    project_id="roots_leaves_client_ai",
    session_id=None,
):

    if not message or not message.strip():
        return {
            "success": False,
            "reply": "Please enter a message.",
        }

    project_id = str(
        project_id or ""
    ).strip()

    if not project_id:
        project_id = "roots_leaves_client_ai"

    # -----------------------------------------------------
    # SESSION ID
    # -----------------------------------------------------

    if not session_id:
        session_id = str(
            uuid.uuid4()
        )

    session_id = str(
        session_id
    ).strip()

    # -----------------------------------------------------
    # EXISTING CLIENT AI CONTEXT
    # -----------------------------------------------------

    context = prepare_client_context(
        project_id
    )

    if not context.get("success"):
        return {
            "success": False,
            "reply": "Client AI is not available.",
        }

    # -----------------------------------------------------
    # MUKA CLIENT INTELLIGENCE
    # -----------------------------------------------------

    intelligence = None

    try:

        intelligence = _client_intelligence.process_message(
            session_id=session_id,
            client_id=project_id,
            message=message.strip(),
        )

    except Exception as error:

        print(
            "MUKA INTELLIGENCE ERROR:",
            type(error).__name__,
            str(error),
        )

        # Existing Client AI continues if
        # intelligence layer fails.

        intelligence = None

    # -----------------------------------------------------
    # ADD INTELLIGENCE TO EXISTING CLIENT CONTEXT
    # -----------------------------------------------------

    model_context = dict(
        context
    )

    if intelligence:

        model_context[
            "muka_client_intelligence"
        ] = intelligence

    # -----------------------------------------------------
    # -----------------------------------------------------
    # ADD EXISTING CONVERSATION HISTORY
    # -----------------------------------------------------

    try:

        conversation_history = _client_intelligence.get_messages(
            session_id=session_id,
            client_id=project_id,
        )

        model_context[
            "conversation_history"
        ] = conversation_history

    except Exception as error:

        print(
            "MUKA CONVERSATION HISTORY ERROR:",
            type(error).__name__,
            str(error),
        )

        model_context[
            "conversation_history"
        ] = []

    # -----------------------------------------------------
    # EXISTING CLIENT AI RESPONSE ENGINE
    # -----------------------------------------------------

    result = generate_ai_response(
        message.strip(),
        model_context,
    )

    # -----------------------------------------------------
    # STORE ASSISTANT RESPONSE
    # -----------------------------------------------------

    if (
        intelligence
        and isinstance(result, dict)
        and result.get("success")
        and result.get("reply")
    ):

        try:

            _client_intelligence.add_assistant_message(
                session_id=session_id,
                client_id=project_id,
                content=str(
                    result.get("reply")
                ).strip(),
            )

        except Exception as error:

            print(
                "MUKA INTELLIGENCE ASSISTANT MEMORY ERROR:",
                type(error).__name__,
                str(error),
            )

    # -----------------------------------------------------
    # RETURN RESULT
    # -----------------------------------------------------

    if not isinstance(result, dict):

        return {
            "success": False,
            "reply": "Invalid response received from Client AI.",
            "session_id": session_id,
            "project_id": project_id,
        }

    result["session_id"] = session_id

    return result
# =========================================================
# FASTAPI APPLICATION
# =========================================================

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="MUKA Client AI API",
)


class ClientChatRequest(BaseModel):
    message: str
    project_id: str = "roots_leaves_client_ai"
    session_id: str | None = None


@app.post("/client-chat")
def client_chat(request: ClientChatRequest):
    return chat_with_client_ai(
        message=request.message,
        project_id=request.project_id,
        session_id=request.session_id,
    )

# =========================================================
# FASTAPI SERVER
# =========================================================

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="MUKA Client AI")


class ClientChatRequest(BaseModel):
    message: str
    project_id: str = "roots_leaves_client_ai"
    session_id: str | None = None

@app.get("/")
def root():
    return {
        "success": True,
        "service": "MUKA Client AI",
        "status": "online",
        "client": "Roots & Leaves Collection",
        "endpoint": "/client-chat",
    }

@app.post("/client-chat")
def client_chat(request: ClientChatRequest):
    return chat_with_client_ai(
        message=request.message,
        project_id=request.project_id,
        session_id=request.session_id,
    )


