from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse
from main import app


BASE_DIR = Path(__file__).resolve().parent
CLIENT_HTML = BASE_DIR / "website_chat.html"


@app.middleware("http")
async def client_domain_router(request: Request, call_next):
    host = request.headers.get("host", "").split(":")[0].lower()
    path = request.url.path.rstrip("/")

    # Public Client AI domain
    # https://client.krmedia.in/<project_id>
    if host == "client.krmedia.in":

        # Root client page
        if path == "":
            if CLIENT_HTML.exists():
                return FileResponse(
                    CLIENT_HTML,
                    media_type="text/html"
                )

        # Dynamic Client AI page
        # Example:
        # /roots_leaves_client_ai
        # /test_client_ai_123
        if path.startswith("/") and path.count("/") == 1:
            project_id = path[1:].strip()

            # Do not intercept known application/API paths
            if project_id not in ("client", "client-chat", "docs", "redoc", "openapi.json"):
                if CLIENT_HTML.exists():
                    return FileResponse(
                        CLIENT_HTML,
                        media_type="text/html"
                    )

    return await call_next(request)


@app.get("/client")
@app.get("/client/")
def client_muka_ai():
    if not CLIENT_HTML.exists():
        return {
            "success": False,
            "message": "website_chat.html not found."
        }

    return FileResponse(
        CLIENT_HTML,
        media_type="text/html"
    )
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8001
    )
