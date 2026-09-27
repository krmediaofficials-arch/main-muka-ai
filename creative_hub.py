from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from auth_session import get_session_user
from accounts import get_user
from datetime import datetime, timezone
from pathlib import Path
import json
import uuid
import mimetypes


router = APIRouter(
    prefix="/creative",
    tags=["Creative Hub"]
)


# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

STORAGE_DIR = BASE_DIR / "creative_storage"
IMAGE_DIR = STORAGE_DIR / "images"
VIDEO_DIR = STORAGE_DIR / "videos"

ASSET_FILE = BASE_DIR / "creative_assets.json"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# CONFIG
# =========================================================

MAX_IMAGE_SIZE = 25 * 1024 * 1024
MAX_VIDEO_SIZE = 500 * 1024 * 1024

ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif"
}

ALLOWED_VIDEO_TYPES = {
    "video/mp4",
    "video/webm",
    "video/quicktime"
}


# =========================================================
# JSON HELPERS
# =========================================================

def load_assets():
    if not ASSET_FILE.exists():
        return {"assets": []}

    try:
        with open(
            ASSET_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {"assets": []}

        if not isinstance(data.get("assets"), list):
            data["assets"] = []

        return data

    except Exception as error:
        print(
            "CREATIVE ASSET READ ERROR:",
            type(error).__name__,
            str(error)
        )
        return {"assets": []}


def save_assets(data):
    temp_file = ASSET_FILE.with_suffix(".tmp")

    with open(
        temp_file,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    temp_file.replace(ASSET_FILE)


# =========================================================
# AUTH
# =========================================================

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


# =========================================================
# FILE HELPERS
# =========================================================

def safe_filename(filename):
    filename = Path(filename or "file").name

    cleaned = "".join(
        character
        for character in filename
        if character.isalnum()
        or character in "._- "
    ).strip()

    return cleaned or "file"


def get_file_type(content_type):
    if content_type in ALLOWED_IMAGE_TYPES:
        return "image"

    if content_type in ALLOWED_VIDEO_TYPES:
        return "video"

    return None


# =========================================================
# UPLOAD
# =========================================================

@router.post("/upload")
async def upload_creative(
    token: str,
    file: UploadFile = File(...)
):
    user = get_authenticated_user(token)

    content_type = (
        file.content_type
        or mimetypes.guess_type(
            file.filename or ""
        )[0]
        or ""
    ).lower()

    asset_type = get_file_type(content_type)

    if not asset_type:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Supported images: JPG, PNG, WEBP, GIF. "
                "Supported videos: MP4, WEBM, MOV."
            )
        )

    max_size = (
        MAX_IMAGE_SIZE
        if asset_type == "image"
        else MAX_VIDEO_SIZE
    )

    asset_id = "asset_" + uuid.uuid4().hex

    original_filename = safe_filename(
        file.filename
    )

    extension = Path(
        original_filename
    ).suffix.lower()

    if not extension:
        extension = (
            mimetypes.guess_extension(
                content_type
            )
            or ""
        )

    stored_filename = (
        asset_id + extension
    )

    storage_dir = (
        IMAGE_DIR
        if asset_type == "image"
        else VIDEO_DIR
    )

    storage_path = storage_dir / stored_filename

    total_size = 0

    try:
        with open(
            storage_path,
            "wb"
        ) as output:

            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                total_size += len(chunk)

                if total_size > max_size:
                    output.close()

                    if storage_path.exists():
                        storage_path.unlink()

                    raise HTTPException(
                        status_code=413,
                        detail=(
                            f"{asset_type.title()} "
                            f"file is too large."
                        )
                    )

                output.write(chunk)

    except HTTPException:
        raise

    except Exception as error:

        if storage_path.exists():
            storage_path.unlink()

        print(
            "CREATIVE UPLOAD ERROR:",
            type(error).__name__,
            str(error)
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to save creative asset."
        )

    finally:
        await file.close()

    workspace_id = user.get(
        "workspace_id",
        "kr_media_workspace"
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    asset = {
        "asset_id": asset_id,
        "workspace_id": workspace_id,
        "type": asset_type,
        "filename": original_filename,
        "stored_filename": stored_filename,
        "content_type": content_type,
        "size": total_size,
        "uploaded_by": user.get("user_id"),
        "uploader_name": user.get("name"),
        "created_at": now,
        "status": "active"
    }

    data = load_assets()

    data["assets"].append(asset)

    save_assets(data)

    return {
        "success": True,
        "message": (
            f"{asset_type.title()} uploaded successfully."
        ),
        "asset": asset
    }


# =========================================================
# LIST SHARED CREATIVE LIBRARY
# =========================================================

@router.get("/assets")
def list_creative_assets(token: str):
    user = get_authenticated_user(token)

    workspace_id = user.get(
        "workspace_id",
        "kr_media_workspace"
    )

    data = load_assets()

    assets = [
        asset
        for asset in data["assets"]
        if asset.get("workspace_id") == workspace_id
        and asset.get("status") == "active"
    ]

    assets.sort(
        key=lambda item: item.get(
            "created_at",
            ""
        ),
        reverse=True
    )

    return {
        "success": True,
        "workspace_id": workspace_id,
        "count": len(assets),
        "assets": assets
    }


# =========================================================
# GET SINGLE ASSET
# =========================================================

@router.get("/assets/{asset_id}")
def get_creative_asset(
    asset_id: str,
    token: str
):
    user = get_authenticated_user(token)

    workspace_id = user.get(
        "workspace_id",
        "kr_media_workspace"
    )

    data = load_assets()

    for asset in data["assets"]:

        if (
            asset.get("asset_id") == asset_id
            and asset.get("workspace_id") == workspace_id
            and asset.get("status") == "active"
        ):
            return {
                "success": True,
                "asset": asset
            }

    raise HTTPException(
        status_code=404,
        detail="Creative asset not found."
    )


# =========================================================
# DOWNLOAD / VIEW ASSET
# =========================================================

@router.get("/assets/{asset_id}/file")
def serve_creative_asset(
    asset_id: str,
    token: str
):
    user = get_authenticated_user(token)

    workspace_id = user.get(
        "workspace_id",
        "kr_media_workspace"
    )

    data = load_assets()

    for asset in data["assets"]:

        if (
            asset.get("asset_id") == asset_id
            and asset.get("workspace_id") == workspace_id
            and asset.get("status") == "active"
        ):

            asset_type = asset.get("type")

            storage_dir = (
                IMAGE_DIR
                if asset_type == "image"
                else VIDEO_DIR
            )

            storage_path = (
                storage_dir
                / asset.get("stored_filename", "")
            )

            if not storage_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="Stored creative file not found."
                )

            return FileResponse(
                path=str(storage_path),
                media_type=asset.get(
                    "content_type",
                    "application/octet-stream"
                ),
                filename=asset.get(
                    "filename",
                    "creative"
                )
            )

    raise HTTPException(
        status_code=404,
        detail="Creative asset not found."
    )
