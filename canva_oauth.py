import base64
import hashlib
import json
import os
import secrets
import time
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse

from auth_session import get_session_user
from accounts import get_user


router = APIRouter()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CANVA_CLIENT_ID = os.getenv("CANVA_CLIENT_ID", "").strip()
CANVA_CLIENT_SECRET = os.getenv("CANVA_CLIENT_SECRET", "").strip()

CANVA_AUTH_URL = "https://www.canva.com/api/oauth/authorize"
CANVA_TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"

CANVA_REDIRECT_URI = os.getenv(
    "CANVA_REDIRECT_URI",
    "https://muka.krmedia.in/canva/oauth/callback"
).strip()

STATE_FILE = os.path.join(BASE_DIR, "canva_oauth_states.json")
CONNECTION_FILE = os.path.join(BASE_DIR, "canva_connections.json")


def _load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data

    except Exception as error:
        print(
            "CANVA JSON READ ERROR:",
            type(error).__name__,
            str(error)
        )
        return default


def _save_json(path, data):
    temp_path = path + ".tmp"

    with open(temp_path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    os.replace(temp_path, path)


def _create_pkce():
    verifier = secrets.token_urlsafe(64)

    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(
            verifier.encode("ascii")
        ).digest()
    ).rstrip(b"=").decode("ascii")

    return verifier, challenge


def _require_muka_user(token):
    user_id = get_session_user(token)

    if not user_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired MUKA session."
        )

    user = get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=401,
            detail="MUKA user account not found."
        )

    if user.get("status") != "active":
        raise HTTPException(
            status_code=403,
            detail="MUKA user account is not active."
        )

    return user


@router.get("/canva/oauth/start")
def canva_oauth_start(token: str):
    user = _require_muka_user(token)

    if not CANVA_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="CANVA_CLIENT_ID is not configured."
        )

    verifier, challenge = _create_pkce()
    state = secrets.token_urlsafe(32)

    states = _load_json(STATE_FILE, {})

    states[state] = {
        "user_id": user["user_id"],
        "workspace_id": user.get(
            "workspace_id",
            "kr_media_workspace"
        ),
        "code_verifier": verifier,
        "created_at": int(time.time())
    }

    _save_json(STATE_FILE, states)

    params = {
        "response_type": "code",
        "client_id": CANVA_CLIENT_ID,
        "redirect_uri": CANVA_REDIRECT_URI,
        "state": state,
        "scope": "asset:read asset:write design:content:read design:content:write design:meta:read",
        "code_challenge": challenge,
        "code_challenge_method": "S256"
    }

    return RedirectResponse(
        CANVA_AUTH_URL + "?" + urlencode(params)
    )


@router.get("/canva/oauth/callback")
async def canva_oauth_callback(
    code: str = None,
    state: str = None,
    error: str = None
):
    if error:
        return JSONResponse(
            {
                "success": False,
                "error": error
            },
            status_code=400
        )

    if not code or not state:
        return JSONResponse(
            {
                "success": False,
                "error": "Canva OAuth callback is missing code or state."
            },
            status_code=400
        )

    states = _load_json(STATE_FILE, {})
    oauth_state = states.pop(state, None)

    _save_json(STATE_FILE, states)

    if not oauth_state:
        return JSONResponse(
            {
                "success": False,
                "error": "Invalid or expired Canva OAuth state."
            },
            status_code=400
        )

    if int(time.time()) - int(
        oauth_state.get("created_at", 0)
    ) > 600:
        return JSONResponse(
            {
                "success": False,
                "error": "Canva OAuth state has expired."
            },
            status_code=400
        )

    if not CANVA_CLIENT_ID or not CANVA_CLIENT_SECRET:
        return JSONResponse(
            {
                "success": False,
                "error": "Canva OAuth credentials are not configured."
            },
            status_code=500
        )

    token_payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": CANVA_REDIRECT_URI,
        "client_id": CANVA_CLIENT_ID,
        "client_secret": CANVA_CLIENT_SECRET,
        "code_verifier": oauth_state["code_verifier"]
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                CANVA_TOKEN_URL,
                data=token_payload,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )

        response_data = response.json()

    except Exception as error:
        print(
            "CANVA TOKEN ERROR:",
            type(error).__name__,
            str(error)
        )

        return JSONResponse(
            {
                "success": False,
                "error": "Unable to connect to Canva token service."
            },
            status_code=502
        )

    if response.status_code >= 400:
        print(
            "CANVA TOKEN RESPONSE ERROR:",
            response.status_code,
            response_data
        )

        return JSONResponse(
            {
                "success": False,
                "error": "Canva authorization could not be completed."
            },
            status_code=502
        )

    connections = _load_json(CONNECTION_FILE, {})

    user_id = oauth_state["user_id"]

    connections[user_id] = {
        "user_id": user_id,
        "workspace_id": oauth_state.get(
            "workspace_id",
            "kr_media_workspace"
        ),
        "access_token": response_data.get("access_token"),
        "refresh_token": response_data.get("refresh_token"),
        "token_type": response_data.get("token_type"),
        "expires_in": response_data.get("expires_in"),
        "scope": response_data.get("scope"),
        "connected_at": int(time.time())
    }

    _save_json(CONNECTION_FILE, connections)
    access_token = response_data.get("access_token")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            editor_response = await client.post(
                "https://api.canva.com/rest/v1/designs",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "type": "type_and_asset",
                    "design_type": {
                        "type": "custom",
                        "width": 1080,
                        "height": 1080
                    },
                    "title": "MUKA Image Editing"
                }
            )

        editor_data = editor_response.json()

    except Exception as error:
        print(
            "CANVA EDITOR CREATE ERROR:",
            type(error).__name__,
            str(error)
        )
        return JSONResponse(
            {
                "success": False,
                "error": "Canva connected, but the editor could not be opened."
            },
            status_code=502
        )

    if editor_response.status_code >= 400:
        print(
            "CANVA EDITOR CREATE RESPONSE ERROR:",
            editor_response.status_code,
            editor_data
        )
        return JSONResponse(
            {
                "success": False,
                "error": "Canva connected, but the editor could not be opened."
            },
            status_code=502
        )

    edit_url = (
        editor_data
        .get("design", {})
        .get("urls", {})
        .get("edit_url")
    )

    if not edit_url:
        return JSONResponse(
            {
                "success": False,
                "error": "Canva connected, but no editor URL was returned."
            },
            status_code=502
        )

    return RedirectResponse(
        edit_url,
        status_code=303
    )


async def _refresh_canva_access_token(user_id, connection):
    refresh_token = connection.get("refresh_token")

    if not refresh_token:
        return None

    credentials = f"{CANVA_CLIENT_ID}:{CANVA_CLIENT_SECRET}".encode("utf-8")
    basic_auth = base64.b64encode(credentials).decode("ascii")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                CANVA_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token
                },
                headers={
                    "Authorization": f"Basic {basic_auth}",
                    "Content-Type": "application/x-www-form-urlencoded"
                }
            )

        response_data = response.json()

    except Exception as error:
        print(
            "CANVA REFRESH ERROR:",
            type(error).__name__,
            str(error)
        )
        return None

    if response.status_code >= 400:
        print(
            "CANVA REFRESH RESPONSE ERROR:",
            response.status_code,
            response_data
        )
        return None

    new_access_token = response_data.get("access_token")
    new_refresh_token = response_data.get("refresh_token")

    if not new_access_token or not new_refresh_token:
        print("CANVA REFRESH RESPONSE MISSING TOKENS")
        return None

    connections = _load_json(CONNECTION_FILE, {})
    current = connections.get(user_id, connection)

    current["access_token"] = new_access_token
    current["refresh_token"] = new_refresh_token
    current["token_type"] = response_data.get(
        "token_type",
        current.get("token_type")
    )
    current["expires_in"] = response_data.get(
        "expires_in",
        current.get("expires_in")
    )
    current["scope"] = response_data.get(
        "scope",
        current.get("scope")
    )
    current["refreshed_at"] = int(time.time())

    connections[user_id] = current
    _save_json(CONNECTION_FILE, connections)

    print("CANVA TOKEN REFRESH: OK")

    return new_access_token


@router.post("/canva/editor")
async def canva_editor(token: str):
    user = _require_muka_user(token)

    connections = _load_json(CONNECTION_FILE, {})
    connection = connections.get(user["user_id"])

    if not connection or not connection.get("access_token"):
        raise HTTPException(
            status_code=401,
            detail="Canva is not connected."
        )

    access_token = connection["access_token"]

    async def create_canva_design(current_access_token):
        async with httpx.AsyncClient(timeout=30.0) as client:
            return await client.post(
                "https://api.canva.com/rest/v1/designs",
                headers={
                    "Authorization": f"Bearer {current_access_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "type": "type_and_asset",
                    "design_type": {
                        "type": "custom",
                        "width": 1080,
                        "height": 1080
                    },
                    "title": "MUKA Image Editing"
                }
            )

    try:
        response = await create_canva_design(access_token)
        response_data = response.json()

        if (
            response.status_code == 401
            and isinstance(response_data, dict)
            and response_data.get("code") == "invalid_access_token"
        ):
            refreshed_token = await _refresh_canva_access_token(
                user["user_id"],
                connection
            )

            if not refreshed_token:
                raise HTTPException(
                    status_code=401,
                    detail="Canva authorization has expired. Please reconnect Canva."
                )

            response = await create_canva_design(refreshed_token)
            response_data = response.json()

    except HTTPException:
        raise

    except Exception as error:
        print(
            "CANVA EDITOR ERROR:",
            type(error).__name__,
            str(error)
        )
        raise HTTPException(
            status_code=502,
            detail="Unable to connect to Canva."
        )

    if response.status_code >= 400:
        print(
            "CANVA EDITOR RESPONSE ERROR:",
            response.status_code,
            response_data
        )
        raise HTTPException(
            status_code=502,
            detail="Canva could not create the editing workspace."
        )

    edit_url = (
        response_data
        .get("design", {})
        .get("urls", {})
        .get("edit_url")
    )

    if not edit_url:
        raise HTTPException(
            status_code=502,
            detail="Canva did not return an editor URL."
        )

    return {
        "success": True,
        "edit_url": edit_url
    }


@router.get("/canva/status")
def canva_status(token: str):
    user = _require_muka_user(token)

    connections = _load_json(CONNECTION_FILE, {})

    connection = connections.get(user["user_id"])

    required_scopes = {
        "asset:read",
        "asset:write",
        "design:content:read",
        "design:content:write",
        "design:meta:read"
    }

    granted_scope = set(
        (connection.get("scope") or "").split()
    ) if connection else set()

    return {
        "success": True,
        "connected": bool(
            connection
            and connection.get("access_token")
            and required_scopes.issubset(granted_scope)
        ),
        "reauthorization_required": bool(
            connection
            and connection.get("access_token")
            and not required_scopes.issubset(granted_scope)
        )
    }
