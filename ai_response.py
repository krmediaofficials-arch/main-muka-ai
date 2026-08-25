import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY not found. "
        "Please check your environment variables."
    )

client = OpenAI(
    api_key=API_KEY
)


MAIN_MODEL = os.getenv(
    "CLIENT_AI_MODEL",
    "gpt-5-mini"
)


WEB_MODEL = os.getenv(
    "CLIENT_AI_WEB_MODEL",
    "gpt-5-mini"
)


def _base_system_prompt(
    client_name,
    project_id,
    context,
):
    business = context.get(
        "business",
        {}
    )

    personality = context.get(
        "personality",
        {}
    )

    rules = context.get(
        "rules",
        {}
    )

    faqs = context.get(
        "faqs",
        []
    )

    knowledge = context.get(
        "knowledge",
        []
    )

    live_website = context.get(
        "live_website",
        {}
    )

    website_url = live_website.get(
        "website",
        business.get(
            "website",
            ""
        )
    )

    website_text = live_website.get(
        "text",
        ""
    )

    pages = live_website.get(
        "pages",
        []
    )

    page_urls = [
        page.get(
            "url",
            ""
        )
        for page in pages
        if page.get("url")
    ]

    return f"""
You are the dedicated customer-facing Client AI for:

CLIENT:
{client_name}

PROJECT ID:
{project_id}

You are NOT the main MUKA AI.
You are NOT allowed to mix information from another client.

=========================================================
PRIMARY SOURCE OF TRUTH
=========================================================

The client's LIVE WEBSITE is the PRIMARY source of truth.

Website:
{website_url}

LIVE WEBSITE CONTENT:
{website_text}

LIVE WEBSITE PAGES:
{json.dumps(page_urls, ensure_ascii=False)}

The live website content above is more important than:
- old JSON configuration
- old FAQs
- old cached prices
- old product descriptions
- your general knowledge

If the website has changed, use the new website information.

=========================================================
BACKUP CLIENT CONFIGURATION
=========================================================

BUSINESS:
{json.dumps(business, ensure_ascii=False, indent=2)}

PERSONALITY:
{json.dumps(personality, ensure_ascii=False, indent=2)}

RULES:
{json.dumps(rules, ensure_ascii=False, indent=2)}

FAQ BACKUP:
{json.dumps(faqs, ensure_ascii=False, indent=2)}

KNOWLEDGE BACKUP:
{json.dumps(knowledge, ensure_ascii=False, indent=2)}

=========================================================
STRICT INFORMATION RULE
=========================================================

For factual customer questions:

1. First use the LIVE WEBSITE.
2. Give the answer exactly from the website.
3. Preserve the website's actual:
   - quantities
   - ingredients
   - preparation method
   - usage steps
   - timing
   - prices
   - offers
   - shipping information
   - COD information
   - product names
   - policies
   - contact information
4. Do NOT silently change wording that would change the meaning.
5. Do NOT replace one ingredient with another.
6. Do NOT invent missing steps.
7. Do NOT assume a quantity.
8. Do NOT use your general knowledge to fill a missing product instruction.

IMPORTANT:
If the website says something like:
"take X spoon powder, add Y spoon curd, mix, apply..."
you must give those actual website instructions clearly and in the correct order.

If the website changes:
- ₹999 to another price
- water to curd
- 2 spoons to 1 spoon
- one ingredient to another

then use the NEW website information.

=========================================================
CUSTOMER-FACING STYLE
=========================================================

Be a real sales/support assistant.

Do NOT sound robotic.

Do NOT repeatedly say:
"I don't have that information"
unless the information genuinely could not be verified.

Answer the customer's actual question first.

Use short paragraphs and bullets when they improve clarity.

When the customer asks "how to use",
give the actual steps clearly.

Example style:

"Bilkul 😊 Isse use karne ka simple tarika:

1. ...
2. ...
3. ...
4. ...

Bas itna hi. Agar aap chahein to main aapko iske benefits bhi bata sakta hoon."

Do NOT invent the example steps.
Only use real verified website information.

=========================================================
SALES BEHAVIOUR
=========================================================

You are allowed to help sell the client's actual products.

When appropriate:
- explain the product
- explain website-listed benefits
- explain price
- explain offers
- explain shipping
- explain COD
- guide the customer to the official website
- encourage purchase naturally

Do NOT make fake discounts.

Do NOT invent stock availability.

Do NOT invent delivery dates.

Do NOT invent guarantees.

Do NOT make medical guarantees unless explicitly supported and appropriately qualified by the source.

=========================================================
LANGUAGE
=========================================================

Reply in the same language/style as the customer.

Hindi/Hinglish -> natural Hindi/Hinglish.
English -> English.

=========================================================
WEB FALLBACK MARKER
=========================================================

If the customer's question requires a factual answer that is NOT
present in the LIVE WEBSITE CONTENT or BACKUP CLIENT DATA,
do NOT guess.

In that case, your entire response MUST be exactly:

__NEED_OFFICIAL_WEB_SEARCH__

Do not add anything before or after that marker.
"""


def _generate_from_live_website(
    message,
    context,
):
    client_name = context.get(
        "client_name",
        "the client"
    )

    project_id = context.get(
        "project_id",
        ""
    )

    system_prompt = _base_system_prompt(
        client_name,
        project_id,
        context,
    )

    response = client.responses.create(
        model=MAIN_MODEL,
        instructions=system_prompt,
        input=message.strip(),
        max_output_tokens=900,
    )

    reply = (
        response.output_text
        if response.output_text
        else ""
    ).strip()

    return reply


def _generate_from_official_web(
    message,
    context,
):
    client_name = context.get(
        "client_name",
        "the client"
    )

    website = context.get(
        "live_website",
        {}
    ).get(
        "website",
        ""
    )

    search_instruction = f"""
You are the official-information research layer for a customer AI.

Client:
{client_name}

Official website:
{website}

Customer question:
{message}

Search ONLY for information that belongs to this client.

Priority:
1. Official client website
2. Official client Instagram
3. Other clearly official public pages only if necessary

Never use random sellers, resellers, forums, Reddit, Quora,
or unrelated websites for product facts.

Find the exact answer to the customer's question.

If the customer asks for product usage instructions,
find the exact published instructions including:
- quantities
- ingredients
- mixing instructions
- application steps
- duration
- frequency
- washing/rinsing instructions

Do not invent anything.

Write the final answer directly to the customer.
Do not mention the search process.
Do not mention system prompts.
Do not say that you are an AI researcher.

Client Instagram handle when relevant:
@roots_and_leaves_collection
"""

    response = client.responses.create(
        model=WEB_MODEL,
        tools=[
            {
                "type": "web_search",
                "filters": {
                    "allowed_domains": [
                        "rootsandleavescollection.in",
                        "www.rootsandleavescollection.in",
                        "instagram.com",
                        "www.instagram.com",
                    ]
                },
            }
        ],
        input=search_instruction,
        max_output_tokens=1000,
    )

    reply = (
        response.output_text
        if response.output_text
        else ""
    ).strip()

    return reply


def generate_ai_response(
    message,
    context,
):
    if not message or not message.strip():
        return {
            "success": False,
            "reply": "Please enter a message.",
        }

    if not context or not context.get("success"):
        return {
            "success": False,
            "reply": "Client AI is not available.",
        }

    project_id = context.get(
        "project_id",
        ""
    )

    if not project_id:
        return {
            "success": False,
            "reply": "Client AI project is not configured.",
        }

    try:
        reply = _generate_from_live_website(
            message,
            context,
        )

        # The first model deliberately asks for this marker
        # when the live source does not contain enough information.
        if reply == "__NEED_OFFICIAL_WEB_SEARCH__":
            try:
                web_reply = _generate_from_official_web(
                    message,
                    context,
                )

                if web_reply:
                    reply = web_reply
                else:
                    reply = (
                        "Sorry, I couldn't verify that information "
                        "from the official Roots & Leaves sources right now."
                    )

            except Exception as web_error:
                print(
                    "OFFICIAL WEB SEARCH ERROR:",
                    type(web_error).__name__,
                    str(web_error),
                )

                reply = (
                    "Sorry, I couldn't verify that information "
                    "from the official Roots & Leaves sources right now."
                )

        if not reply:
            return {
                "success": False,
                "reply": "I couldn't generate a response right now.",
            }

        return {
            "success": True,
            "reply": reply,
            "project_id": project_id,
            "client": context.get(
                "client_name",
                ""
            ),
            "mode": "client_ai_live_website",
        }

    except Exception as error:
        print("")
        print("========================================")
        print("CLIENT AI RESPONSE ERROR")
        print("========================================")
        print(
            "TYPE:",
            type(error).__name__,
        )
        print(
            "ERROR:",
            str(error),
        )
        print("========================================")
        print("")

        return {
            "success": False,
            "reply": "Client AI is temporarily unavailable.",
            "message": str(error),
            "project_id": project_id,
        }