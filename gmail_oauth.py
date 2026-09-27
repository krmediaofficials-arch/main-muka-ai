import json
import os
import secrets
from datetime import datetime, timezone

from dotenv import load_dotenv
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

load_dotenv("/opt/muka/.env")

router = APIRouter(
    prefix="/mailbox",
    tags=["MUKA Mail Box"]
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]

SESSION_FILE = "/opt/muka/gmail_sessions.json"
TOKEN_FILE = "/opt/muka/gmail_tokens.json"


# =========================================================
# FILE HELPERS
# =========================================================

def load_json_file(path):
    if not os.path.exists(path):
        return {}

    try:
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except Exception as error:
        print(
            "GMAIL JSON READ ERROR:",
            type(error).__name__,
            str(error)
        )
        return {}


def save_json_file(path, data):
    temp_path = path + ".tmp"

    with open(
        temp_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )

    os.replace(temp_path, path)

    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


# =========================================================
# GOOGLE OAUTH
# =========================================================

def create_google_flow(state=None):

    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise RuntimeError(
            "Google OAuth credentials are not configured."
        )

    if not GOOGLE_REDIRECT_URI:
        raise RuntimeError(
            "GOOGLE_REDIRECT_URI is not configured."
        )

    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": (
                "https://accounts.google.com/o/oauth2/auth"
            ),
            "token_uri": (
                "https://oauth2.googleapis.com/token"
            ),
            "redirect_uris": [
                GOOGLE_REDIRECT_URI
            ],
        }
    }

    flow = Flow.from_client_config(
        client_config,
        scopes=GMAIL_SCOPES,
        state=state,
        redirect_uri=GOOGLE_REDIRECT_URI,
    )

    return flow


# =========================================================
# OAUTH STATE
# =========================================================

def create_oauth_state(user_id):

    state = secrets.token_urlsafe(32)

    sessions = load_json_file(SESSION_FILE)

    sessions[state] = {
        "user_id": user_id,
        "created_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "expires_at": (
            datetime.now(timezone.utc).timestamp() + 600
        )
    }

    save_json_file(
        SESSION_FILE,
        sessions
    )

    return state


def get_oauth_state(state):

    if not state:
        return None

    sessions = load_json_file(SESSION_FILE)

    session = sessions.get(state)

    if session is None:
        return None

    if session.get("expires_at", 0) < datetime.now(timezone.utc).timestamp():
        sessions.pop(state, None)
        save_json_file(SESSION_FILE, sessions)
        return None

    return session


def consume_oauth_state(state):

    if not state:
        return None

    sessions = load_json_file(SESSION_FILE)

    session = sessions.pop(state, None)

    if session is not None:
        save_json_file(
            SESSION_FILE,
            sessions
        )

        if session.get("expires_at", 0) < datetime.now(timezone.utc).timestamp():
            return None

    return session


# =========================================================
# TOKEN STORAGE
# =========================================================

def save_gmail_credentials(
    user_id,
    credentials
):

    tokens = load_json_file(TOKEN_FILE)

    tokens[user_id] = {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "scopes": credentials.scopes,
        "email": getattr(credentials, "_gmail_email", None),
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat()
    }

    save_json_file(
        TOKEN_FILE,
        tokens
    )


def get_gmail_credentials_data(user_id):

    tokens = load_json_file(TOKEN_FILE)

    return tokens.get(user_id)


# =========================================================
# OAUTH START
# =========================================================

def get_google_authorization_url(user_id):

    state = create_oauth_state(user_id)

    flow = create_google_flow(
        state=state
    )

    authorization_url, generated_state = (
        flow.authorization_url(
            access_type="offline",
            include_granted_scopes="true",
            prompt="consent",
        )
    )

    # Preserve the PKCE verifier generated by the original
    # OAuth flow so the callback can complete the same flow.
    sessions = load_json_file(SESSION_FILE)

    if state in sessions:
        sessions[state]["code_verifier"] = (
            getattr(flow, "code_verifier", None)
            or getattr(
                getattr(flow, "oauth2session", None),
                "code_verifier",
                None
            )
        )
        save_json_file(
            SESSION_FILE,
            sessions
        )

    return authorization_url


# =========================================================
# OAUTH CALLBACK
# =========================================================

def complete_google_oauth(
    authorization_response
):

    from urllib.parse import parse_qs, urlparse

    parsed = urlparse(
        authorization_response
    )

    query = parse_qs(
        parsed.query
    )

    state_values = query.get(
        "state",
        []
    )

    state = (
        state_values[0]
        if state_values
        else None
    )

    session = get_oauth_state(
        state
    )

    if not session:
        return {
            "success": False,
            "error": (
                "OAuth state is missing, "
                "invalid, or already used."
            )
        }

    error_values = query.get(
        "error",
        []
    )

    if error_values:
        return {
            "success": False,
            "error": error_values[0]
        }

    user_id = session.get(
        "user_id"
    )

    if not user_id:
        return {
            "success": False,
            "error": "OAuth user session is invalid."
        }

    try:

        flow = create_google_flow(
            state=state
        )

        # Restore the PKCE verifier created during OAuth start.
        code_verifier = session.get(
            "code_verifier"
        )

        if code_verifier:
            flow.code_verifier = code_verifier

            if hasattr(flow, "oauth2session"):
                flow.oauth2session.code_verifier = (
                    code_verifier
                )

        flow.fetch_token(
            authorization_response=(
                authorization_response
            )
        )

        credentials = flow.credentials

        gmail_service = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False
        )

        profile = gmail_service.users().getProfile(
            userId="me"
        ).execute()

        credentials._gmail_email = profile.get("emailAddress")

        save_gmail_credentials(
            user_id,
            credentials
        )

        # OAuth state is one-time-use only.
        # Consume it only after successful token exchange
        # and Gmail credential storage.
        consume_oauth_state(state)

        return {
            "success": True,
            "user_id": user_id,
            "token_received": bool(
                credentials.token
            ),
            "refresh_token_received": bool(
                credentials.refresh_token
            ),
            "scope": credentials.scopes
        }

    except Exception as error:

        return {
            "success": False,
            "error": (
                "Failed to complete "
                "Google OAuth."
            ),
            "details": str(error)
        }


# =========================================================
# ROUTES
# =========================================================

@router.get("/oauth/start")
def gmail_oauth_start(
    token: str
):

    # MUKA authentication is deliberately imported
    # here so the existing auth system remains untouched.
    from auth_session import get_session_user

    user_id = get_session_user(
        token
    )

    if not user_id:
        return JSONResponse(
            {
                "success": False,
                "error": (
                    "Invalid or expired "
                    "MUKA session."
                )
            },
            status_code=401
        )

    try:

        authorization_url = (
            get_google_authorization_url(
                user_id
            )
        )

        return RedirectResponse(
            authorization_url
        )

    except Exception as error:

        return JSONResponse(
            {
                "success": False,
                "error": str(error)
            },
            status_code=500
        )


@router.get("/oauth/callback")
def gmail_oauth_callback(
    request: Request,
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
                "error": (
                    "OAuth callback is missing "
                    "required parameters."
                )
            },
            status_code=400
        )

    # Pass the actual callback URL received by FastAPI
    # to Google's OAuth library.
    authorization_response = str(request.url)

    result = complete_google_oauth(
        authorization_response
    )

    if not result.get("success"):
        return JSONResponse(
            result,
            status_code=400
        )

    return JSONResponse(
        {
            "success": True,
            "message": (
                "Google Gmail connected "
                "successfully."
            ),
            "gmail_connected": True,
            "scope": result.get("scope")
        }
    )
