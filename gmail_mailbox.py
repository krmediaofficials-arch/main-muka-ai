import os
from datetime import datetime, timezone

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


router = APIRouter(
    prefix="/mailbox",
    tags=["MUKA Mail Box"]
)

TOKEN_FILE = "/opt/muka/gmail_tokens.json"

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify"
]


# =========================================================
# FILE HELPERS
# =========================================================

def load_token_data():
    if not os.path.exists(TOKEN_FILE):
        return {}

    try:
        import json

        with open(
            TOKEN_FILE,
            "r",
            encoding="utf-8"
        ) as file:
            data = json.load(file)

        return data if isinstance(data, dict) else {}

    except Exception as error:
        print(
            "GMAIL MAILBOX TOKEN READ ERROR:",
            type(error).__name__,
            str(error)
        )
        return {}


def save_token_data(data):
    import json

    temp_path = TOKEN_FILE + ".tmp"

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

    os.replace(
        temp_path,
        TOKEN_FILE
    )

    try:
        os.chmod(
            TOKEN_FILE,
            0o600
        )
    except OSError:
        pass


# =========================================================
# GMAIL CREDENTIALS
# =========================================================

def get_gmail_credentials(user_id):

    tokens = load_token_data()

    record = tokens.get(user_id)

    if not record:
        return None, "Gmail account is not connected."

    credentials = Credentials(
        token=record.get("token"),
        refresh_token=record.get("refresh_token"),
        token_uri=record.get(
            "token_uri",
            "https://oauth2.googleapis.com/token"
        ),
        client_id=record.get("client_id"),
        client_secret=os.getenv(
            "GOOGLE_CLIENT_SECRET"
        ),
        scopes=record.get(
            "scopes",
            GMAIL_SCOPES
        )
    )

    try:

        if not credentials.valid:

            if credentials.expired and credentials.refresh_token:

                credentials.refresh(
                    Request()
                )

                record["token"] = credentials.token
                record["updated_at"] = (
                    datetime.now(
                        timezone.utc
                    ).isoformat()
                )

                tokens[user_id] = record

                save_token_data(
                    tokens
                )

            else:
                return None, "Gmail authorization needs to be renewed."

    except Exception as error:

        print(
            "GMAIL CREDENTIAL REFRESH ERROR:",
            type(error).__name__,
            str(error)
        )

        return None, "Unable to refresh Gmail authorization."

    return credentials, None


# =========================================================
# GMAIL INBOX
# =========================================================

def get_header(headers, name):

    target = name.lower()

    for header in headers or []:

        if header.get("name", "").lower() == target:
            return header.get("value", "")

    return ""


def format_message(message):

    payload = message.get(
        "payload",
        {}
    )

    headers = payload.get(
        "headers",
        []
    )

    internal_date = message.get(
        "internalDate"
    )

    date_iso = None

    if internal_date:

        try:

            date_iso = datetime.fromtimestamp(
                int(internal_date) / 1000,
                tz=timezone.utc
            ).isoformat()

        except (TypeError, ValueError, OverflowError):
            date_iso = None

    label_ids = message.get(
        "labelIds",
        []
    )

    return {
        "id": message.get("id"),
        "thread_id": message.get("threadId"),
        "sender": get_header(
            headers,
            "From"
        ),
        "to": get_header(
            headers,
            "To"
        ),
        "subject": get_header(
            headers,
            "Subject"
        ),
        "date": get_header(
            headers,
            "Date"
        ),
        "date_iso": date_iso,
        "snippet": message.get(
            "snippet",
            ""
        ),
        "unread": "UNREAD" in label_ids,
        "starred": "STARRED" in label_ids,
        "important": "IMPORTANT" in label_ids,
        "labels": label_ids
    }


# =========================================================
# API ROUTE
# =========================================================


@router.get("/gmail/message")
def gmail_message(token: str, message_id: str):
    from auth_session import get_session_user
    import base64

    user_id = get_session_user(token)
    if not user_id:
        return JSONResponse(
            {"success": False, "error": "Invalid or expired MUKA session."},
            status_code=401
        )

    if not message_id or len(message_id) > 200:
        return JSONResponse(
            {"success": False, "error": "Invalid Gmail message ID."},
            status_code=400
        )

    credentials, error = get_gmail_credentials(user_id)
    if error:
        return JSONResponse(
            {"success": False, "error": error},
            status_code=400
        )

    def extract_mime_body(raw_data):
        """
        Decode the complete RFC 2822 MIME message instead of
        manually decoding one Gmail payload part.

        This correctly handles:
        - quoted-printable
        - charset
        - multipart/alternative
        - text/html
        - text/plain
        """
        if not raw_data:
            return "", "text"

        try:
            from email import policy
            from email.parser import BytesParser

            raw_bytes = base64.urlsafe_b64decode(
                raw_data + "=" * (-len(raw_data) % 4)
            )

            mail = BytesParser(
                policy=policy.default
            ).parsebytes(raw_bytes)

            html_body = ""
            text_body = ""

            for part in mail.walk():
                if part.is_multipart():
                    continue

                disposition = (
                    part.get_content_disposition() or ""
                ).lower()

                if disposition == "attachment":
                    continue

                content_type = (
                    part.get_content_type() or ""
                ).lower()

                if content_type == "text/html":
                    try:
                        html_body = part.get_content()
                    except Exception:
                        payload = part.get_payload(
                            decode=True
                        )
                        if payload:
                            charset = (
                                part.get_content_charset()
                                or "utf-8"
                            )
                            html_body = payload.decode(
                                charset,
                                errors="replace"
                            )

                    if html_body:
                        return html_body, "html"

                elif content_type == "text/plain":
                    try:
                        text_body = part.get_content()
                    except Exception:
                        payload = part.get_payload(
                            decode=True
                        )
                        if payload:
                            charset = (
                                part.get_content_charset()
                                or "utf-8"
                            )
                            text_body = payload.decode(
                                charset,
                                errors="replace"
                            )

            if text_body:
                return text_body, "text"

        except Exception as error:
            print(
                "GMAIL MIME BODY ERROR:",
                type(error).__name__,
                str(error)
            )

        return "", "text"

    try:
        gmail = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False
        )

        message = gmail.users().messages().get(
            userId="me",
            id=message_id,
            format="raw"
        ).execute()

        raw_message = message.get("raw", "")

        from email import policy
        from email.parser import BytesParser

        raw_bytes = base64.urlsafe_b64decode(
            raw_message +
            "=" * (-len(raw_message) % 4)
        )

        parsed_message = BytesParser(
            policy=policy.default
        ).parsebytes(raw_bytes)

        headers = [
            {
                "name": key,
                "value": value
            }
            for key, value in parsed_message.items()
        ]

        body, body_type = extract_mime_body(raw_message)

        return {
            "success": True,
            "message": {
                "id": message.get("id"),
                "thread_id": message.get("threadId"),
                "sender": get_header(headers, "From"),
                "to": get_header(headers, "To"),
                "cc": get_header(headers, "Cc"),
                "reply_to": get_header(headers, "Reply-To"),
                "subject": get_header(headers, "Subject"),
                "date": get_header(headers, "Date"),
                "snippet": message.get("snippet", ""),
                "body": body,
                "body_type": body_type,
                "unread": "UNREAD" in message.get("labelIds", []),
                "starred": "STARRED" in message.get("labelIds", []),
                "labels": message.get("labelIds", [])
            }
        }

    except Exception as error:
        print(
            "GMAIL MESSAGE ERROR:",
            type(error).__name__,
            str(error)
        )
        return JSONResponse(
            {"success": False, "error": "Unable to open Gmail message."},
            status_code=500
        )

@router.get("/gmail/messages")
def gmail_messages(
    token: str,
    max_results: int = 20,
    page_token: str = None
):

    # Keep the existing MUKA authentication system untouched.
    from auth_session import get_session_user

    user_id = get_session_user(
        token
    )

    if not user_id:

        return JSONResponse(
            {
                "success": False,
                "error": "Invalid or expired MUKA session."
            },
            status_code=401
        )

    max_results = max(
        1,
        min(
            int(max_results),
            50
        )
    )

    credentials, error = get_gmail_credentials(
        user_id
    )

    if error:

        return JSONResponse(
            {
                "success": False,
                "error": error
            },
            status_code=400
        )

    try:

        gmail = build(
            "gmail",
            "v1",
            credentials=credentials,
            cache_discovery=False
        )

        folder_labels = {
            "inbox": "INBOX",
            "starred": "STARRED",
            "sent": "SENT",
            "drafts": "DRAFT",
            "archive": "ALL_MAIL",
            "trash": "TRASH"
        }

        gmail_label = folder_labels.get(
            str(folder or "inbox").lower(),
            "INBOX"
        )

        list_request = gmail.users().messages().list(
            userId="me",
            labelIds=[gmail_label],
            maxResults=max_results
        )

        if page_token:
            list_request = gmail.users().messages().list(
                userId="me",
                labelIds=[gmail_label],
                maxResults=max_results,
                pageToken=page_token
            )

        result = list_request.execute()

        message_refs = result.get(
            "messages",
            []
        )

        messages = []

        for message_ref in message_refs:

            message = gmail.users().messages().get(
                userId="me",
                id=message_ref["id"],
                format="metadata",
                metadataHeaders=[
                    "From",
                    "To",
                    "Subject",
                    "Date"
                ]
            ).execute()

            messages.append(
                format_message(
                    message
                )
            )

        tokens = load_token_data()
        record = tokens.get(user_id, {})

        return {
            "success": True,
            "gmail_connected": True,
            "email": record.get("email"),
            "messages": messages,
            "count": len(messages),
            "next_page_token": result.get(
                "nextPageToken"
            )
        }

    except Exception as error:

        print(
            "GMAIL INBOX ERROR:",
            type(error).__name__,
            str(error)
        )

        return JSONResponse(
            {
                "success": False,
                "error": "Unable to read Gmail inbox."
            },
            status_code=500
        )
