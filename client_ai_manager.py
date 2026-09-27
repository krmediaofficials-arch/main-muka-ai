import json
import os


# =========================================================
# FILE
# =========================================================

FILE = "client_ai_config.json"


# =========================================================
# LOAD DATA
# =========================================================

def load_data():

    if not os.path.exists(FILE):

        return {}

    try:

        with open(
            FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, dict):

            return {}

        # Support the existing Client AI config format:
        # {
        #     "project_id": {
        #         ...
        #     }
        # }

        return data

    except Exception as error:

        print(
            "CLIENT AI CONFIG READ ERROR:",
            type(error).__name__,
            str(error)
        )

        return {}

# =========================================================
# SAVE DATA
# =========================================================

def save_data(data):

    with open(
        FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# CREATE CLIENT AI
# =========================================================

def create_client_ai(
    project_id,
    name,
    client_name
):

    data = load_data()

    if project_id in data["client_ais"]:

        return {
            "success": False,
            "message": "Client AI already exists"
        }


    client_ai = {

        "project_id":
            project_id,

        "name":
            name,

        "client_name":
            client_name,

        "status":
            "active",

        "business": {

            "website":
                "",

            "description":
                "",

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
            []
    }


    data["client_ais"][project_id] = client_ai

    save_data(data)


    return {

        "success":
            True,

        "message":
            "Client AI created successfully",

        "client_ai":
            client_ai
    }

# =========================================================
# GET CLIENT AI
# =========================================================

def get_client_ai(
    project_id
):

    data = load_data()

    client_ais = data.get(
        "client_ais",
        {}
    )

    if project_id not in client_ais:

        return {
            "success":
                False,

            "message":
                "Client AI not found"
        }

    return {
        "success":
            True,

        "client_ai":
            client_ais[project_id]
    }




# =========================================================
# GET ALL CLIENT AIs
# =========================================================

def get_all_client_ais():

    data = load_data()

    return {

        "success":
            True,

        "client_ais":
            data["client_ais"],

        "count":
            len(data["client_ais"])
    }


# =========================================================
# UPDATE CLIENT AI
# =========================================================

def update_client_ai(
    project_id,
    updates
):

    data = load_data()

    if project_id not in data["client_ais"]:

        return {

            "success":
                False,

            "message":
                "Client AI not found"
        }


    client_ai = data["client_ais"][project_id]


    if not isinstance(
        updates,
        dict
    ):

        return {

            "success":
                False,

            "message":
                "Updates must be an object."
        }


    for key, value in updates.items():

        if key in [
            "project_id"
        ]:

            continue

        client_ai[key] = value


    data["client_ais"][project_id] = client_ai

    save_data(data)


    return {

        "success":
            True,

        "message":
            "Client AI updated successfully",

        "client_ai":
            client_ai
    }


# =========================================================
# ADD FAQ
# =========================================================

def add_client_ai_faq(
    project_id,
    question,
    answer
):

    data = load_data()

    if project_id not in data["client_ais"]:

        return {

            "success":
                False,

            "message":
                "Client AI not found"
        }


    client_ai = data["client_ais"][project_id]

    if "faqs" not in client_ai:

        client_ai["faqs"] = []


    faq = {

        "question":
            question,

        "answer":
            answer
    }


    client_ai["faqs"].append(
        faq
    )

    save_data(data)


    return {

        "success":
            True,

        "message":
            "FAQ added successfully",

        "project_id":
            project_id,

        "faq":
            faq
    }


# =========================================================
# ADD KNOWLEDGE
# =========================================================

def add_client_ai_knowledge(
    project_id,
    title,
    content
):

    data = load_data()

    if project_id not in data["client_ais"]:

        return {

            "success":
                False,

            "message":
                "Client AI not found"
        }


    client_ai = data["client_ais"][project_id]

    if "knowledge" not in client_ai:

        client_ai["knowledge"] = []


    item = {

        "title":
            title,

        "content":
            content
    }


    client_ai["knowledge"].append(
        item
    )

    save_data(data)


    return {

        "success":
            True,

        "message":
            "Knowledge added successfully",

        "project_id":
            project_id,

        "knowledge":
            item
    }