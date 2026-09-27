import json
import os
import secrets
from datetime import datetime, timezone


# =========================================================
# PERSISTENT AUTH SESSIONS
# =========================================================

SESSION_FILE = "auth_sessions.json"


# =========================================================
# LOAD SESSIONS
# =========================================================

def load_sessions():

    if not os.path.exists(SESSION_FILE):
        return {}

    try:

        with open(
            SESSION_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        if isinstance(data, dict):
            return data

    except Exception as error:

        print(
            "AUTH SESSION READ ERROR:",
            type(error).__name__,
            str(error)
        )

    return {}


# =========================================================
# SAVE SESSIONS
# =========================================================

def save_sessions(sessions):

    with open(
        SESSION_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            sessions,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# CREATE SESSION
# =========================================================

def create_session(user):

    token = secrets.token_urlsafe(32)

    sessions = load_sessions()

    sessions[token] = {
        "user_id": user["user_id"],
        "created_at": datetime.now(
            timezone.utc
        ).isoformat()
    }

    save_sessions(sessions)

    return token


# =========================================================
# GET USER FROM SESSION
# =========================================================

def get_session_user(token):

    if not token:
        return None

    sessions = load_sessions()

    session = sessions.get(token)

    if not session:
        return None

    return session.get("user_id")


# =========================================================
# DELETE SESSION
# =========================================================

def delete_session(token):

    sessions = load_sessions()

    if token in sessions:

        del sessions[token]

        save_sessions(sessions)

        return True

    return False