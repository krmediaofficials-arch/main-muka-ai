import os
import base64
from email.message import EmailMessage

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from googleapiclient.discovery import build

from gmail_mailbox import get_gmail_credentials, load_token_data

router = APIRouter(
    prefix="/mailbox",
    tags=["MUKA Mail Box Actions"]
)


def get_user(token):
    from auth_session import get_session_user
    return get_session_user(token)


def get_gmail(token):
    user_id = get_user(token)

    if not user_id:
        return None, None, JSONResponse(
            {
                "success": False,
                "error": "Invalid or expired MUKA session."
            },
            status_code=401
        )

    credentials, error = get_gmail_credentials(user_id)

    if error:
        return None, None, JSONResponse(
            {
                "success": False,
                "error": error
            },
            status_code=400
        )

    gmail = build(
        "gmail",
        "v1",
        credentials=credentials,
        cache_discovery=False
    )

    return user_id, gmail, None


FOLDER_CONFIG = {
    "inbox": {
        "label_ids": ["INBOX"]
    },
    "starred": {
        "label_ids": ["STARRED"]
    },
    "sent": {
        "label_ids": ["SENT"]
    },
    "drafts": {
        "label_ids": ["DRAFT"]
    },
    "archive": {
        "q": "-label:inbox -label:trash"
    },
    "trash": {
        "label_ids": ["TRASH"]
    }
}


@router.get("/gmail/folders")
def gmail_folders(token: str, folder: str = "inbox", max_results: int = 20):
    folder = (folder or "inbox").strip().lower()

    if folder not in FOLDER_CONFIG:
        return JSONResponse(
            {
                "success": False,
                "error": "Unknown Gmail folder."
            },
            status_code=400
        )

    max_results = max(1, min(int(max_results), 50))

    user_id, gmail, error_response = get_gmail(token)

    if error_response:
        return error_response

    config = FOLDER_CONFIG[folder]

    try:
        params = {
            "userId": "me",
            "maxResults": max_results
        }

        if config.get("label_ids"):
            params["labelIds"] = config["label_ids"]

        if config.get("q"):
            params["q"] = config["q"]

        result = gmail.users().messages().list(**params).execute()

        messages = []

        for ref in result.get("messages", []):
            message = gmail.users().messages().get(
                userId="me",
                id=ref["id"],
                format="metadata",
                metadataHeaders=[
                    "From",
                    "To",
                    "Subject",
                    "Date"
                ]
            ).execute()

            payload = message.get("payload", {})
            headers = payload.get("headers", [])

            def header(name):
                for item in headers:
                    if item.get("name", "").lower() == name.lower():
                        return item.get("value", "")
                return ""

            labels = message.get("labelIds", [])

            messages.append({
                "id": message.get("id"),
                "thread_id": message.get("threadId"),
                "sender": header("From"),
                "to": header("To"),
                "subject": header("Subject"),
                "date": header("Date"),
                "snippet": message.get("snippet", ""),
                "unread": "UNREAD" in labels,
                "starred": "STARRED" in labels,
                "important": "IMPORTANT" in labels,
                "labels": labels
            })

        token_data = load_token_data()
        account = token_data.get(user_id, {})

        return {
            "success": True,
            "folder": folder,
            "email": account.get("email"),
            "messages": messages,
            "count": len(messages)
        }

    except Exception as error:
        print(
            "GMAIL FOLDER ERROR:",
            type(error).__name__,
            str(error)
        )

        return JSONResponse(
            {
                "success": False,
                "error": "Unable to load Gmail folder."
            },
            status_code=500
        )


@router.post("/gmail/message/action")
def gmail_message_action(
    token: str,
    message_id: str,
    action: str
):
    if not message_id or len(message_id) > 200:
        return JSONResponse(
            {
                "success": False,
                "error": "Invalid Gmail message ID."
            },
            status_code=400
        )

    allowed = {
        "read",
        "unread",
        "star",
        "unstar",
        "archive",
        "trash"
    }

    action = (action or "").strip().lower()

    if action not in allowed:
        return JSONResponse(
            {
                "success": False,
                "error": "Unsupported Gmail action."
            },
            status_code=400
        )

    _, gmail, error_response = get_gmail(token)

    if error_response:
        return error_response

    try:
        body = {}

        if action == "read":
            body = {
                "removeLabelIds": ["UNREAD"]
            }

        elif action == "unread":
            body = {
                "addLabelIds": ["UNREAD"]
            }

        elif action == "star":
            body = {
                "addLabelIds": ["STARRED"]
            }

        elif action == "unstar":
            body = {
                "removeLabelIds": ["STARRED"]
            }

        elif action == "archive":
            body = {
                "removeLabelIds": ["INBOX"]
            }

        elif action == "trash":
            body = {
                "addLabelIds": ["TRASH"]
            }

        result = gmail.users().messages().modify(
            userId="me",
            id=message_id,
            body=body
        ).execute()

        return {
            "success": True,
            "action": action,
            "message_id": result.get("id", message_id)
        }

    except Exception as error:
        print(
            "GMAIL MESSAGE ACTION ERROR:",
            type(error).__name__,
            str(error)
        )

        return JSONResponse(
            {
                "success": False,
                "error": "Unable to update Gmail message."
            },
            status_code=500
        )


@router.post("/gmail/send")
def gmail_send(
    token: str,
    to: str,
    subject: str = "",
    body: str = "",
    cc: str = "",
    reply_to_message_id: str = ""
):
    to = (to or "").strip()
    subject = (subject or "").strip()
    body = body or ""
    cc = (cc or "").strip()

    if not to:
        return JSONResponse(
            {
                "success": False,
                "error": "Recipient email is required."
            },
            status_code=400
        )

    if not body.strip():
        return JSONResponse(
            {
                "success": False,
                "error": "Message body is required."
            },
            status_code=400
        )

    _, gmail, error_response = get_gmail(token)

    if error_response:
        return error_response

    try:
        message = EmailMessage()

        message["To"] = to
        message["Subject"] = subject or "(No subject)"

        if cc:
            message["Cc"] = cc

        message.set_content(body)

        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        send_body = {
            "raw": raw_message
        }

        if reply_to_message_id:
            original = gmail.users().messages().get(
                userId="me",
                id=reply_to_message_id,
                format="metadata",
                metadataHeaders=[
                    "Message-ID",
                    "References",
                    "Subject"
                ]
            ).execute()

            original_headers = original.get(
                "payload", {}
            ).get(
                "headers", []
            )

            original_message_id = ""
            references = ""

            for item in original_headers:
                name = item.get("name", "").lower()
                value = item.get("value", "")

                if name == "message-id":
                    original_message_id = value

                elif name == "references":
                    references = value

            if original_message_id:
                message["In-Reply-To"] = original_message_id

                if references:
                    message["References"] = (
                        references + " " + original_message_id
                    )
                else:
                    message["References"] = original_message_id

            send_body["raw"] = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()

            send_body["threadId"] = original.get("threadId")

        result = gmail.users().messages().send(
            userId="me",
            body=send_body
        ).execute()

        return {
            "success": True,
            "message": "Email sent successfully.",
            "message_id": result.get("id")
        }

    except Exception as error:
        print(
            "GMAIL SEND ERROR:",
            type(error).__name__,
            str(error)
        )

        return JSONResponse(
            {
                "success": False,
                "error": "Unable to send email."
            },
            status_code=500
        )


@router.post("/gmail/draft")
def gmail_create_draft(
    token: str,
    to: str = "",
    subject: str = "",
    body: str = "",
    cc: str = ""
):
    _, gmail, error_response = get_gmail(token)

    if error_response:
        return error_response

    try:
        message = EmailMessage()

        if to.strip():
            message["To"] = to.strip()

        if cc.strip():
            message["Cc"] = cc.strip()

        message["Subject"] = subject.strip() or "(No subject)"
        message.set_content(body or "")

        raw_message = base64.urlsafe_b64encode(
            message.as_bytes()
        ).decode()

        result = gmail.users().drafts().create(
            userId="me",
            body={
                "message": {
                    "raw": raw_message
                }
            }
        ).execute()

        return {
            "success": True,
            "message": "Draft saved.",
            "draft_id": result.get("id")
        }

    except Exception as error:
        print(
            "GMAIL DRAFT ERROR:",
            type(error).__name__,
            str(error)
        )

        return JSONResponse(
            {
                "success": False,
                "error": "Unable to save draft."
            },
            status_code=500
        )
