import json
import os
import uuid
from datetime import datetime


MEMORY_FILE = "main_muka_long_term_memory.json"
PENDING_FILE = "main_muka_pending_memory.json"
MEMORY_CATEGORIES = {
    "identity",
    "preference",
    "project",
    "business",
    "technical",
    "instruction",
    "general"
}

MEMORY_IMPORTANCE_LEVELS = {
    "low",
    "medium",
    "high",
    "critical"
}

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
            f"MEMORY JSON ERROR [{filename}]:",
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
# LONG TERM MEMORY
# =========================================================

def load_memories(user_id):

    data = load_json(
        MEMORY_FILE,
        {}
    )

    if not isinstance(data, dict):
        return []

    memories = data.get(
        user_id,
        []
    )

    if not isinstance(memories, list):
        return []

    return memories
def normalize_memory(memory):

    if not isinstance(memory, dict):
        return {
            "memory": str(memory),
            "category": "general",
            "importance": "medium"
        }

    normalized = dict(memory)

    category = normalized.get(
        "category",
        "general"
    )

    importance = normalized.get(
        "importance",
        "medium"
    )

    if category not in MEMORY_CATEGORIES:
        category = "general"

    if importance not in MEMORY_IMPORTANCE_LEVELS:
        importance = "medium"

    normalized["category"] = category
    normalized["importance"] = importance

    return normalized

def save_memories(user_id, memories):

    data = load_json(
        MEMORY_FILE,
        {}
    )

    if not isinstance(data, dict):
        data = {}

    data[user_id] = memories

    save_json(
        MEMORY_FILE,
        data
    )


def memory_exists(user_id, memory):

    memory_normalized = (
        memory.strip().lower()
    )

    for item in load_memories(user_id):

        if isinstance(item, dict):

            existing = str(
                item.get(
                    "memory",
                    ""
                )
            )

        else:

            existing = str(item)

        if (
            existing.strip().lower()
            == memory_normalized
        ):

            return True

    return False


def sort_memories_by_importance(memories):

    priority = {
        "critical": 4,
        "high": 3,
        "medium": 2,
        "low": 1
    }

    return sorted(
        memories,
        key=lambda item: priority.get(
            str(
                item.get(
                    "importance",
                    "medium"
                )
            ).lower(),
            2
        ),
        reverse=True
    )
def add_memory(
    user_id,
    memory,
    category="general",
    source="conversation",
    importance="medium"
):
    memory = memory.strip()

    if not memory:
        return False
    if category not in MEMORY_CATEGORIES:
        category = "general"

    if importance not in MEMORY_IMPORTANCE_LEVELS:
        importance = "medium"
    if memory_exists(
        user_id,
        memory
    ):
        return False

    memories = load_memories(
        user_id
    )

    memories.append({

        "id":
            str(uuid.uuid4()),

        "memory":
            memory,

        "category":
            category,
"importance":
    importance,

        "source":
            source,

        "created_at":
            datetime.now().isoformat(),

        "updated_at":
            datetime.now().isoformat()
    })

    memories = memories[-500:]

    save_memories(
        user_id,
        memories
    )

    return True

def forget_memory(user_id, memory_id):
    memories = load_memories(user_id)

    updated_memories = [
        memory
        for memory in memories
        if str(memory.get("id", "")) != str(memory_id)
    ]

    if len(updated_memories) == len(memories):
        return False

    save_memories(
        user_id,
        updated_memories
    )

    return True
# =========================================================
# PENDING MEMORY
# =========================================================

def load_pending():

    data = load_json(
        PENDING_FILE,
        {}
    )

    if not isinstance(data, dict):
        return {}

    return data


def save_pending(data):

    save_json(
        PENDING_FILE,
        data
    )


def get_pending_memory(user_id):

    data = load_pending()

    pending = data.get(
        user_id
    )

    if not isinstance(
        pending,
        dict
    ):
        return None

    return pending


def set_pending_memory(
    user_id,
    memory,
    category="general"
):

    data = load_pending()

    data[user_id] = {

        "memory":
            memory.strip(),

        "category":
            category,

        "created_at":
            datetime.now().isoformat()
    }

    save_pending(
        data
    )


def clear_pending_memory(user_id):

    data = load_pending()

    data.pop(
        user_id,
        None
    )

    save_pending(
        data
    )


def confirm_pending_memory(user_id):

    pending = get_pending_memory(
        user_id
    )

    if not pending:
        return False, None

    memory = pending.get(
        "memory",
        ""
    )

    category = pending.get(
        "category",
        "general"
    )

    saved = add_memory(
        user_id,
        memory,
        category=category,
        source="user_confirmation"
    )

    clear_pending_memory(
        user_id
    )

    return saved, memory


# =========================================================
# USER CONFIRMATION DETECTION
# =========================================================

def is_memory_confirmation(message):

    text = (
        message
        .strip()
        .lower()
    )

    confirmations = {
        "yes",
        "yes please",
        "yeah",
        "yep",
        "haan",
        "ha",
        "han",
        "haan save karo",
        "ha save karo",
        "save karo",
        "save kar do",
        "yaad rakh",
        "yaad rakhna",
        "remember it",
        "remember this",
        "remember that",
        "save it",
        "please save it"
    }

    if text in confirmations:
        return True

    confirmation_endings = (
        "yes",
        "yes please",
        "yeah",
        "yep",
        "haan",
        "ha",
        "han",
        "haan save karo",
        "ha save karo",
        "save karo",
        "save kar do",
        "yaad rakh",
        "yaad rakhna",
        "remember it",
        "remember this",
        "remember that",
        "save it",
        "please save it"
    )

    return any(
        text.endswith(" " + ending)
        for ending in confirmation_endings
    )
def is_memory_forget_request(message):

    text = (
        message
        .strip()
        .lower()
    )

    forget_phrases = (
        "forget this",
        "forget that",
        "forget it",
        "forget this memory",
        "forget that memory",
        "forget my memory",
        "forget my name",
        "mera naam bhool jao",
        "mera name bhool jao",
        "mera naam bhul jao",
        "ye baat bhool jao",
        "yeh baat bhool jao",
        "is memory ko bhool jao",
        "memory bhool jao",
        "memory delete karo",
        "memory delete kar do",
        "ise bhool jao",
        "isko bhool jao"
    )

    return any(
        phrase in text
        for phrase in forget_phrases
    )

def extract_memory_forget_target(message):

    text = (
        message
        .strip()
        .lower()
    )

    prefixes = (
        "forget this",
        "forget that",
        "forget it",
        "forget this memory",
        "forget that memory",
        "forget my memory",
        "forget my name",
        "mera naam bhool jao",
        "mera naam bhul jao",
        "ye baat bhool jao",
        "yeh baat bhool jao",
        "is memory ko bhool jao",
        "memory bhool jao",
        "memory delete karo",
        "memory delete kar do",
        "ise bhool jao",
        "isko bhool jao"
    )

    for phrase in prefixes:

        if phrase in text:

            target = text.replace(
                phrase,
                ""
            ).strip()

            return target
    if text in (
        "mera naam bhool jao",
        "mera name bhool jao"
    ):
        return "rithik"

    return ""
def find_memory_by_text(user_id, search_text):

    search_text = (
        search_text
        .strip()
        .lower()
    )

    if not search_text:
        return None

    memories = load_memories(user_id)

    for item in memories:

        if not isinstance(item, dict):
            continue

        memory = str(
            item.get("memory", "")
        ).strip()

        if search_text in memory.lower():
            return item

    return None


def is_memory_rejection(message):

    text = (
        message
        .strip()
        .lower()
    )

    rejections = {

        "no",
        "nope",
        "nahi",
        "nahin",
        "mat save karo",
        "save mat karo",
        "don't save",
        "do not save",
        "forget it",
        "leave it"
    }

    return text in rejections