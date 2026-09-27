import os
import re
import json
from openai import OpenAI

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in environment variables.")

client = OpenAI(api_key=API_KEY)

# Valid Schemas for Strict Parsing
VALID_STAGES = {"DISCOVERY", "EVALUATION", "READY_TO_BUY", "DELAY_HESITATION"}
VALID_CATEGORIES = {
    "hesitation_delay", "purchase_intent", "efficacy_value_risk_doubt",
    "suitability_uncertainty", "price_value", "trust_safety",
    "logistics_fulfillment", "general_inquiry"
}


class SecurityError(Exception):
    """Raised when cross-client data leak or unverified context is detected."""
    pass


# ==============================================================================
# ENGINE 1: NATIVE ADVANCED LEAD INTELLIGENCE ENGINE
# ==============================================================================
def _extract_lead_intelligence(message):
    text = (message or "").strip()
    
    phone_match = re.search(r'(?:\+?91[\-\s]?)?[6-9]\d{9}', text)
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    
    name_match = None
    name_patterns = [
        r"(?:my name is|mera naam|i am|main)\s+([a-zA-Za-z]+)",
        r"^([a-zA-Z]{3,15})$"
    ]
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and match.group(1).lower() not in ["hello", "hi", "hey", "help", "order", "price", "info", "okay", "thanks"]:
            name_match = match.group(1).capitalize()
            break

    return {
        "extracted_name": name_match,
        "phone": phone_match.group(0) if phone_match else None,
        "email": email_match.group(0) if email_match else None,
        "has_lead_info": bool(phone_match or email_match or name_match)
    }


# ==============================================================================
# ENGINE 2: SCHEMA VALIDATOR & SANITIZER FOR SEMANTIC OUTPUT
# ==============================================================================
def _validate_and_sanitize_semantic(raw_data):
    """
    Validates and sanitizes dynamic LLM outputs against strict structural schemas.
    """
    if not isinstance(raw_data, dict):
        raw_data = {}

    # 1. Validate Category
    category = str(raw_data.get("primary_category", "general_inquiry")).lower()
    if category not in VALID_CATEGORIES:
        category = "general_inquiry"

    # 2. Validate Buying Stage
    stage = str(raw_data.get("buying_stage", "EVALUATION")).upper()
    if stage not in VALID_STAGES:
        stage = "EVALUATION"

    # 3. Validate Intent Score
    try:
        score = float(raw_data.get("buying_intent_score", 0.5))
        score = max(0.0, min(1.0, score))
    except (ValueError, TypeError):
        score = 0.5

    # 4. Extract Customer Needs & Active Objections
    needs = raw_data.get("primary_customer_needs", [])
    if not isinstance(needs, list):
        needs = [str(needs)] if needs else []

    objections = raw_data.get("active_objections", [])
    if not isinstance(objections, list):
        objections = [str(objections)] if objections else []

    return {
        "literal_meaning": str(raw_data.get("literal_meaning", "")),
        "hidden_intent": str(raw_data.get("hidden_intent", "General inquiry")),
        "primary_category": category,
        "buying_stage": stage,
        "buying_intent_score": score,
        "primary_customer_needs": [str(n) for n in needs],
        "active_objections": [str(o) for o in objections]
    }


# ==============================================================================
# ENGINE 3: FULL CONTEXT MULTI-TURN SEMANTIC REASONING & 360° MEMORY
# ==============================================================================
def _derive_full_conversation_semantics(message, full_history):
    """
    Processes FULL multi-turn conversation history to derive true 360° state memory.
    """
    prompt = f"""
    Analyze the full conversation history and current user message.
    
    FULL HISTORY: {json.dumps(full_history) if full_history else "[]"}
    CURRENT USER MESSAGE: "{message}"

    Extract structured JSON:
    {{
      "literal_meaning": "summary of latest message",
      "hidden_intent": "underlying goal, desire, or hesitation",
      "primary_category": "hesitation_delay | purchase_intent | efficacy_value_risk_doubt | suitability_uncertainty | price_value | trust_safety | logistics_fulfillment | general_inquiry",
      "buying_stage": "DISCOVERY | EVALUATION | READY_TO_BUY | DELAY_HESITATION",
      "buying_intent_score": 0.0 to 1.0,
      "primary_customer_needs": ["extracted core needs/goals across entire chat"],
      "active_objections": ["unresolved objections raised so far"]
    }}
    Return ONLY valid JSON.
    """
    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0
        )
        parsed = json.loads(res.choices[0].message.content)
        return _validate_and_sanitize_semantic(parsed)
    except Exception:
        return _validate_and_sanitize_semantic({})


# ==============================================================================
# ENGINE 4: CONTEXT-AWARE MEMORY & LEAD APPROPRIATENESS ENGINE
# ==============================================================================
def _extract_360_contextual_memory(history, semantic_data):
    memory = {
        "price_shared": False,
        "link_shared": False,
        "primary_customer_needs": semantic_data["primary_customer_needs"],
        "active_objections": semantic_data["active_objections"],
        "turns_count": len(history) if history else 0
    }

    if history:
        for turn in history:
            msg = str(turn).lower()
            if any(k in msg for k in ["rs", "₹", "price", "cost", "rupees", "$"]):
                memory["price_shared"] = True
            if any(k in msg for k in ["http", "www", "link", "website"]):
                memory["link_shared"] = True

    return memory


def _evaluate_lead_appropriateness(semantic_data, memory, history, lead_info):
    """
    Determines if lead contact prompt is genuinely appropriate.
    STRICT RULE: Banned if READY_TO_BUY, DELAY_HESITATION, or already captured/prompted.
    """
    if lead_info["has_lead_info"]:
        return False

    stage = semantic_data["buying_stage"]
    
    # Priority Separation: Never intercept READY_TO_BUY or DELAY stages with lead forms
    if stage in ["READY_TO_BUY", "DELAY_HESITATION"]:
        return False

    history_str = " ".join([str(item) for item in history]).lower() if history else ""
    already_asked = any(k in history_str for k in ["number", "phone", "email", "contact", "details send"])

    if already_asked:
        return False

    # Lead capture is strictly allowed ONLY in EVALUATION stage after value delivery
    score = semantic_data["buying_intent_score"]
    if stage == "EVALUATION" and score >= 0.65 and memory["turns_count"] >= 1:
        return True

    return False


# ==============================================================================
# ENGINE 5: DYNAMIC HUMAN SALES BRAIN STRATEGY ENGINE
# ==============================================================================
def _determine_best_sales_angle(semantic_data, should_prompt_lead):
    category = semantic_data["primary_category"]
    stage = semantic_data["buying_stage"]

    # Priority 1: Ready to buy -> Direct Checkout Guidance
    if stage == "READY_TO_BUY":
        return {
            "strategy": "STOP_SELLING_CHECKOUT",
            "directive": "Customer is ready to buy. STOP PITCHING. Provide clear, direct checkout steps immediately."
        }
    
    # Priority 2: Hesitation -> Respect Space
    if stage == "DELAY_HESITATION":
        return {
            "strategy": "RESPECTFUL_SPACE",
            "directive": "Acknowledge decision politely. Zero sales pressure, warmly keep the door open."
        }

    # Priority 3: Evaluation with Lead Opportunity
    if should_prompt_lead:
        return {
            "strategy": "HELPFUL_LEAD_OFFER",
            "directive": "Answer query directly first, then offer to send tailored details to their phone or email."
        }

    # Priority 4: Objection & Value Resolution
    if category == "efficacy_value_risk_doubt":
        return {
            "strategy": "RISK_REDUCTION_VALUE_PITCH",
            "directive": "Address cost-vs-result doubt by highlighting verified outcome value from knowledge base."
        }

    if category == "price_value":
        return {
            "strategy": "VALUE_PROPOSITION_FOCUS",
            "directive": "Highlight core benefits from verified knowledge base to naturally justify cost."
        }

    return {
        "strategy": "HELPFUL_GUIDANCE",
        "directive": "Provide clear, concise guidance answering the customer's exact question."
    }


# ==============================================================================
# ENGINE 6: CONTEXT-AWARE DYNAMIC CTA ENGINE
# ==============================================================================
def _decide_cta_strategy(stage, semantic_data, should_prompt_lead):
    if stage in ["SHORT_ACK", "DELAY_HESITATION"]:
        return False, "NO_CTA"

    if stage == "READY_TO_BUY":
        return True, "CHECKOUT_CTA"

    if should_prompt_lead:
        return True, "LEAD_CAPTURE_CTA"

    if semantic_data["buying_intent_score"] >= 0.65:
        return True, "SOFT_GUIDANCE_QUESTION"

    return False, "NO_CTA"


# ==============================================================================
# ENGINE 7: STRICT OBJECT-LEVEL SYSTEM ISOLATION VALIDATOR
# ==============================================================================
def _enforce_system_security_isolation(context):
    """
    Validates ownership across ALL sub-objects and domain definitions.
    """
    project_id = context.get("project_id")
    if not project_id:
        raise SecurityError("CRITICAL SECURITY VIOLATION: Missing project_id in execution context.")

    allowed_domain = context.get("rules", {}).get("allowed_domain")
    if not allowed_domain:
        raise SecurityError(f"CRITICAL SECURITY VIOLATION: Missing allowed_domain for project ({project_id}).")

    sanitized_pid = str(project_id).strip()

    def _verify_object_ownership(item_list, list_name):
        for item in item_list:
            if isinstance(item, dict):
                item_pid = item.get("project_id")
                if item_pid and str(item_pid).strip() != sanitized_pid:
                    raise SecurityError(
                        f"CROSS-CLIENT LEAKAGE IN {list_name.upper()}! Active project ({sanitized_pid}) received data tagged for ({item_pid})."
                    )

    # Verify every data array explicitly
    _verify_object_ownership(context.get("knowledge", []), "knowledge")
    _verify_object_ownership(context.get("faqs", []), "faqs")
    _verify_object_ownership(context.get("conversation_history", []), "conversation_history")

    return {
        "client_name": context.get("client_name", "Assigned Client"),
        "project_id": sanitized_pid,
        "allowed_domain": str(allowed_domain).strip(),
        "name": context.get("name", "Assistant"),
        "business": context.get("business", {}),
        "rules": context.get("rules", {}),
        "faqs": context.get("faqs", []),
        "knowledge": context.get("knowledge", []),
        "conversation_history": context.get("conversation_history", [])
    }


# ==============================================================================
# ENGINE 8: POST-GENERATION FEMALE VOICE GUARDRAIL
# ==============================================================================
def _sanitize_female_voice(text):
    if not text:
        return text

    text = re.sub(r'\b(sakta|sakti)\s*/\s*(sakti|sakta)\b', 'sakti', text, flags=re.IGNORECASE)
    
    subs = {
        r'\bsamajh sakta hoon\b': 'samajh sakti hoon',
        r'\bkar sakta hoon\b': 'kar sakti hoon',
        r'\bbata sakta hoon\b': 'bata sakti hoon',
        r'\bde sakta hoon\b': 'de sakti hoon',
        r'\bhelp kar sakta hoon\b': 'help kar sakti hoon',
        r'\bmadad kar sakta hoon\b': 'madad kar sakti hoon'
    }

    for pattern, replacement in subs.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    return text


# ==============================================================================
# MASTER SYSTEM PROMPT BUILDER
# ==============================================================================
def build_client_system_prompt(context, pipeline_data):
    client_name = context["client_name"]
    project_id = context["project_id"]
    ai_name = context["name"]

    semantic_data = pipeline_data["semantic_data"]
    sales_angle = pipeline_data["sales_angle"]
    memory = pipeline_data["context_memory"]
    lead_info = pipeline_data["lead_info"]
    cta_allow, cta_type = pipeline_data["cta_strategy"]

    no_repeat = []
    if memory["price_shared"]:
        no_repeat.append("- Price was ALREADY shared in this session. Do NOT repeat price unless explicitly requested.")
    if memory["link_shared"]:
        no_repeat.append("- Checkout link was ALREADY shared. Do NOT repeat link unless explicitly requested.")

    no_repeat_str = "\n".join(no_repeat) if no_repeat else "- No repetitive constraints active."

    return f"""
You are {ai_name}, an intelligent Female Sales Assistant representing ONLY {client_name} (Project ID: {project_id}, Allowed Domain: {context['allowed_domain']}).

==================================================
21 MASTER BEHAVIORAL DIRECTIVES (MUKA CORE)
==================================================
1. IDENTITY & BOUNDARY: Represent ONLY {client_name}.
2. CLIENT ISOLATION: Use ONLY current client's verified knowledge & domain ({context['allowed_domain']}).
3. VERIFIED KNOWLEDGE ONLY: Use facts strictly present in knowledge base.
4. CUSTOMER NEED UNDERSTANDING: Respond to semantic intent ({semantic_data['hidden_intent']}), not raw keywords.
5. CONVERSATION CONTINUITY: Maintain multi-turn memory. Extracted needs: {semantic_data['primary_customer_needs']}.
6. BUYING STAGE: Active Stage = {semantic_data['buying_stage']}.
7. OBJECTION HANDLING: Address unresolved objections ({semantic_data['active_objections']}) without pushiness.
8. NATURAL PERSUASION: Naturally guide customer by showing solution fit.
9. PROBLEM -> SOLUTION: Acknowledge -> Solution -> Benefit -> Natural Fit.
10. READY-TO-BUY: STOP SELLING immediately. Focus strictly on checkout guidance.
11. LATER / DELAY: Respect decision completely. Zero pressure.
12. ACKNOWLEDGEMENT: Short response (1 sentence) for "ok/acha/thanks".
13. RELEVANCE-FIRST (STRICT): Answer ONLY the immediate intent in 2 short sentences. STRICTLY BANNED UNLESS EXPLICITLY ASKED: usage steps, recipes (tablespoons, curd, ratios), prices, links, and disclaimers. For hair/skin concerns: Acknowledge empathetically -> State relevant product -> Mention core benefit -> STOP.
14. NO REPETITION: Respect active session constraints.
15. SMART CTA CONTROL: Append CTA ONLY if allowed.
16. LEAD INTELLIGENCE: Prompt for details ONLY when appropriate. NEVER prompt during READY_TO_BUY.
  ai_response_professional.py:369:17. DYNAMIC FEMALE VOICE: Speak in a natural female voice. Use "Samajh sakti hoon" ONLY when the user expresses a problem or concern (e.g. dry hair, hair fall). Do NOT use it for direct questions like price, links, ingredients, or out-of-scope requests. For direct queries, start naturally (e.g., "Isme...", "Ji bilkul!...", "Is mask ki price...").
  18. ZERO DISCLAIMERS & CONFIDENT OBJECTION HANDLING (STRICT):
  - NEVER EVER use phrases like "lagta hai", "website par mention hai", "dikhayi jaati hai", "marketed hai", "doctor se consult karein".
  - PRICE OBJECTION (thoda mehenga hai): Explain the real value confidently! Highlight that this mask contains 57+ concentrated natural herbs, replacing expensive salon treatments, plus comes with Free Pan-India Shipping.
  - CONCERNS (hair fall, dandruff, dry hair): Confidently explain that 57+ natural herbs (like Amla, Bhringraj, Fenugreek) nourish the scalp and target that specific concern naturally.
  - NEVER EVER use phrases like "marketed hai", "website par", "dikhayi jaati hai", "suitable for all hair types bataya gaya hai", "doctor se consult karein".
  - Speak like a real human sales advisor in natural Hinglish with 100% confidence.
  - When asked about hair concerns (hair fall, colored hair, dry hair, dandruff), reply directly:
   - When asked about hair concerns (hair fall, colored hair, dry hair, dandruff), reply directly with a short 1-sentence natural empathetic acknowledgment and solution.
19. OUT-OF-SCOPE PROTECTION: Politely refuse queries outside {context['allowed_domain']}.
20. NO INVENTED FACTS: State clearly if information is unavailable.
  21. CONCISE & COMPLETION-SAFE FLOW (STRICT):
  - Maximum 2-3 short, warm sentences per response. Never write long paragraphs that get cut off.
  - When user is ready to buy ("haan order karna hai"), directly give the link and 2 quick steps: "Aap is link se order kar sakti hain: https://rootsandleavescollection.in. Simply product select karke checkout complete kar lijiye!" 
  - Keep responses strictly to 2-3 short, warm sentences.
  - No robotic disclaimers, no English text dumps, no corporate AI jargon.
  - Usage and Buying steps must be simple numbered steps without extra warnings.

==================================================
PIPELINE ANALYSIS METADATA
==================================================
- HIDDEN INTENT: {semantic_data['hidden_intent']}
- CATEGORY: {semantic_data['primary_category']} (Score: {semantic_data['buying_intent_score']})
- BUYING STAGE: {semantic_data['buying_stage']}
- STRATEGY: {sales_angle['strategy']} -> {sales_angle['directive']}
- MEMORY CONSTRAINTS:\n{no_repeat_str}
- LEAD INFO DETECTED: {lead_info['has_lead_info']} | Prompt Recommended: {pipeline_data['should_prompt_lead']}
- CTA ALLOWED: {cta_allow} ({cta_type})

==================================================
VERIFIED CLIENT KNOWLEDGE BASE ({client_name})
==================================================
Business Info: {context['business']}
Rules: {context['rules']}
Knowledge Base: {context['knowledge']}
FAQs: {context['faqs']}
History: {context['conversation_history']}

Generate the optimal response now:
"""


# ==============================================================================
# MAIN RESPONSE GENERATION PIPELINE
# ==============================================================================
def generate_ai_response(message, context):
    if not message or not message.strip():
        return {"success": False, "reply": "Please enter a message."}

    try:
        # Step 1: Enforce Strict Security & Deep Isolation
        clean_context = _enforce_system_security_isolation(context)

        # Step 2: Extract Lead Information
        lead_info = _extract_lead_intelligence(message)

        # Step 3: Full-Context Semantic Reasoning Engine (Handles entire chat history)
        semantic_data = _derive_full_conversation_semantics(message, clean_context["conversation_history"])

        # Step 4: Extract 360° Contextual Memory
        context_memory = _extract_360_contextual_memory(clean_context["conversation_history"], semantic_data)

        # Step 5: Contextual Lead Appropriateness Evaluation
        should_prompt_lead = _evaluate_lead_appropriateness(
            semantic_data, 
            context_memory, 
            clean_context["conversation_history"], 
            lead_info
        )

        # Step 6: Determine Dynamic Sales Strategy
        sales_angle = _determine_best_sales_angle(semantic_data, should_prompt_lead)

        # Step 7: Decide CTA Strategy
        cta_strategy = _decide_cta_strategy(semantic_data["buying_stage"], semantic_data, should_prompt_lead)

        pipeline_data = {
            "lead_info": lead_info,
            "semantic_data": semantic_data,
            "should_prompt_lead": should_prompt_lead,
            "sales_angle": sales_angle,
            "context_memory": context_memory,
            "cta_strategy": cta_strategy
        }

        # Step 8: Build Master System Prompt
        system_prompt = build_client_system_prompt(clean_context, pipeline_data)

        # Step 9: LLM Final Execution
        max_tokens = 800
        response = client.responses.create(
            model="gpt-5-mini",
            instructions=system_prompt,
            input=[{"role": "user", "content": message.strip()}],
            reasoning={"effort": "low"},
            max_output_tokens=max_tokens
        )

        raw_reply = (response.output_text if response.output_text else "").strip()

        if not raw_reply:
            return {"success": False, "reply": "Client AI returned an empty response."}

        # Step 10: Apply Female Voice Guardrail
        sanitized_reply = _sanitize_female_voice(raw_reply)

        return {
            "success": True,
            "reply": sanitized_reply,
            "client": clean_context["client_name"],
            "project_id": clean_context["project_id"],
            "pipeline_meta": {
                "hidden_intent": semantic_data["hidden_intent"],
                "category": semantic_data["primary_category"],
                "buying_stage": semantic_data["buying_stage"],
                "customer_needs": semantic_data["primary_customer_needs"],
                "active_objections": semantic_data["active_objections"],
                "strategy": sales_angle["strategy"],
                "lead_captured": lead_info["has_lead_info"],
                "cta_allowed": cta_strategy[0]
            }
        }

    except SecurityError as sec_err:
        print(f"\n[SECURITY ALERT] {str(sec_err)}\n")
        return {"success": False, "reply": "Security Error: System access boundary violation blocked."}
    except Exception as error:
        print("\n========================================")
        print("CLIENT AI PIPELINE ERROR:", str(error))
        print("========================================\n")
        return {"success": False, "reply": f"Client AI Error: {str(error)}"}











