from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime
import os
import json
import uuid
import re


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY not found. Please check your .env file."
    )

client = OpenAI(api_key=API_KEY)


# =========================================================
# CLIENT AI CONNECTION
# =========================================================

try:
    from chat_api import chat_with_client_ai
except Exception as error:
    chat_with_client_ai = None
    print("CLIENT AI IMPORT ERROR:", error)


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="MUKA AI - Main Brain",
    version="2.2.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# FILES
# =========================================================

CONVERSATION_FILE = "main_muka_memory.json"
LONG_TERM_MEMORY_FILE = "main_muka_long_term_memory.json"
PROJECT_MEMORY_FILE = "project_memory.json"


# =========================================================
# MAIN MUKA SYSTEM
# =========================================================

MAIN_MUKA_SYSTEM = """
You are MUKA AI, the central AI brain of KR Media.

You are the MAIN MUKA AI.

You are NOT a client-specific sales chatbot.

Your job is to help the owner/team of KR Media with:

- Coding
- Debugging
- Websites
- Web applications
- AI systems
- Client AI systems
- Business planning
- Marketing
- Automation
- Research
- Software projects
- Project planning
- Technical troubleshooting
- Future AI projects

=========================================================
MAIN ARCHITECTURE
=========================================================

MAIN MUKA AI
    |
    |-- Client AI 1
    |-- Client AI 2
    |-- Client AI 3
    |-- Future Projects
    |-- Coding
    |-- Research
    |-- Automation

MAIN MUKA is the central brain.

Client AIs are separate assistants.

Client AIs must focus only on their assigned client's
website, products, services and business.

Never mix client information between projects.


=========================================================
CLIENT AI
=========================================================

You have access to Client AI systems through the
send_message_to_client_ai tool.

When the owner asks you to:

- talk to a Client AI
- ask a Client AI something
- test a Client AI
- send a message to a Client AI
- get a response from a Client AI
- check how a Client AI responds
- ask the client chatbot a question
- test a client's chatbot

you MUST use the send_message_to_client_ai tool.

For Roots & Leaves Collection, use:

project_id:
roots_leaves_client_ai

Do not pretend that you contacted a Client AI.

Only say that a Client AI was contacted when the tool
actually returns a successful result.

When the Client AI returns a response, show the response
naturally to the owner and make it clear that it came
from the Client AI.

Never mix one client's information with another client's
information.


=========================================================
PROJECT MEMORY
=========================================================

Project memory is persistent structured information.

Projects can contain:

- name
- type
- client
- status
- goal
- decisions
- tasks
- notes

When the owner explicitly asks you to:

- create a project
- make a project
- add a project
- update a project
- change a project
- add a decision
- add a task
- add a note
- change project status
- change project goal

use the appropriate project-memory tool.

Do NOT merely tell the owner that you saved something.

Actually use the tool.

After the tool successfully completes, tell the owner what
was actually saved or changed.

Never claim that a project-memory change happened unless
the tool confirms it.


=========================================================
LONG-TERM MEMORY
=========================================================

If the owner explicitly says:

- yaad rakhna
- yaad rakh
- isko yaad rakh
- memory mein save karo
- memory me save karo
- remember this
- remember that
- future mein yaad rakhna
- save this
- save that

the application may save the information as long-term memory.

Do not claim permanent memory was saved unless the application
confirms it.


=========================================================
CODING
=========================================================

When working with code:

- Understand the existing structure.
- Preserve working functionality.
- Avoid unnecessary changes.
- If asked for complete code, provide complete relevant code.
- If asked for a small fix, prefer a targeted fix.

The owner uses Windows PowerShell and VS Code.

Give Windows-friendly instructions.


=========================================================
LANGUAGE
=========================================================

If the owner speaks Hindi/Hinglish, reply naturally in
Hindi/Hinglish.

If the owner speaks English, reply in English.


=========================================================
HONESTY
=========================================================

Never claim that you:

- opened a website
- changed a file
- installed software
- accessed an account
- deployed something
- sent something
- saved project information

unless the corresponding action was actually performed.


=========================================================
MAIN PURPOSE
=========================================================

You are the central AI brain of KR Media.

Think broadly.

Help the owner build, manage, debug and improve future
software, AI and business projects.
"""


# =========================================================
# REQUEST MODELS
# =========================================================

class ChatRequest(BaseModel):
    message: str
    user_id: str = "main_user"


class ClientChatRequest(BaseModel):
    message: str
    project_id: str = "roots_leaves_client_ai"


# =========================================================
# JSON HELPERS
# =========================================================

def load_json_file(filename, default):

    if not os.path.exists(filename):
        return default

    try:

        with open(
            filename,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except Exception as error:

        print(
            f"JSON READ ERROR [{filename}]:",
            type(error).__name__,
            str(error)
        )

        return default


def save_json_file(filename, data):

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
# CONVERSATION MEMORY
# =========================================================

def load_conversation(user_id):

    data = load_json_file(
        CONVERSATION_FILE,
        {}
    )

    if not isinstance(data, dict):
        return []

    history = data.get(
        user_id,
        []
    )

    if not isinstance(history, list):
        return []

    return history


def save_conversation(user_id, history):

    data = load_json_file(
        CONVERSATION_FILE,
        {}
    )

    if not isinstance(data, dict):
        data = {}

    data[user_id] = history

    save_json_file(
        CONVERSATION_FILE,
        data
    )


# =========================================================
# LONG-TERM MEMORY
# =========================================================

def load_long_term_memory(user_id):

    data = load_json_file(
        LONG_TERM_MEMORY_FILE,
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


def save_long_term_memory(user_id, memories):

    data = load_json_file(
        LONG_TERM_MEMORY_FILE,
        {}
    )

    if not isinstance(data, dict):
        data = {}

    data[user_id] = memories

    save_json_file(
        LONG_TERM_MEMORY_FILE,
        data
    )


def extract_explicit_memory(message):

    text = message.strip()
    lower = text.lower()

    triggers = [
        "yaad rakhna",
        "yaad rakh",
        "isko yaad rakh",
        "isey yaad rakh",
        "memory mein save karo",
        "memory me save karo",
        "memory mein save kar",
        "memory me save kar",
        "remember this",
        "remember that",
        "remember",
        "future mein yaad rakhna",
        "future me yaad rakhna",
        "save this",
        "save that"
    ]

    matched = None

    for trigger in triggers:

        if trigger in lower:

            matched = trigger
            break

    if not matched:
        return None

    memory = re.sub(
        re.escape(matched),
        "",
        text,
        count=1,
        flags=re.IGNORECASE
    ).strip()

    memory = memory.lstrip(
        " :-,.\n"
    )

    if not memory:
        return None

    return memory


def add_long_term_memory(user_id, memory):

    memories = load_long_term_memory(
        user_id
    )

    for item in memories:

        if isinstance(item, dict):

            existing = item.get(
                "memory",
                ""
            )

        else:

            existing = str(item)

        if existing.strip().lower() == memory.strip().lower():

            return False

    memories.append({

        "id":
            str(uuid.uuid4()),

        "memory":
            memory,

        "created_at":
            datetime.now().isoformat()
    })

    memories = memories[-500:]

    save_long_term_memory(
        user_id,
        memories
    )

    return True


# =========================================================
# PROJECT MEMORY
# =========================================================

def load_project_memory():

    data = load_json_file(
        PROJECT_MEMORY_FILE,
        {}
    )

    if not isinstance(data, dict):
        data = {}

    if not isinstance(
        data.get("projects"),
        dict
    ):

        data["projects"] = {}

    return data


def save_project_memory(data):

    save_json_file(
        PROJECT_MEMORY_FILE,
        data
    )


def get_projects():

    data = load_project_memory()

    return data["projects"]


def get_project(project_id):

    projects = get_projects()

    return projects.get(
        project_id
    )


# =========================================================
# CREATE PROJECT
# =========================================================

def create_project(
    project_id,
    name,
    project_type="project",
    client="",
    status="active",
    goal=""
):

    data = load_project_memory()

    projects = data["projects"]

    if project_id in projects:

        return {
            "success": False,
            "message": "Project already exists.",
            "project": projects[project_id]
        }

    project = {

        "name":
            name,

        "type":
            project_type,

        "client":
            client,

        "status":
            status,

        "goal":
            goal,

        "decisions":
            [],

        "tasks":
            [],

        "notes":
            []
    }

    projects[project_id] = project

    save_project_memory(
        data
    )

    return {

        "success":
            True,

        "message":
            "Project created successfully.",

        "project_id":
            project_id,

        "project":
            project
    }


# =========================================================
# UPDATE PROJECT
# =========================================================

def update_project(
    project_id,
    name=None,
    project_type=None,
    client=None,
    status=None,
    goal=None
):

    data = load_project_memory()

    projects = data["projects"]

    if project_id not in projects:

        return {

            "success":
                False,

            "message":
                "Project not found."
        }

    project = projects[project_id]

    if name is not None:
        project["name"] = name

    if project_type is not None:
        project["type"] = project_type

    if client is not None:
        project["client"] = client

    if status is not None:
        project["status"] = status

    if goal is not None:
        project["goal"] = goal

    save_project_memory(
        data
    )

    return {

        "success":
            True,

        "message":
            "Project updated successfully.",

        "project_id":
            project_id,

        "project":
            project
    }


# =========================================================
# ADD PROJECT DECISION
# =========================================================

def add_project_decision(
    project_id,
    decision
):

    data = load_project_memory()

    projects = data["projects"]

    if project_id not in projects:

        return {

            "success":
                False,

            "message":
                "Project not found."
        }

    project = projects[project_id]

    if "decisions" not in project:
        project["decisions"] = []

    project["decisions"].append(
        decision
    )

    save_project_memory(
        data
    )

    return {

        "success":
            True,

        "message":
            "Project decision saved.",

        "project_id":
            project_id,

        "decision":
            decision
    }


# =========================================================
# ADD PROJECT TASK
# =========================================================

def add_project_task(
    project_id,
    task
):

    data = load_project_memory()

    projects = data["projects"]

    if project_id not in projects:

        return {

            "success":
                False,

            "message":
                "Project not found."
        }

    project = projects[project_id]

    if "tasks" not in project:
        project["tasks"] = []

    project["tasks"].append(
        task
    )

    save_project_memory(
        data
    )

    return {

        "success":
            True,

        "message":
            "Project task saved.",

        "project_id":
            project_id,

        "task":
            task
    }


# =========================================================
# ADD PROJECT NOTE
# =========================================================

def add_project_note(
    project_id,
    note
):

    data = load_project_memory()

    projects = data["projects"]

    if project_id not in projects:

        return {

            "success":
                False,

            "message":
                "Project not found."
        }

    project = projects[project_id]

    if "notes" not in project:
        project["notes"] = []

    project["notes"].append(
        note
    )

    save_project_memory(
        data
    )

    return {

        "success":
            True,

        "message":
            "Project note saved.",

        "project_id":
            project_id,

        "note":
            note
    }


# =========================================================
# PROJECT CONTEXT
# =========================================================

def get_project_context():

    projects = get_projects()

    if not projects:
        return ""

    text = """

=========================================================
CURRENT PROJECT MEMORY
=========================================================

"""

    for project_id, project in projects.items():

        if not isinstance(project, dict):
            continue

        text += f"""
PROJECT ID: {project_id}
PROJECT NAME: {project.get("name", "")}
TYPE: {project.get("type", "")}
CLIENT: {project.get("client", "")}
STATUS: {project.get("status", "")}
GOAL: {project.get("goal", "")}
"""

        decisions = project.get(
            "decisions",
            []
        )

        if decisions:

            text += "DECISIONS:\n"

            for decision in decisions:

                text += (
                    "- "
                    + str(decision)
                    + "\n"
                )

        tasks = project.get(
            "tasks",
            []
        )

        if tasks:

            text += "TASKS:\n"

            for task in tasks:

                text += (
                    "- "
                    + str(task)
                    + "\n"
                )

        notes = project.get(
            "notes",
            []
        )

        if notes:

            text += "NOTES:\n"

            for note in notes:

                text += (
                    "- "
                    + str(note)
                    + "\n"
                )

        text += "\n"

    text += """

=========================================================
END PROJECT MEMORY
=========================================================

"""

    return text


# =========================================================
# SEND MESSAGE TO CLIENT AI
# =========================================================

def send_message_to_client_ai(
    message,
    project_id="roots_leaves_client_ai"
):

    if not message or not message.strip():

        return {
            "success": False,
            "message": "Client AI message cannot be empty."
        }

    if not project_id or not project_id.strip():

        project_id = "roots_leaves_client_ai"

    if chat_with_client_ai is None:

        return {
            "success": False,
            "message": "Client AI connection is not available."
        }

    try:

        result = chat_with_client_ai(
            message.strip(),
            project_id.strip()
        )

        if not isinstance(result, dict):

            return {
                "success": False,
                "message": "Invalid response received from Client AI."
            }

        return result

    except Exception as error:

        print("")
        print(
            "========================================"
        )
        print(
            "CLIENT AI TOOL ERROR"
        )
        print(
            "========================================"
        )
        print(
            "TYPE:",
            type(error).__name__
        )
        print(
            "ERROR:",
            str(error)
        )
        print(
            "========================================"
        )
        print("")

        return {
            "success": False,
            "message": (
                "Client AI tool error: "
                + str(error)
            )
        }


# =========================================================
# PROJECT AI TOOLS
# =========================================================

PROJECT_TOOLS = [

    {
        "type": "function",
        "name": "create_project",
        "description": (
            "Create a new KR Media project in persistent "
            "project memory."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "project_id": {
                    "type": "string"
                },

                "name": {
                    "type": "string"
                },

                "project_type": {
                    "type": "string"
                },

                "client": {
                    "type": "string"
                },

                "status": {
                    "type": "string"
                },

                "goal": {
                    "type": "string"
                }
            },
            "required": [
                "project_id",
                "name"
            ],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "update_project",
        "description": (
            "Update existing project information."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "project_id": {
                    "type": "string"
                },

                "name": {
                    "type": ["string", "null"]
                },

                "project_type": {
                    "type": ["string", "null"]
                },

                "client": {
                    "type": ["string", "null"]
                },

                "status": {
                    "type": ["string", "null"]
                },

                "goal": {
                    "type": ["string", "null"]
                }
            },
            "required": [
                "project_id"
            ],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "add_project_decision",
        "description": (
            "Save an important decision to an existing project."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "project_id": {
                    "type": "string"
                },

                "decision": {
                    "type": "string"
                }
            },
            "required": [
                "project_id",
                "decision"
            ],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "add_project_task",
        "description": (
            "Add a task to an existing project."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "project_id": {
                    "type": "string"
                },

                "task": {
                    "type": "string"
                }
            },
            "required": [
                "project_id",
                "task"
            ],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "add_project_note",
        "description": (
            "Add a note to an existing project."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "project_id": {
                    "type": "string"
                },

                "note": {
                    "type": "string"
                }
            },
            "required": [
                "project_id",
                "note"
            ],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "send_message_to_client_ai",
        "description": (
            "Send a message to a specific Client AI and "
            "return its actual response. Use this whenever "
            "the owner asks you to talk to, test, query, "
            "or communicate with a Client AI."
        ),
        "parameters": {
            "type": "object",
            "properties": {

                "message": {
                    "type": "string",
                    "description": (
                        "The exact message that should be "
                        "sent to the Client AI."
                    )
                },

                "project_id": {
                    "type": "string",
                    "description": (
                        "The Client AI project ID. "
                        "For Roots & Leaves Collection use "
                        "roots_leaves_client_ai."
                    )
                }
            },
            "required": [
                "message",
                "project_id"
            ],
            "additionalProperties": False
        }
    }
]


# =========================================================
# EXECUTE PROJECT TOOL
# =========================================================

def execute_project_tool(
    tool_name,
    arguments
):

    if tool_name == "create_project":

        return create_project(
            project_id=arguments["project_id"],
            name=arguments["name"],
            project_type=arguments.get(
                "project_type",
                "project"
            ),
            client=arguments.get(
                "client",
                ""
            ),
            status=arguments.get(
                "status",
                "active"
            ),
            goal=arguments.get(
                "goal",
                ""
            )
        )

    if tool_name == "update_project":

        return update_project(
            project_id=arguments["project_id"],
            name=arguments.get("name"),
            project_type=arguments.get("project_type"),
            client=arguments.get("client"),
            status=arguments.get("status"),
            goal=arguments.get("goal")
        )

    if tool_name == "add_project_decision":

        return add_project_decision(
            project_id=arguments["project_id"],
            decision=arguments["decision"]
        )

    if tool_name == "add_project_task":

        return add_project_task(
            project_id=arguments["project_id"],
            task=arguments["task"]
        )

    if tool_name == "add_project_note":

        return add_project_note(
            project_id=arguments["project_id"],
            note=arguments["note"]
        )

    if tool_name == "send_message_to_client_ai":

        return send_message_to_client_ai(
            message=arguments["message"],
            project_id=arguments.get(
                "project_id",
                "roots_leaves_client_ai"
            )
        )

    return {
        "success": False,
        "message": "Unknown project tool."
    }


# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():

    index_path = os.path.join(
        os.path.dirname(__file__),
        "index.html"
    )

    if os.path.exists(index_path):

        return FileResponse(
            index_path,
            media_type="text/html"
        )

    return {

        "status":
            "online",

        "name":
            "MUKA AI",

        "type":
            "Main AI Brain",

        "message":
            "Main MUKA AI is running.",

        "version":
            "2.2.0"
    }


# =========================================================
# INDEX
# =========================================================

@app.get("/index.html")
def index():

    index_path = os.path.join(
        os.path.dirname(__file__),
        "index.html"
    )

    if not os.path.exists(index_path):

        raise HTTPException(
            status_code=404,
            detail="index.html not found."
        )

    return FileResponse(
        index_path,
        media_type="text/html"
    )


# =========================================================
# HEALTH
# =========================================================

@app.get("/health")
def health():

    return {

        "status":
            "ok",

        "message":
            "Main MUKA AI is running.",

        "version":
            "2.2.0"
    }


# =========================================================
# MAIN MUKA CHAT
# =========================================================

@app.post("/chat")
def chat(request: ChatRequest):

    message = request.message.strip()

    user_id = request.user_id.strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Please enter a message."
        )

    if not user_id:
        user_id = "main_user"

    try:

        conversation_history = load_conversation(
            user_id
        )

        long_term_memories = load_long_term_memory(
            user_id
        )

        project_context = get_project_context()

        recent_history = (
            conversation_history[-40:]
        )

        conversation = []

        for item in recent_history:

            role = item.get("role")
            content = item.get("content")

            if role in [
                "user",
                "assistant"
            ] and content:

                conversation.append({
                    "role": role,
                    "content": content
                })

        memory_text = ""

        if long_term_memories:

            memory_text = """

=========================================================
LONG-TERM MEMORY
=========================================================

"""

            for item in long_term_memories:

                if isinstance(item, dict):

                    memory = item.get(
                        "memory",
                        ""
                    )

                else:

                    memory = str(item)

                if memory:

                    memory_text += (
                        "- "
                        + memory
                        + "\n"
                    )

            memory_text += """

=========================================================
END LONG-TERM MEMORY
=========================================================

"""

        conversation.append({
            "role": "user",
            "content": message
        })

        response = client.responses.create(

            model="gpt-5-mini",

            instructions=
                MAIN_MUKA_SYSTEM
                + memory_text
                + project_context,

            input=conversation,

            tools=PROJECT_TOOLS,

            max_output_tokens=1200
        )

        tool_results = []

        while True:

            function_calls = []

            for item in response.output:

                if item.type == "function_call":

                    function_calls.append(item)

            if not function_calls:
                break

            tool_outputs = []

            for call in function_calls:

                try:

                    arguments = json.loads(
                        call.arguments
                    )

                except Exception:

                    arguments = {}

                result = execute_project_tool(
                    call.name,
                    arguments
                )

                tool_results.append({

                    "tool":
                        call.name,

                    "result":
                        result
                })

                tool_outputs.append({

                    "type":
                        "function_call_output",

                    "call_id":
                        call.call_id,

                    "output":
                        json.dumps(
                            result,
                            ensure_ascii=False
                        )
                })

            response = client.responses.create(

                model="gpt-5-mini",

                instructions=
                    MAIN_MUKA_SYSTEM
                    + memory_text
                    + get_project_context(),

                previous_response_id=
                    response.id,

                input=tool_outputs,

                tools=PROJECT_TOOLS,

                max_output_tokens=1200
            )

        reply = (
            response.output_text
            if response.output_text
            else ""
        ).strip()

        if not reply:

            raise RuntimeError(
                "OpenAI returned an empty response."
            )

        memory_to_save = (
            extract_explicit_memory(message)
        )

        memory_saved = False

        if memory_to_save:

            memory_saved = add_long_term_memory(
                user_id,
                memory_to_save
            )

        conversation_history.append({

            "id":
                str(uuid.uuid4()),

            "role":
                "user",

            "content":
                message,

            "timestamp":
                datetime.now().isoformat()
        })

        conversation_history.append({

            "id":
                str(uuid.uuid4()),

            "role":
                "assistant",

            "content":
                reply,

            "timestamp":
                datetime.now().isoformat()
        })

        conversation_history = (
            conversation_history[-100:]
        )

        save_conversation(
            user_id,
            conversation_history
        )

        return {

            "status":
                "success",

            "reply":
                reply,

            "user_id":
                user_id,

            "mode":
                "main_muka_ai",

            "memory_saved":
                memory_saved,

            "project_actions":
                tool_results,

            "projects_loaded":
                len(get_projects())
        }

    except HTTPException:
        raise

    except Exception as error:

        print("")
        print(
            "========================================"
        )
        print(
            "MAIN MUKA ERROR"
        )
        print(
            "========================================"
        )
        print(
            "TYPE:",
            type(error).__name__
        )
        print(
            "ERROR:",
            str(error)
        )
        print(
            "========================================"
        )
        print("")

        raise HTTPException(

            status_code=500,

            detail=
                "Main MUKA AI error: "
                + str(error)
        )


# =========================================================
# GET CHAT
# =========================================================

@app.get("/chat")
def chat_get(

    message: str,

    user_id: str = "main_user"

):

    return chat(

        ChatRequest(

            message=message,

            user_id=user_id
        )
    )


# =========================================================
# CLIENT AI CHAT
# =========================================================

@app.post("/client-chat")
def client_chat(request: ClientChatRequest):

    message = request.message.strip()

    project_id = request.project_id.strip()

    if not message:

        raise HTTPException(
            status_code=400,
            detail="Please enter a message."
        )

    if not project_id:

        project_id = "roots_leaves_client_ai"

    if chat_with_client_ai is None:

        raise HTTPException(

            status_code=500,

            detail=
                "Client AI connection is not available."
        )

    try:

        result = chat_with_client_ai(
            message,
            project_id
        )

        if not result.get("success"):

            raise HTTPException(

                status_code=500,

                detail=result.get(
                    "reply",
                    result.get(
                        "message",
                        "Client AI error."
                    )
                )
            )

        return {

            "status":
                "success",

            "reply":
                result.get(
                    "reply",
                    ""
                ),

            "project_id":
                project_id,

            "client":
                result.get(
                    "client",
                    "Roots & Leaves Collection"
                ),

            "mode":
                "client_ai"
        }

    except HTTPException:
        raise

    except Exception as error:

        print("")
        print(
            "========================================"
        )
        print(
            "CLIENT AI ERROR"
        )
        print(
            "========================================"
        )
        print(
            "TYPE:",
            type(error).__name__
        )
        print(
            "ERROR:",
            str(error)
        )
        print(
            "========================================"
        )
        print("")

        raise HTTPException(

            status_code=500,

            detail=
                "Client AI error: "
                + str(error)
        )


# =========================================================
# MEMORY STATUS
# =========================================================

@app.get("/memory/{user_id}")
def memory_status(user_id: str):

    conversation = load_conversation(
        user_id
    )

    long_term = load_long_term_memory(
        user_id
    )

    projects = get_projects()

    return {

        "status":
            "success",

        "user_id":
            user_id,

        "conversation_messages":
            len(conversation),

        "long_term_memories":
            len(long_term),

        "projects":
            len(projects)
    }


# =========================================================
# VIEW LONG-TERM MEMORY
# =========================================================

@app.get("/memory/{user_id}/long-term")
def view_long_term_memory(user_id: str):

    memories = load_long_term_memory(
        user_id
    )

    return {

        "status":
            "success",

        "user_id":
            user_id,

        "memories":
            memories,

        "count":
            len(memories)
    }


# =========================================================
# PROJECT LIST
# =========================================================

@app.get("/projects")
def projects():

    return {

        "status":
            "success",

        "projects":
            get_projects()
    }


# =========================================================
# SINGLE PROJECT
# =========================================================

@app.get("/projects/{project_id}")
def single_project(project_id: str):

    project = get_project(
        project_id
    )

    if project is None:

        raise HTTPException(

            status_code=404,

            detail=
                "Project not found."
        )

    return {

        "status":
            "success",

        "project_id":
            project_id,

        "project":
            project
    }


# =========================================================
# MANUAL CREATE PROJECT API
# =========================================================

@app.post("/projects/{project_id}")
def manual_create_project(

    project_id: str,

    project: dict

):

    result = create_project(

        project_id=
            project_id,

        name=
            project.get(
                "name",
                project_id
            ),

        project_type=
            project.get(
                "type",
                "project"
            ),

        client=
            project.get(
                "client",
                ""
            ),

        status=
            project.get(
                "status",
                "active"
            ),

        goal=
            project.get(
                "goal",
                ""
            )
    )

    if not result["success"]:

        raise HTTPException(

            status_code=409,

            detail=result["message"]
        )

    return result


# =========================================================
# DELETE PROJECT
# =========================================================

@app.delete("/projects/{project_id}")
def delete_project(project_id: str):

    data = load_project_memory()

    projects = data["projects"]

    if project_id not in projects:

        raise HTTPException(

            status_code=404,

            detail=
                "Project not found."
        )

    deleted = projects.pop(
        project_id
    )

    save_project_memory(
        data
    )

    return {

        "status":
            "success",

        "message":
            "Project deleted.",

        "project_id":
            project_id,

        "deleted":
            deleted
    }


# =========================================================
# CLEAR LONG-TERM MEMORY
# =========================================================

@app.delete("/memory/{user_id}/long-term")
def clear_long_term_memory(user_id: str):

    data = load_json_file(
        LONG_TERM_MEMORY_FILE,
        {}
    )

    if not isinstance(data, dict):
        data = {}

    data.pop(
        user_id,
        None
    )

    save_json_file(
        LONG_TERM_MEMORY_FILE,
        data
    )

    return {

        "status":
            "success",

        "message":
            "Long-term memory cleared.",

        "user_id":
            user_id
    }


# =========================================================
# START SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "main:app",

        host="127.0.0.1",

        port=8000,

        reload=True
    )