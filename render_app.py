from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse
from main import app


BASE_DIR = Path(__file__).resolve().parent
CLIENT_HTML = BASE_DIR / "website_chat.html"


@app.middleware("http")
async def client_domain_router(request: Request, call_next):
    host = request.headers.get("host", "").split(":")[0].lower()

    if host == "client.krmedia.in" and request.url.path in ("", "/"):
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