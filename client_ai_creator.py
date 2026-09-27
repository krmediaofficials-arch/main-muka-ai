import json
import os
import re
import uuid
from datetime import datetime, timezone


# =========================================================
# CLIENT AI CREATOR
# =========================================================

CLIENT_AI_CONFIG_FILE = "client_ai_config.json"
PROJECT_MEMORY_FILE = "project_memory.json"


# =========================================================
# JSON HELPERS
# =========================================================

def load_json(filename, default):

    if not os.path.exists(filename):
        return default

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        return data

    except Exception as error:

        print(
            f"CLIENT AI JSON READ ERROR [{filename}]:",
            type(error).__name__,
            str(error)
        )

        return default


def save_json(filename, data):

    with open(
        filename,
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
# ID HELPERS
# =========================================================

def make_project_id(client_name):

    slug = re.sub(
        r"[^a-z0-9]+",
        "_",
        client_name.lower()
    ).strip("_")

    if not slug:
        slug = "client"

    return (
        f"{slug}_client_ai_"
        f"{uuid.uuid4().hex[:8]}"
    )


# =========================================================
# CLIENT AI CONFIG
# =========================================================

def load_client_ai_configs():

    data = load_json(
        CLIENT_AI_CONFIG_FILE,
        {}
    )

    if not isinstance(data, dict):
        return {}

    client_ais = data.get(
        "client_ais"
    )

    if isinstance(client_ais, dict):
        return client_ais

    return data

def save_client_ai_configs(configs):

    if not isinstance(configs, dict):
        configs = {}

    save_json(
        CLIENT_AI_CONFIG_FILE,
        {
            "client_ais": configs
        }
    )

# =========================================================
# CLIENT AI TRASH
# =========================================================

CLIENT_AI_TRASH_FILE = "client_ai_trash.json"


def load_client_ai_trash():

    data = load_json(
        CLIENT_AI_TRASH_FILE,
        {}
    )

    if not isinstance(data, dict):
        return {}

    trash = data.get("trash")

    if isinstance(trash, dict):
        return trash

    return data


def save_client_ai_trash(trash):

    if not isinstance(trash, dict):
        trash = {}

    save_json(
        CLIENT_AI_TRASH_FILE,
        {
            "trash": trash
        }
    )

# =========================================================
# CREATE CLIENT AI
# =========================================================

def create_client_ai(
    client_name,
    website="",
    description="",
    created_by="",
    workspace_id="kr_media_workspace"
):

    client_name = client_name.strip()
    website = website.strip()
    description = description.strip()
    created_by = created_by.strip()
    workspace_id = workspace_id.strip()

    if not client_name:
        return {
            "success": False,
            "message": "Client name is required."
        }

    project_id = make_project_id(
        client_name
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    client_ai = {

        "project_id":
            project_id,

        "name":
            f"{client_name} Client AI",

        "client_name":
            client_name,

        "status":
            "active",

        "business": {

            "website":
                website,

            "description":
                description,

            "products":
                [],

            "services":
                []
        },

        "personality": {

            "tone":
                "friendly",

            "style":
                "helpful sales assistant",

            "language":
                "match_customer"
        },

        "rules": {

            "client_focused":
                True,

            "never_mix_clients":
                True,

            "never_invent_information":
                True,

            "never_guess_price":
                True,

            "never_make_unverified_health_claims":
                True
        },

        "faqs":
            [],

        "knowledge":
            [],

        "conversation_flow":
            [
                "Greet the customer warmly",
                "Understand the customer's requirement",
                "Answer using verified current-client information",
                "If information is unavailable, clearly say so",
                "Never invent client-specific information",
                "Never mix information from another Client AI"
            ],

        "workspace_id":
            workspace_id,

        "created_by":
            created_by,

        "created_at":
            now,

        "updated_at":
            now,

        "website":
            website
    }

    configs = load_client_ai_configs()

    if project_id in configs:

        return {
            "success": False,
            "message": "Client AI ID already exists."
        }

    configs[project_id] = client_ai

    save_json(
        CLIENT_AI_CONFIG_FILE,
        {
            "client_ais": configs
        }
    )

    return {

        "success":
            True,

        "message":
            "Client AI created successfully.",

        "client_ai":
            client_ai
    }

    client_name = client_name.strip()
    website = website.strip()
    description = description.strip()
    created_by = created_by.strip()
    workspace_id = workspace_id.strip()

    if not client_name:

        return {
            "success": False,
            "message": "Client name is required."
        }

    project_id = make_project_id(
        client_name
    )

    now = datetime.now(
        timezone.utc
    ).isoformat()

    client_ai = {

        "project_id": project_id,

        "client_name": client_name,

        "website": website,

        "description": description,

        "workspace_id": workspace_id,

        "created_by": created_by,

        "status": "active",

        "created_at": now,

        "updated_at": now
    }

    configs = load_client_ai_configs()

    if project_id in configs:

        return {
            "success": False,
            "message": "Client AI ID already exists."
        }

    configs[project_id] = client_ai

    save_client_ai_configs(
        configs
    )

    return {

        "success": True,

        "message": "Client AI created successfully.",

        "client_ai": client_ai
    }


# =========================================================
# GET CLIENT AI
# =========================================================

def get_client_ai(project_id):

    configs = load_client_ai_configs()

    return configs.get(
        project_id
    )


# =========================================================
# LIST CLIENT AIs
# =========================================================

def list_client_ais(
    workspace_id=None
):

    configs = load_client_ai_configs()

    results = []

    for client_ai in configs.values():

        if workspace_id:

            if client_ai.get(
                "workspace_id"
            ) != workspace_id:

                continue

        results.append(
            client_ai
        )

    results.sort(
        key=lambda item:
        item.get(
            "created_at",
            ""
        ),
        reverse=True
    )

    return results