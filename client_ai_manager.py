import json
import os

FILE = "client_ai_config.json"


def load_data():
    if not os.path.exists(FILE):
        return {"client_ais": {}}

    with open(FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def create_client_ai(project_id, name, client_name):
    data = load_data()

    if project_id in data["client_ais"]:
        return {
            "success": False,
            "message": "Client AI already exists"
        }

    client_ai = {
        "project_id": project_id,
        "name": name,
        "client_name": client_name,
        "status": "active",
        "business": {
            "website": "",
            "description": "",
            "products": [],
            "services": []
        },
        "personality": {
            "tone": "friendly",
            "style": "helpful sales assistant"
        },
        "rules": {
            "client_focused": True,
            "never_mix_clients": True,
            "never_invent_information": True
        },
        "faqs": [],
        "knowledge": []
    }

    data["client_ais"][project_id] = client_ai

    save_data(data)

    return {
        "success": True,
        "message": "Client AI created successfully",
        "client_ai": client_ai
    }


def get_client_ai(project_id):
    data = load_data()

    if project_id not in data["client_ais"]:
        return {
            "success": False,
            "message": "Client AI not found"
        }

    return {
        "success": True,
        "client_ai": data["client_ais"][project_id]
    }


def get_all_client_ais():
    data = load_data()

    return {
        "success": True,
        "client_ais": data["client_ais"],
        "count": len(data["client_ais"])
    }