from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os

app = FastAPI(
    title="MUKA AI Client Chat"
)


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


@app.get("/health")
def health():

    return {
        "status": "online",
        "name": "MUKA AI",
        "type": "Client AI Chat",
        "client": "Roots & Leaves Collection"
    }


if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "client_ui:app",
        host="127.0.0.1",
        port=8001,
        reload=True
    )