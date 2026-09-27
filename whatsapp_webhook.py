import os
import requests

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse

from dotenv import load_dotenv

from chat_api import chat_with_client_ai


load_dotenv()


# =========================================================
# KR MEDIA WHATSAPP CONFIG
# =========================================================

WHATSAPP_VERIFY_TOKEN = os.getenv(
    "WHATSAPP_VERIFY_TOKEN",
    ""
).strip()

WHATSAPP_ACCESS_TOKEN = os.getenv(
    "WHATSAPP_ACCESS_TOKEN",
    ""
).strip()

WHATSAPP_PHONE_NUMBER_ID = os.getenv(
    "WHATSAPP_PHONE_NUMBER_ID",
    ""
).strip()

WHATSAPP_API_VERSION = os.getenv(
    "WHATSAPP_API_VERSION",
    "v23.0"
).strip()

KR_MEDIA_PROJECT_ID = (
    "kr_media_client_ai_3880e155"
)


router = APIRouter(
    prefix="/whatsapp",
    tags=["WhatsApp"]
)


# =========================================================
# META WEBHOOK VERIFICATION
# =========================================================

@router.get("/webhook")
async def verify_webhook(request: Request):

    params = request.query_params

    mode = params.get("hub.mode")
    verify_token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if (
        mode == "subscribe"
        and verify_token
        and verify_token == WHATSAPP_VERIFY_TOKEN
    ):
        return PlainTextResponse(
            challenge or ""
        )

    return PlainTextResponse(
        "Verification failed",
        status_code=403,
    )


# =========================================================
# WHATSAPP INCOMING WEBHOOK
# =========================================================

@router.post("/webhook")
async def whatsapp_webhook(request: Request):

    try:

        payload = await request.json()

        print(
            "WHATSAPP WEBHOOK RECEIVED:",
            payload
        )

        entries = payload.get(
            "entry",
            []
        )

        for entry in entries:

            changes = entry.get(
                "changes",
                []
            )

            for change in changes:

                value = change.get(
                    "value",
                    {}
                )

                messages = value.get(
                    "messages",
                    []
                )

                for message in messages:

                    if message.get("type") != "text":
                        continue

                    sender = (
                        message
                        .get("from", "")
                        .strip()
                    )

                    text = (
                        message
                        .get("text", {})
                        .get("body", "")
                        .strip()
                    )

                    if not sender or not text:
                        continue

                    # -------------------------------------------------
                    # SAME CUSTOMER = SAME MUKA SESSION
                    # -------------------------------------------------

                    result = chat_with_client_ai(
                        message=text,
                        project_id=KR_MEDIA_PROJECT_ID,
                        session_id=sender,
                    )

                    reply = ""

                    if isinstance(result, dict):
                        reply = str(
                            result.get(
                                "reply",
                                ""
                            )
                        ).strip()

                    if not reply:
                        reply = (
                            "Sorry, I couldn't process "
                            "that message right now."
                        )

                    send_whatsapp_message(
                        recipient=sender,
                        text=reply,
                    )

        return {
            "status": "ok"
        }

    except Exception as error:

        print(
            "WHATSAPP WEBHOOK ERROR:",
            type(error).__name__,
            str(error),
        )

        return {
            "status": "error"
        }


# =========================================================
# SEND MESSAGE THROUGH META WHATSAPP API
# =========================================================

def send_whatsapp_message(
    recipient,
    text,
):

    if not WHATSAPP_ACCESS_TOKEN:
        raise RuntimeError(
            "WHATSAPP_ACCESS_TOKEN is not configured."
        )

    if not WHATSAPP_PHONE_NUMBER_ID:
        raise RuntimeError(
            "WHATSAPP_PHONE_NUMBER_ID is not configured."
        )

    url = (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_API_VERSION}/"
        f"{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": (
            f"Bearer {WHATSAPP_ACCESS_TOKEN}"
        ),
        "Content-Type": "application/json",
    }

    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": recipient,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text,
        },
    }

    response = requests.post(
        url,
        headers=headers,
        json=data,
        timeout=30,
    )

    print(
        "WHATSAPP SEND STATUS:",
        response.status_code,
        response.text,
    )

    response.raise_for_status()

    return response.json()
