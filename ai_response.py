import os
from typing import Any, Dict

from dotenv import load_dotenv
from openai import OpenAI

from client_ai_knowledge import build_knowledge_text

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not configured")

client = OpenAI(api_key=API_KEY)

MODEL = os.getenv("CLIENT_AI_MODEL", "gpt-5-mini")
WEB_MODEL = os.getenv("CLIENT_AI_WEB_MODEL", MODEL)

OFFICIAL_DOMAINS = [
    "rootsandleavescollection.in",
    "www.rootsandleavescollection.in",
    "instagram.com",
    "www.instagram.com",
]

OUT_OF_SCOPE_REPLY = (
    "Main sirf Roots & Leaves Collection ke products, website, ordering, "
    "shipping, payment aur related customer-support questions mein help kar sakta hoon."
)

NOT_VERIFIED_REPLY = (
    "Mujhe is information ka verified answer Roots & Leaves ke official sources mein nahi mila, "
    "isliye main guess nahi karunga."
)


def _live_source_text(context: Dict[str, Any]) -> str:
    live = context.get("live_website") or {}
    return str(live.get("text") or "")[:60000]


def _website_url(context: Dict[str, Any]) -> str:
    live = context.get("live_website") or {}
    return str(live.get("website") or "https://rootsandleavescollection.in")


def _system_prompt(context: Dict[str, Any]) -> str:
    client_name = context.get("client_name", "Roots & Leaves Collection")
    project_id = context.get("project_id", "roots_leaves_client_ai")
    knowledge = build_knowledge_text(max_chars=50000)
    live_text = _live_source_text(context)
    website = _website_url(context)

    return f"""
You are MUKA AI, the customer-facing sales and support assistant for {client_name}.
Project ID: {project_id}
Official website: {website}

HIGHEST PRIORITY RULE:
The LIVE OFFICIAL WEBSITE is the current source of truth.
If the live website has information that differs from the older approved Q&A, use the live website.
The approved Q&A is a fallback for questions that the live website does not answer clearly.
Official web search is the final fallback for relevant missing information.

SCOPE:
You may answer ONLY questions related to:
- Roots & Leaves Collection
- its products
- ingredients
- product usage
- product benefits/claims
- pricing/offers
- ordering/purchase
- shipping/delivery
- payment/COD
- brand/contact details
- other directly related customer-support topics

For unrelated general knowledge, politics, sports, coding, finance, medicine unrelated to this product, etc., do not answer the unrelated topic. Use:
"{OUT_OF_SCOPE_REPLY}"

NEVER:
- invent a product fact
- invent a usage quantity
- invent a price, discount, stock status, delivery date, policy or warranty
- claim an outcome as guaranteed unless the official source explicitly says so and the answer is clearly framed as the brand's claim
- replace an official ingredient or instruction with your own suggestion
- cite random third-party sellers as official facts
- mix information from another client

CUSTOMER STYLE:
- Answer the exact question first.
- Be natural, confident, friendly and sales-oriented.
- Do not sound robotic.
- Match the customer's language: Hindi/Hinglish -> Hindi/Hinglish; English -> English.
- Use short bullets/numbered steps for how-to questions.
- When the approved usage instructions answer the question, give the complete practical steps clearly.
- When the customer wants to buy, guide them to the official website and mention verified purchase facts.

APPROVED KNOWLEDGE:
{knowledge}

LIVE WEBSITE CONTENT:
{live_text}
""".strip()


def _ask_model(message: str, context: Dict[str, Any]) -> str:
    response = client.responses.create(
        model=MODEL,
        instructions=_system_prompt(context),
        input=message.strip(),
        max_output_tokens=900,
    )
    return (response.output_text or "").strip()


def _web_search_answer(message: str, context: Dict[str, Any]) -> str:
    website = _website_url(context)

    research_prompt = f"""
You are a restricted research layer for the official customer assistant of Roots & Leaves Collection.

Official website: {website}
Official Instagram: @roots_and_leaves_collection

Customer question:
{message}

Find the answer only if it is directly related to Roots & Leaves Collection or its products.
Search priority:
1. rootsandleavescollection.in
2. Instagram pages/posts belonging to Roots & Leaves Collection

Never use unrelated sources for product facts.
Never invent missing information.
Return a concise customer-facing answer with verified facts only.
If no official source verifies the answer, return exactly: NOT_VERIFIED
""".strip()

    response = client.responses.create(
        model=WEB_MODEL,
        input=research_prompt,
        tools=[
            {
                "type": "web_search",
                "filters": {
                    "allowed_domains": OFFICIAL_DOMAINS,
                },
            }
        ],
        max_output_tokens=900,
    )

    text = (response.output_text or "").strip()
    if not text or text == "NOT_VERIFIED":
        return NOT_VERIFIED_REPLY

    return text


def generate_ai_response(message: str, context: Dict[str, Any]) -> Dict[str, Any]:
    if not message or not message.strip():
        return {"success": False, "reply": "Please enter a message."}

    if not context or not context.get("success"):
        return {"success": False, "reply": "Client AI is not available."}

    try:
        reply = _ask_model(message, context)

        if reply == "__NEED_OFFICIAL_WEB_SEARCH__":
            reply = _web_search_answer(message, context)

        return {
            "success": True,
            "reply": reply,
            "project_id": context.get("project_id", "roots_leaves_client_ai"),
            "client": context.get("client_name", "Roots & Leaves Collection"),
        }

    except Exception as error:
        print("CLIENT AI ERROR:", type(error).__name__, str(error))
        return {
            "success": False,
            "reply": "Client AI is temporarily unavailable.",
            "message": str(error),
        }
