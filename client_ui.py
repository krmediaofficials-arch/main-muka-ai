from fastapi import FastAPI, HTTPException
from chat_api import chat_with_client_ai
from client_ai_manager import get_client_ai, get_all_client_ais
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os


app = FastAPI(
    title="MUKA AI Client Gateway",
    version="2.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# CLIENT CHAT PAGE
# =========================================================

@app.get("/")
def client_chat_home():

    website_chat_path = os.path.join(
        os.path.dirname(__file__),
        "website_chat.html"
    )

    if not os.path.exists(website_chat_path):
        raise HTTPException(
            status_code=404,
            detail="website_chat.html not found."
        )

    return FileResponse(
        website_chat_path,
        media_type="text/html"
    )


# =========================================================
# CLIENT CONFIG
# =========================================================

@app.get("/client-config")
def client_config(project_id: str):

    project_id = str(project_id or "").strip()

    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="project_id is required."
        )

    try:
        lookup = get_client_ai(project_id)

    except Exception as error:
        print(
            "CLIENT CONFIG ERROR:",
            type(error).__name__,
            str(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load Client AI."
        )

    if not lookup.get("success"):
        raise HTTPException(
            status_code=404,
            detail=lookup.get(
                "message",
                "Client AI not found."
            )
        )

    client = lookup.get("client_ai")

    if not client:
        raise HTTPException(
            status_code=404,
            detail="Client AI not found."
        )

    return {
        "success": True,
        "client_ai": {
            "project_id": client.get(
                "project_id",
                project_id
            ),
            "client_name": client.get(
                "client_name",
                client.get(
                    "name",
                    "Client AI"
                )
            ),
            "website": client.get(
                "website",
                ""
            ),
            "status": client.get(
                "status",
                "active"
            )
        }
    }


# =========================================================
# LIST ALL CLIENT AIs
# =========================================================

@app.get("/client-ai/list")
def client_ai_list():

    try:
        result = get_all_client_ais()

    except Exception as error:
        print(
            "CLIENT AI LIST ERROR:",
            type(error).__name__,
            str(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load Client AIs."
        )

    if not result.get("success"):
        raise HTTPException(
            status_code=500,
            detail=result.get(
                "message",
                "Unable to load Client AIs."
            )
        )

    client_ais = result.get(
        "client_ais",
        {}
    )

    if not isinstance(client_ais, dict):
        client_ais = {}

    clients = []

    for project_id, client in client_ais.items():

        if not isinstance(client, dict):
            continue

        clients.append({
            "project_id": client.get(
                "project_id",
                project_id
            ),
            "client_name": client.get(
                "client_name",
                client.get(
                    "name",
                    "Client AI"
                )
            ),
            "website": client.get(
                "website",
                ""
            ),
            "status": client.get(
                "status",
                "active"
            )
        })

    return {
        "success": True,
        "client_ais": clients,
        "count": len(clients)
    }


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "online",
        "name": "MUKA AI",
        "type": "Multi-Client AI Gateway"
    }


# =========================================================
# CLIENT AI CHAT
# =========================================================

@app.post("/client-chat")
def client_chat(request: dict):

    message = str(
        request.get(
            "message",
            ""
        )
    ).strip()

    project_id = str(
        request.get(
            "project_id",
            ""
        )
    ).strip()

    session_id = str(
        request.get(
            "session_id",
            ""
        )
    ).strip()

    if not message:
        raise HTTPException(
            status_code=400,
            detail="Please enter a message."
        )

    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="project_id is required."
        )

    # -----------------------------------------------------
    # VERIFY CLIENT AI BEFORE CHAT
    # -----------------------------------------------------

    try:

        lookup = get_client_ai(
            project_id
        )

    except Exception as error:

        print(
            "CLIENT LOOKUP ERROR:",
            type(error).__name__,
            str(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to load Client AI."
        )

    if not lookup.get("success"):

        raise HTTPException(
            status_code=404,
            detail=lookup.get(
                "message",
                "Client AI not found."
            )
        )

    client = lookup.get(
        "client_ai"
    )

    if not client:

        raise HTTPException(
            status_code=404,
            detail="Client AI not found."
        )

    # -----------------------------------------------------
    # CHAT WITH SELECTED CLIENT AI
    # -----------------------------------------------------

    try:

        result = chat_with_client_ai(
    message,
    project_id,
    session_id
)

        if not result.get("success"):

            raise HTTPException(
                status_code=500,
                detail=result.get(
                    "reply",
                    result.get(
                        "message",
                        "Client AI error."
                    )
                )
            )

        return {

            "status":
                "success",

            "reply":
                result.get(
                    "reply",
                    ""
                ),

            "project_id":
                result.get(
                    "project_id",
                    project_id
                ),

            "client":
                result.get(
                    "client",
                    client.get(
                        "client_name",
                        client.get(
                            "name",
                            "Client AI"
                        )
                    )
                ),

            "mode":
                "client_ai"
        }

    except HTTPException:

        raise

    except Exception as error:

        print(
            "CLIENT CHAT ERROR:",
            type(error).__name__,
            str(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to process Client AI request."
        )


# =========================================================
# START CLIENT MUKA SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "client_ui:app",
        host="127.0.0.1",
        port=8001,
        reload=True
    )