import json
import os
import uuid
from datetime import datetime, timezone

import bcrypt


ACCOUNTS_FILE = "accounts.json"


# =========================================================
# JSON HELPERS
# =========================================================

def load_accounts():
    if not os.path.exists(ACCOUNTS_FILE):
        return {
            "users": {}
        }

    try:
        with open(
            ACCOUNTS_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        if not isinstance(data, dict):
            return {"users": {}}

        if not isinstance(data.get("users"), dict):
            data["users"] = {}

        return data

    except Exception as error:
        print(
            "ACCOUNTS JSON ERROR:",
            type(error).__name__,
            str(error)
        )
        return {
            "users": {}
        }


def save_accounts(data):
    with open(
        ACCOUNTS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# PASSWORD
# =========================================================

def hash_password(password):
    if not isinstance(password, str) or not password:
        raise ValueError("Password cannot be empty.")

    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")


def verify_password(password, password_hash):
    if not password or not password_hash:
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception:
        return False


# =========================================================
# USER HELPERS
# =========================================================

def find_user_by_email(email):
    email = email.strip().lower()

    data = load_accounts()

    for user in data["users"].values():

        if user.get("email", "").lower() == email:
            return user

    return None


def get_user(user_id):
    data = load_accounts()

    return data["users"].get(user_id)


# =========================================================
# CREATE USER
# =========================================================

def create_user(
    name,
    email,
    password,
    role="member",
    workspace_id="kr_media_workspace"
):

    name = name.strip()
    email = email.strip().lower()

    if not name:
        return {
            "success": False,
            "message": "Name is required."
        }

    if not email:
        return {
            "success": False,
            "message": "Email is required."
        }

    if not password:
        return {
            "success": False,
            "message": "Password is required."
        }

    if len(password) < 8:
        return {
            "success": False,
            "message": "Password must be at least 8 characters."
        }

    if find_user_by_email(email):
        return {
            "success": False,
            "message": "An account with this email already exists."
        }

    user_id = "user_" + uuid.uuid4().hex[:12]

    now = datetime.now(
        timezone.utc
    ).isoformat()

    user = {
        "user_id": user_id,
        "name": name,
        "email": email,
        "password_hash": hash_password(password),
        "role": role,
        "workspace_id": workspace_id,
        "status": "active",
        "created_at": now,
        "last_login": None
    }

    data = load_accounts()

    data["users"][user_id] = user

    save_accounts(data)

    return {
        "success": True,
        "message": "Account created successfully.",
        "user": public_user(user)
    }


# =========================================================
# LOGIN
# =========================================================

def authenticate_user(email, password):

    user = find_user_by_email(email)

    if not user:
        return {
            "success": False,
            "message": "Invalid email or password."
        }

    if user.get("status") != "active":
        return {
            "success": False,
            "message": "This account is not active."
        }

    if not verify_password(
        password,
        user.get("password_hash", "")
    ):
        return {
            "success": False,
            "message": "Invalid email or password."
        }

    data = load_accounts()

    user_id = user["user_id"]

    data["users"][user_id]["last_login"] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    save_accounts(data)

    updated_user = data["users"][user_id]

    return {
        "success": True,
        "message": "Login successful.",
        "user": public_user(updated_user)
    }


# =========================================================
# PUBLIC USER DATA
# =========================================================

def public_user(user):

    return {
        "user_id": user.get("user_id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "workspace_id": user.get("workspace_id"),
        "status": user.get("status"),
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login")
    }


# =========================================================
# OWNER
# =========================================================

def ensure_owner_account():

    data = load_accounts()

    for user in data["users"].values():

        if user.get("role") == "owner":
            return {
                "success": True,
                "created": False,
                "user": public_user(user)
            }

    return {
        "success": True,
        "created": False,
        "message": (
            "No owner account exists yet. "
            "Create the owner through the setup flow."
        )
    }
# =========================================================
# ROLE & PERMISSIONS
# =========================================================

ROLE_PERMISSIONS = {

    "owner": {
        "manage_team",
        "manage_accounts",
        "manage_projects",
        "create_client_ai",
        "manage_client_ai",
        "view_all_activity",
        "manage_workspace",
        "use_main_muka"
    },

    "admin": {
        "manage_team",
        "manage_projects",
        "create_client_ai",
        "manage_client_ai",
        "view_all_activity",
        "use_main_muka"
    },

    "developer": {
        "manage_projects",
        "create_client_ai",
        "manage_client_ai",
        "use_main_muka"
    },

    "marketer": {
        "manage_projects",
        "use_main_muka"
    },

    "member": {
        "use_main_muka"
    }
}


def has_permission(user, permission):

    if not user:
        return False

    role = user.get(
        "role",
        "member"
    )

    permissions = ROLE_PERMISSIONS.get(
        role,
        ROLE_PERMISSIONS["member"]
    )

    return permission in permissions


def get_user_permissions(user):

    if not user:
        return []

    role = user.get(
        "role",
        "member"
    )

    return sorted(
        ROLE_PERMISSIONS.get(
            role,
            ROLE_PERMISSIONS["member"]
        )
    )


def can_manage_team(user):

    return has_permission(
        user,
        "manage_team"
    )


def can_create_client_ai(user):

    return has_permission(
        user,
        "create_client_ai"
    )


def can_manage_client_ai(user):

    return has_permission(
        user,
        "manage_client_ai"
    )


def can_view_all_activity(user):

    return has_permission(
        user,
        "view_all_activity"
    )
# =========================================================
# SET USER ROLE
# =========================================================

def set_user_role(user_id, role):

    allowed_roles = {
        "owner",
        "admin",
        "developer",
        "marketer",
        "member"
    }

    if role not in allowed_roles:
        return {
            "success": False,
            "message": "Invalid role."
        }

    data = load_accounts()

    user = data["users"].get(user_id)

    if not user:
        return {
            "success": False,
            "message": "User not found."
        }

    if role == "owner":

        for existing_user in data["users"].values():

            if (
                existing_user.get("role") == "owner"
                and existing_user.get("user_id") != user_id
            ):
                return {
                    "success": False,
                    "message": "An owner account already exists."
                }

    user["role"] = role

    data["users"][user_id] = user

    save_accounts(data)

    return {
        "success": True,
        "message": "User role updated successfully.",
        "user": public_user(user)
    }