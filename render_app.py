from pathlib import Path

from fastapi.responses import FileResponse

from main import app


BASE_DIR = Path(__file__).resolve().parent
CLIENT_HTML = BASE_DIR / "website_chat.html"


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