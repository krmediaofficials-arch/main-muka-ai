import base64
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from openai import OpenAI

from auth_session import get_session_user
from accounts import get_user


router = APIRouter()

BASE_DIR = Path("/opt/muka")
IMAGE_DIR = BASE_DIR / "creative_storage" / "images"
ASSETS_FILE = BASE_DIR / "creative_assets.json"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_MODEL = "gpt-image-2"


class ImageGenerateRequest(BaseModel):
    token: str
    prompt: str


def load_assets():
    if not ASSETS_FILE.exists():
        return {"assets": []}

    import json

    try:
        return json.loads(ASSETS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"assets": []}


def save_assets(data):
    import json

    temp = ASSETS_FILE.with_suffix(".tmp")
    temp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    temp.replace(ASSETS_FILE)


def get_authenticated_user(token):
    user_id = get_session_user(token)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Authentication required."
        )

    user = get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User account not found."
        )

    if user.get("status") != "active":
        raise HTTPException(
            status_code=403,
            detail="User account is not active."
        )

    return user


@router.post("/creative/generate-image")
def generate_image(request: ImageGenerateRequest):
    user = get_authenticated_user(request.token)

    prompt = (request.prompt or "").strip()

    if not prompt:
        raise HTTPException(status_code=400, detail="Image prompt is required.")

    if len(prompt) > 4000:
        raise HTTPException(
            status_code=400,
            detail="Image prompt is too long. Maximum 4000 characters.",
        )

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OpenAI API key is not configured.",
        )

    try:
        client = OpenAI(api_key=api_key)

        result = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Image generation failed: {str(exc)}",
        )

    if not result.data:
        raise HTTPException(
            status_code=502,
            detail="Image generation returned no image.",
        )

    image_data = getattr(result.data[0], "b64_json", None)

    if not image_data:
        raise HTTPException(
            status_code=502,
            detail="Image generation returned no image data.",
        )

    try:
        image_bytes = base64.b64decode(image_data)
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Generated image data could not be decoded.",
        )

    asset_id = uuid.uuid4().hex
    stored_filename = f"generated_{asset_id}.png"
    output_path = IMAGE_DIR / stored_filename

    output_path.write_bytes(image_bytes)

    assets = load_assets()

    asset = {
        "asset_id": asset_id,
        "workspace_id": user.get("workspace_id", "kr_media_workspace"),
        "type": "image",
        "filename": stored_filename,
        "stored_filename": stored_filename,
        "content_type": "image/png",
        "size": len(image_bytes),
        "uploaded_by": user.get("user_id"),
        "uploader_name": user.get("name") or user.get("full_name") or "MUKA AI",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "active",
        "source": "ai_generated",
        "generation_prompt": prompt,
    }

    assets.setdefault("assets", []).append(asset)
    save_assets(assets)

    return {
        "success": True,
        "asset": asset,
    }
