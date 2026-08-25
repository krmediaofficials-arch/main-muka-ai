import os
import re
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
    "Main sirf Roots & Leaves Collection ke products, website, "
    "ordering, shipping, payment aur related customer-support "
    "questions mein help kar sakta hoon."
)

NOT_VERIFIED_REPLY = (
    "Mujhe is information ka verified answer Roots & Leaves ke official "
    "sources mein nahi mila, isliye main guess nahi karunga."
)


def _live_source_text(context: Dict[str, Any]) -> str:
    live = context.get("live_website") or {}
    return str(live.get("text") or "")[:70000]


def _website_url(context: Dict[str, Any]) -> str:
    live = context.get("live_website") or {}
    return str(
        live.get("website")
        or "https://rootsandleavescollection.in"
    )


def _knowledge_text() -> str:
    try:
        return build_knowledge_text(max_chars=60000)
    except Exception as error:
        print(
            "KNOWLEDGE LOAD ERROR:",
            type(error).__name__,
            str(error),
        )
        return ""


def _system_prompt(context: Dict[str, Any]) -> str:
    client_name = context.get(
        "client_name",
        "Roots & Leaves Collection",
    )

    project_id = context.get(
        "project_id",
        "roots_leaves_client_ai",
    )

    knowledge = _knowledge_text()
    live_text = _live_source_text(context)
    website = _website_url(context)

    return f"""
You are MUKA AI, the customer-facing sales and support assistant for
{client_name}.

Project ID:
{project_id}

Official website:
{website}

============================================================
SOURCE PRIORITY
============================================================

1. LIVE OFFICIAL WEBSITE = highest priority.
2. Approved Roots & Leaves Q&A = second priority.
3. Official Roots & Leaves web search = final fallback.
4. NEVER use general knowledge to invent a product fact.

If the live website says something different from the old approved Q&A,
the LIVE WEBSITE wins.

============================================================
STRICT CLIENT SCOPE
============================================================

You may answer only about:

- Roots & Leaves Collection
- its products
- ingredients
- preparation and usage
- product benefits/claims
- pricing/offers
- ordering/purchase
- shipping/delivery
- COD/payment
- brand/contact details
- directly related customer support

For unrelated questions, reply only:

"{OUT_OF_SCOPE_REPLY}"

============================================================
STRICT NO-INVENTION RULE
============================================================

NEVER invent:

- price
- discount
- stock
- delivery date
- shipping fee
- refund policy
- checkout steps
- ingredients
- quantities
- preparation instructions
- medical outcomes
- guarantees

Do NOT create a checkout process from common e-commerce knowledge.

For example, if the official information only confirms:
"Go to the official website and use Buy Now"

then do NOT invent:
"enter address -> click payment -> receive SMS -> choose COD"
unless those steps are actually verified in the official source.

============================================================
USAGE
============================================================

When verified usage information is available, give it clearly as
numbered practical steps.

For this product, the approved usage information includes:

- 1 tablespoon hair-mask powder
- about 7–8 tablespoons curd
- egg is optional
- make a smooth, spreadable paste
- apply to scalp and hair
- leave for about 20–30 minutes
- rinse thoroughly
- recommended frequency: 1–2 times per week

Use these only as verified approved instructions.

============================================================
CUSTOMER STYLE
============================================================

Be natural, friendly and sales-oriented.

Answer the customer's exact question first.

Do not dump the entire product catalogue into every answer.

Do not repeatedly say:
"I don't have that information."

Use Hindi/Hinglish when customer uses Hindi/Hinglish.
Use English when customer uses English.

Use short bullets or numbered steps when useful.

============================================================
APPROVED KNOWLEDGE
============================================================

{knowledge}

============================================================
LIVE WEBSITE CONTENT
============================================================

{live_text}
""".strip()


def _ask_model(message: str, context: Dict[str, Any]) -> str:
    response = client.responses.create(
        model=MODEL,
        instructions=_system_prompt(context),
        input=message.strip(),
        max_output_tokens=900,
    )

    return (
        response.output_text or ""
    ).strip()


def _contains_any(text: str, words) -> bool:
    text = text.lower()

    return any(
        word.lower() in text
        for word in words
    )


def _extract_price(context: Dict[str, Any]) -> str | None:
    """
    Try current website first, then approved knowledge.
    """

    live_text = _live_source_text(context)

    # Prefer amounts near product/offer language.
    price_patterns = [
        r"(?:offer|sale|current|price)[^\₹\d]{0,80}₹\s*([0-9][0-9,]*)",
        r"₹\s*([0-9][0-9,]*)[^\n]{0,60}(?:offer|sale|price|hair mask)",
    ]

    for pattern in price_patterns:
        match = re.search(
            pattern,
            live_text,
            flags=re.IGNORECASE,
        )

        if match:
            return f"₹{match.group(1)}"

    # Approved current answer.
    knowledge = _knowledge_text()

    match = re.search(
        r"₹\s*([0-9][0-9,]*)",
        knowledge,
    )

    if match:
        return f"₹{match.group(1)}"

    return None


def _local_fallback(
    message: str,
    context: Dict[str, Any],
) -> str | None:
    """
    Safe fallback for high-value common customer questions.
    This runs without an OpenAI request.
    """

    text = message.strip().lower()

    # PRICE
    if _contains_any(
        text,
        [
            "price",
            "kitne ka",
            "kitna ka",
            "kitne ki",
            "cost",
            "rate",
            "₹",
        ],
    ):
        price = _extract_price(context)

        if price:
            return (
                f"{context.get('client_name', 'Roots & Leaves Collection')} "
                f"Natural Botanical Hair Mask – Mini Luxe ki current listed "
                f"price {price} hai."
            )

    # HOW TO USE
    if _contains_any(
        text,
        [
            "how to use",
            "use kaise",
            "kaise use",
            "kaise lagaye",
            "kaise lagana",
            "usage",
            "application",
            "hair mask kaise",
        ],
    ):
        return (
            "Bilkul 😊 Isse use karne ka simple tarika:\n\n"
            "1. 1 tablespoon hair-mask powder lein.\n"
            "2. Isme about 7–8 tablespoons curd milayein.\n"
            "3. Egg optional hai — chahein to add kar sakte hain.\n"
            "4. Smooth, spreadable paste banayein.\n"
            "5. Paste ko scalp aur hair par evenly apply karein.\n"
            "6. About 20–30 minutes tak laga rehne dein.\n"
            "7. Phir water se thoroughly rinse karein.\n\n"
            "Recommended routine: 1–2 times per week."
        )

    # INGREDIENTS
    if _contains_any(
        text,
        [
            "ingredient",
            "ingredients",
            "isme kya hai",
            "kya kya pada",
            "kya kya hai",
        ],
    ):
        return (
            "Is Natural Botanical Hair Mask mein listed botanical "
            "ingredients hain: Amla, Bhringraj, Hibiscus, Fenugreek, "
            "Aloe Vera aur Curry Leaves."
        )

    # COD
    if _contains_any(
        text,
        [
            "cod",
            "cash on delivery",
            "cash delivery",
            "delivery par payment",
        ],
    ):
        return (
            "Haan 😊 Website par Cash on Delivery (COD) available "
            "dikhaya gaya hai."
        )

    # SHIPPING
    if _contains_any(
        text,
        [
            "shipping",
            "delivery charge",
            "delivery free",
            "free shipping",
            "pan india",
            "pan-india",
        ],
    ):
        return (
            "Website par Free Pan-India Shipping available dikhayi gayi hai."
        )

    # ORDER / BUYING
    if _contains_any(
        text,
        [
            "how to buy",
            "how can i order",
            "how to order",
            "order kaise",
            "order kaise karu",
            "buy kaise",
            "purchase kaise",
            "mujhe order karna",
            "product lena hai",
        ],
    ):
        return (
            "Bilkul 😊 Aap official Roots & Leaves Collection website "
            "https://rootsandleavescollection.in par jaiye aur "
            "Natural Botanical Hair Mask – Mini Luxe ka **Buy Now** "
            "option use karke order start kijiye. Website par COD aur "
            "Free Pan-India Shipping available dikhaya gaya hai.\n\n"
            "Exact checkout steps website ke current checkout flow "
            "par depend karte hain, isliye main unverified steps invent "
            "nahi karunga."
        )

    # BENEFITS
    if _contains_any(
        text,
        [
            "benefit",
            "benefits",
            "fayda",
            "fayde",
            "what does it do",
            "kya fayda",
        ],
    ):
        return (
            "Bilkul 😊 Brand ke according is hair mask ko scalp "
            "nourishment, healthier-looking hair, hair-fall reduction, "
            "dandruff control aur healthy new hair growth support ke "
            "benefits ke saath present kiya gaya hai."
        )

    # PRODUCT BASIC
    if _contains_any(
        text,
        [
            "what is this",
            "what is the product",
            "product kya hai",
            "ye product kya hai",
            "hair mask kya hai",
        ],
    ):
        return (
            "Ye Roots & Leaves Collection ka Natural Botanical Hair Mask "
            "– Mini Luxe hai. Ye botanical hair-mask powder hai jise "
            "paste bana kar scalp aur hair par apply kiya jata hai."
        )

    return None


def _web_search_answer(
    message: str,
    context: Dict[str, Any],
) -> str:
    website = _website_url(context)

    research_prompt = f"""
You are a restricted research layer for the official customer assistant
of Roots & Leaves Collection.

Official website:
{website}

Official Instagram:
@roots_and_leaves_collection

Customer question:
{message}

Search ONLY for information directly related to Roots & Leaves Collection,
its products, ordering, shipping, payment, product usage, or official brand
information.

Search priority:
1. rootsandleavescollection.in
2. Instagram pages/posts belonging to Roots & Leaves Collection

Never use random sellers, resellers, Reddit, Quora or unrelated sites.

If the official sources verify the answer, give the verified answer.

If they do not verify the answer, return exactly:
NOT_VERIFIED

Do not invent anything.
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

    text = (
        response.output_text or ""
    ).strip()

    if not text or text == "NOT_VERIFIED":
        return NOT_VERIFIED_REPLY

    return text


def generate_ai_response(
    message: str,
    context: Dict[str, Any],
) -> Dict[str, Any]:

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

    # ---------------------------------------------------------
    # 1. Deterministic common customer-support answers first.
    # ---------------------------------------------------------

    local_reply = _local_fallback(
        message,
        context,
    )

    if local_reply:
        return {
            "success": True,
            "reply": local_reply,
            "project_id": context.get(
                "project_id",
                "roots_leaves_client_ai",
            ),
            "client": context.get(
                "client_name",
                "Roots & Leaves Collection",
            ),
            "mode": "approved_local_fallback",
        }

    # ---------------------------------------------------------
    # 2. Normal OpenAI reasoning for other relevant questions.
    # ---------------------------------------------------------

    try:
        reply = _ask_model(
            message,
            context,
        )

        if reply == "__NEED_OFFICIAL_WEB_SEARCH__":
            reply = _web_search_answer(
                message,
                context,
            )

        return {
            "success": True,
            "reply": reply,
            "project_id": context.get(
                "project_id",
                "roots_leaves_client_ai",
            ),
            "client": context.get(
                "client_name",
                "Roots & Leaves Collection",
            ),
            "mode": "openai_client_ai",
        }

    except Exception as error:
        print(
            "CLIENT AI OPENAI ERROR:",
            type(error).__name__,
            str(error),
        )

        # -----------------------------------------------------
        # 3. If OpenAI is temporarily unavailable, do NOT show
        #    a scary technical error to the customer.
        # -----------------------------------------------------

        return {
            "success": True,
            "reply": (
                "Sorry, mujhe abhi is question ka verified answer "
                "generate karne mein problem aa rahi hai. "
                "Aap Roots & Leaves Collection ke price, usage, "
                "ingredients, COD, shipping ya ordering ke baare "
                "mein pooch sakte hain."
            ),
            "project_id": context.get(
                "project_id",
                "roots_leaves_client_ai",
            ),
            "client": context.get(
                "client_name",
                "Roots & Leaves Collection",
            ),
            "mode": "safe_error_fallback",
        }