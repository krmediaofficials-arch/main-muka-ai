import base64
import json
import os
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from openai import OpenAI
from pydantic import BaseModel

from auth_session import get_session_user
from accounts import get_user


router = APIRouter()

BASE_DIR = Path("/opt/muka")
WORKSPACE_DIR = BASE_DIR / "creative_generation_workspace"
SESSIONS_FILE = BASE_DIR / "creative_generation_sessions.json"
CREATIVE_ASSETS_FILE = BASE_DIR / "creative_assets.json"
CREATIVE_IMAGES_DIR = BASE_DIR / "creative_storage" / "images"
CONVERSATIONS_FILE = BASE_DIR / "main_conversations.json"

WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
CREATIVE_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_MODEL = "gpt-image-2"


class GenerationRequest(BaseModel):
    token: str
    session_id: str
    prompt: str


class SessionRequest(BaseModel):
    token: str
    session_id: str


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


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def load_sessions():
    if not SESSIONS_FILE.exists():
        return {}

    try:
        data = json.loads(SESSIONS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_sessions(data):
    tmp = SESSIONS_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    tmp.replace(SESSIONS_FILE)


def load_conversations():
    if not CONVERSATIONS_FILE.exists():
        return {}

    try:
        data = json.loads(CONVERSATIONS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_conversations(data):
    tmp = CONVERSATIONS_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    tmp.replace(CONVERSATIONS_FILE)


def create_generation_conversation(user_id, session_id):
    conversations = load_conversations()

    if user_id not in conversations or not isinstance(conversations.get(user_id), dict):
        conversations[user_id] = {}

    conversation = {
        "id": session_id,
        "title": "MUKA Image Generation",
        "conversation_type": "image_generation",
        "generation_session_id": session_id,
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "messages": []
    }

    conversations[user_id][session_id] = conversation
    save_conversations(conversations)

    return conversation


def load_generation_conversation(user_id, session_id):
    conversations = load_conversations()
    user_conversations = conversations.get(user_id, {})

    if not isinstance(user_conversations, dict):
        return None

    conversation = user_conversations.get(session_id)

    if not isinstance(conversation, dict):
        return None

    if conversation.get("conversation_type") != "image_generation":
        return None

    return conversation


def save_generation_conversation(user_id, conversation):
    conversations = load_conversations()

    if user_id not in conversations or not isinstance(conversations.get(user_id), dict):
        conversations[user_id] = {}

    conversation["updated_at"] = now_iso()
    conversations[user_id][conversation["id"]] = conversation

    save_conversations(conversations)


def append_generation_message(user_id, session_id, role, content, **extra):
    conversation = load_generation_conversation(user_id, session_id)

    if conversation is None:
        conversation = create_generation_conversation(user_id, session_id)

    message = {
        "id": str(uuid.uuid4()),
        "role": role,
        "content": content,
        "timestamp": now_iso()
    }

    message.update(extra)
    conversation.setdefault("messages", []).append(message)

    save_generation_conversation(user_id, conversation)

    return message


def session_dir(session_id):
    return WORKSPACE_DIR / session_id


def get_session_for_user(session_id, user):
    sessions = load_sessions()
    session = sessions.get(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Generation session not found.")

    if session.get("user_id") != str(user.get("id") or user.get("user_id")):
        raise HTTPException(status_code=403, detail="Generation session access denied.")

    return sessions, session


def clean_prompt(prompt):
    value = (prompt or "").strip()

    if not value:
        raise HTTPException(status_code=400, detail="Image prompt is required.")

    if len(value) > 4000:
        raise HTTPException(status_code=400, detail="Image prompt is too long.")

    return value


def save_generation_image(session_id, version, image_bytes):
    folder = session_dir(session_id)
    folder.mkdir(parents=True, exist_ok=True)

    filename = f"version_{version}.png"
    path = folder / filename
    path.write_bytes(image_bytes)

    return path


def generate_new_image(prompt, reference_path=None):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured."
        )

    client = OpenAI(api_key=api_key)

    if reference_path:
        with reference_path.open("rb") as reference_file:
            result = client.images.edit(
                model=IMAGE_MODEL,
                image=[reference_file],
                prompt=prompt,
            )
    else:
        result = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
        )

    if not result.data or not result.data[0].b64_json:
        raise RuntimeError("OpenAI returned no generated image.")

    return base64.b64decode(result.data[0].b64_json)


def edit_existing_image(image_path, prompt, reference_path=None):
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY is not configured."
        )

    client = OpenAI(api_key=api_key)

    if reference_path:
        with image_path.open("rb") as image_file, reference_path.open("rb") as reference_file:
            result = client.images.edit(
                model=IMAGE_MODEL,
                image=[image_file, reference_file],
                prompt=prompt,
            )
    else:
        with image_path.open("rb") as image_file:
            result = client.images.edit(
                model=IMAGE_MODEL,
                image=image_file,
                prompt=prompt,
            )

    if not result.data or not result.data[0].b64_json:
        raise RuntimeError("OpenAI returned no edited image.")

    return base64.b64decode(result.data[0].b64_json)


@router.post("/creative/generation/session")
def create_generation_session(token: str):
    user = get_authenticated_user(token)

    user_id = str(user.get("id") or user.get("user_id"))
    session_id = "img_" + uuid.uuid4().hex

    sessions = load_sessions()

    sessions[session_id] = {
        "session_id": session_id,
        "user_id": user_id,
        "workspace_id": "kr_media_workspace",
        "status": "active",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "versions": [],
        "accepted_asset_id": None,
    }

    save_sessions(sessions)
    create_generation_conversation(user_id, session_id)

    return {
        "success": True,
        "session_id": session_id,
        "title": "MUKA Image Generation"
    }


@router.get("/creative/generation/session/{session_id}")
def get_generation_session(session_id: str, token: str):
    user = get_authenticated_user(token)

    sessions, session = get_session_for_user(session_id, user)

    user_id = str(user.get("id") or user.get("user_id"))
    conversation = load_generation_conversation(user_id, session_id)

    return {
        "success": True,
        "session": session,
        "conversation": conversation
    }



@router.post("/creative/generation/reference-upload")
async def upload_generation_reference(
    token: str = Form(...),
    session_id: str = Form(...),
    file: UploadFile = File(...)
):
    user = get_authenticated_user(token)

    sessions, session = get_session_for_user(session_id, user)

    if session.get("status") != "active":
        raise HTTPException(
            status_code=400,
            detail="Generation session is no longer active."
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Reference image is required."
        )

    content_type = (file.content_type or "").lower()

    allowed_types = {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
        "image/gif": ".gif"
    }

    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, PNG, WEBP or GIF reference images are allowed."
        )

    image_bytes = await file.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="Reference image is empty."
        )

    if len(image_bytes) > 25 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="Reference image must be 25MB or smaller."
        )

    folder = session_dir(session_id)
    folder.mkdir(parents=True, exist_ok=True)

    old_reference = session.get("reference_image")

    if old_reference:
        old_filename = old_reference.get("filename")
        if old_filename:
            old_path = folder / old_filename
            if old_path.exists():
                try:
                    old_path.unlink()
                except Exception:
                    pass

    reference_id = "ref_" + uuid.uuid4().hex
    filename = reference_id + allowed_types[content_type]
    path = folder / filename
    path.write_bytes(image_bytes)

    session["reference_image"] = {
        "reference_id": reference_id,
        "filename": filename,
        "original_filename": file.filename,
        "content_type": content_type,
        "size": len(image_bytes),
        "created_at": now_iso()
    }

    session["updated_at"] = now_iso()
    save_sessions(sessions)

    return {
        "success": True,
        "session_id": session_id,
        "reference_image": session["reference_image"]
    }


@router.post("/creative/generation/generate")
def generate_generation_image(request: GenerationRequest):
    user = get_authenticated_user(request.token)
    prompt = clean_prompt(request.prompt)

    sessions, session = get_session_for_user(request.session_id, user)

    if session.get("status") != "active":
        raise HTTPException(status_code=400, detail="Generation session is no longer active.")

    next_version = len(session.get("versions", [])) + 1

    reference_path = None
    reference_info = session.get("reference_image")
    if reference_info and reference_info.get("filename"):
        candidate = session_dir(request.session_id) / reference_info["filename"]
        if candidate.exists():
            reference_path = candidate

    try:
        image_bytes = generate_new_image(prompt, reference_path=reference_path)
        image_path = save_generation_image(
            request.session_id,
            next_version,
            image_bytes
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Image generation failed: {exc}"
        )

    version = {
        "version": next_version,
        "prompt": prompt,
        "filename": image_path.name,
        "created_at": now_iso(),
        "source": "generation"
    }

    session.setdefault("versions", []).append(version)
    session["updated_at"] = now_iso()
    session["last_prompt"] = prompt
    save_sessions(sessions)

    append_generation_message(
        str(user.get("id") or user.get("user_id")),
        request.session_id,
        "user",
        prompt
    )

    append_generation_message(
        str(user.get("id") or user.get("user_id")),
        request.session_id,
        "assistant",
        "Generated image",
        image_url=f"/creative/generation/image/{request.session_id}/{next_version}?token={request.token}",
        generation_session_id=request.session_id,
        version=next_version
    )

    return {
        "success": True,
        "session_id": request.session_id,
        "version": version,
        "image_url": f"/creative/generation/image/{request.session_id}/{next_version}?token={request.token}"
    }


@router.post("/creative/generation/refine")
def refine_generation_image(request: GenerationRequest):
    user = get_authenticated_user(request.token)
    prompt = clean_prompt(request.prompt)

    sessions, session = get_session_for_user(request.session_id, user)

    if session.get("status") != "active":
        raise HTTPException(status_code=400, detail="Generation session is no longer active.")

    versions = session.get("versions", [])

    if not versions:
        raise HTTPException(
            status_code=400,
            detail="There is no generated image to refine yet."
        )

    latest = versions[-1]
    source_path = session_dir(request.session_id) / latest["filename"]

    if not source_path.exists():
        raise HTTPException(
            status_code=404,
            detail="The current generation image is missing."
        )

    next_version = len(versions) + 1

    edit_prompt = (
        "Make a precise, minimal edit to the provided current image. "
        "The provided image is the source of truth and must remain visually "
        "the same except for the exact changes explicitly requested by the user. "
        "Do not redesign, recreate, recompose, replace, crop, resize, "
        "restyle, or change the camera angle. "
        "Preserve the exact subject/product identity, product packaging, "
        "layout, composition, framing, objects, typography, colors, "
        "lighting structure, proportions and visual details unless the user "
        "explicitly asks to change one of them. "
        "If the user asks to change only one element, change only that element "
        "and leave everything else as close to the provided image as possible.\n\n"
        "User's requested changes:\n"
        + prompt
    )

    try:
        image_bytes = edit_existing_image(
            source_path,
            edit_prompt
        )
        image_path = save_generation_image(
            request.session_id,
            next_version,
            image_bytes
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Image refinement failed: {exc}"
        )

    version = {
        "version": next_version,
        "prompt": prompt,
        "filename": image_path.name,
        "created_at": now_iso(),
        "source": "refinement",
        "based_on_version": latest["version"]
    }

    versions.append(version)
    session["updated_at"] = now_iso()
    session["last_prompt"] = prompt
    save_sessions(sessions)

    append_generation_message(
        str(user.get("id") or user.get("user_id")),
        request.session_id,
        "user",
        prompt
    )

    append_generation_message(
        str(user.get("id") or user.get("user_id")),
        request.session_id,
        "assistant",
        "Generated refined image",
        image_url=f"/creative/generation/image/{request.session_id}/{next_version}?token={request.token}",
        generation_session_id=request.session_id,
        version=next_version,
        based_on_version=latest["version"]
    )

    return {
        "success": True,
        "session_id": request.session_id,
        "version": version,
        "image_url": f"/creative/generation/image/{request.session_id}/{next_version}?token={request.token}"
    }


@router.get("/creative/generation/image/{session_id}/{version}")
def get_generation_image(session_id: str, version: int, token: str):
    user = get_authenticated_user(token)

    _, session = get_session_for_user(session_id, user)

    versions = session.get("versions", [])
    selected = next(
        (item for item in versions if int(item.get("version", 0)) == version),
        None
    )

    if not selected:
        raise HTTPException(status_code=404, detail="Generation version not found.")

    path = session_dir(session_id) / selected["filename"]

    if not path.exists():
        raise HTTPException(status_code=404, detail="Generation image file not found.")

    return FileResponse(
        path,
        media_type="image/png",
        filename=selected["filename"]
    )


@router.post("/creative/generation/accept")
def accept_generation(request: SessionRequest):
    user = get_authenticated_user(request.token)

    sessions, session = get_session_for_user(request.session_id, user)

    if session.get("status") != "active":
        raise HTTPException(status_code=400, detail="Generation session is no longer active.")

    versions = session.get("versions", [])

    if not versions:
        raise HTTPException(status_code=400, detail="No generated image to accept.")

    latest = versions[-1]
    source_path = session_dir(request.session_id) / latest["filename"]

    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Generated image file not found.")

    asset_id = "creative_" + uuid.uuid4().hex
    filename = f"muka_generated_{asset_id}.png"
    destination = CREATIVE_IMAGES_DIR / filename

    shutil.copy2(source_path, destination)

    try:
        assets = json.loads(
            CREATIVE_ASSETS_FILE.read_text(encoding="utf-8")
        ) if CREATIVE_ASSETS_FILE.exists() else {"assets": []}
    except Exception:
        assets = {"assets": []}

    if not isinstance(assets, dict):
        assets = {"assets": []}

    if not isinstance(assets.get("assets"), list):
        assets["assets"] = []

    user_id = str(user.get("id") or user.get("user_id"))
    uploader_name = (
        user.get("name")
        or user.get("full_name")
        or user.get("email")
        or "Team member"
    )

    asset = {
        "asset_id": asset_id,
        "workspace_id": "kr_media_workspace",
        "type": "image",
        "filename": filename,
        "original_filename": latest["filename"],
        "uploaded_by": user_id,
        "uploader_name": uploader_name,
        "created_at": now_iso(),
        "size": destination.stat().st_size,
        "status": "active",
        "source": "ai_generated",
        "generation_prompt": latest.get("prompt", "")
    }

    assets["assets"].append(asset)

    tmp = CREATIVE_ASSETS_FILE.with_suffix(".tmp")
    tmp.write_text(
        json.dumps(assets, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    tmp.replace(CREATIVE_ASSETS_FILE)

    session["status"] = "accepted"
    session["accepted_asset_id"] = asset_id
    session["updated_at"] = now_iso()
    sessions = load_sessions()
    sessions[request.session_id] = session
    save_sessions(sessions)

    return {
        "success": True,
        "asset": asset
    }


@router.post("/creative/generation/reject")
def reject_generation(request: SessionRequest):
    user = get_authenticated_user(request.token)

    sessions, session = get_session_for_user(request.session_id, user)

    session["status"] = "rejected"
    session["updated_at"] = now_iso()
    sessions[request.session_id] = session
    save_sessions(sessions)

    return {
        "success": True,
        "status": "rejected"
    }
