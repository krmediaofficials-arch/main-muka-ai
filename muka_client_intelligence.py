"""
MUKA Client Intelligence Layer - V3

Generic conversational intelligence for ANY Client AI.

Rules:
- No client-specific knowledge.
- No product-specific facts.
- No industry-specific assumptions.
- Temporary session memory only.
- Cross-client access is blocked.
- Existing Client AI remains untouched.
"""

import re


class MukaClientIntelligence:

    def __init__(self, client_ai=None):
        self.client_ai = client_ai
        self.sessions = {}

    # ============================================================
    # SESSION MANAGEMENT
    # ============================================================

    def create_session(self, session_id, client_id):

        if not session_id:
            raise ValueError("session_id is required")

        if not client_id:
            raise ValueError("client_id is required")

        existing = self.sessions.get(session_id)

        if existing is not None:

            if existing["client_id"] != client_id:
                raise ValueError(
                    "Session belongs to a different client. "
                    "Cross-client session access is blocked."
                )

            return existing

        self.sessions[session_id] = {
            "client_id": client_id,
            "messages": [],
            "customer_context": {
                "requirements": [],
                "problems": [],
                "goals": [],
                "preferences": [],
                "constraints": [],
                "budget": None,
                "timeframe": None,
                "urgency": None,
                "comparison_requested": False,
            },
            "intent": None,
            "behavior": {},
            "buying_stage": None,
            "objections": [],
            "lead": {},
        }

        return self.sessions[session_id]

    def get_session(self, session_id, client_id=None):

        session = self.sessions.get(session_id)

        if session is None:
            return None

        if client_id is not None:
            if session["client_id"] != client_id:
                raise ValueError(
                    "Cross-client session access is blocked."
                )

        return session

    def clear_session(self, session_id, client_id=None):

        session = self.sessions.get(session_id)

        if session is None:
            return False

        if client_id is not None:
            if session["client_id"] != client_id:
                raise ValueError(
                    "Cross-client session deletion is blocked."
                )

        del self.sessions[session_id]

        return True

    # ============================================================
    # MESSAGE MEMORY
    # ============================================================

    def add_message(
        self,
        session_id,
        client_id,
        role,
        content,
    ):

        if not role:
            raise ValueError("role is required")

        if not content:
            raise ValueError("content is required")

        session = self.create_session(
            session_id,
            client_id,
        )

        session["messages"].append({
            "role": role,
            "content": content,
        })

        return session

    def add_user_message(
        self,
        session_id,
        client_id,
        content,
    ):

        return self.add_message(
            session_id,
            client_id,
            "user",
            content,
        )

    def add_assistant_message(
        self,
        session_id,
        client_id,
        content,
    ):

        return self.add_message(
            session_id,
            client_id,
            "assistant",
            content,
        )

    def get_messages(
        self,
        session_id,
        client_id,
    ):

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return []

        return list(session["messages"])

    # ============================================================
    # INTENT INTELLIGENCE V3
    # ============================================================

    def detect_intent(self, message):

        if not isinstance(message, str):
            return "UNKNOWN"

        text = message.strip().lower()

        if not text:
            return "UNKNOWN"

        # --------------------------------------------------------
        # Purchase
        # --------------------------------------------------------

        purchase_patterns = [
            r"\bi want to buy\b",
            r"\bi want to order\b",
            r"\bi want to purchase\b",
            r"\bi would like to buy\b",
            r"\bmujhe order karna hai\b",
            r"\bmujhe order krna hai\b",
            r"\bmujhe kharidna hai\b",
            r"\bmujhe khareedna hai\b",
            r"\bmujhe lena hai\b",
            r"\bmujhe book karna hai\b",
            r"\bmujhe booking karni hai\b",
            r"\bbook karna hai\b",
        ]

        if any(
            re.search(pattern, text)
            for pattern in purchase_patterns
        ):
            return "PURCHASE_INTENT"

        # --------------------------------------------------------
        # Price objection
        # --------------------------------------------------------

        price_objection_patterns = [
            "too expensive",
            "very expensive",
            "expensive",
            "costly",
            "bahut mehnga",
            "bohot mehnga",
            "zyada mehnga",
            "price zyada",
            "mehnga lag",
            "budget zyada",
            "budget kam",
            "budget low",
            "afford nahi",
            "afford nahin",
            "can't afford",
            "cannot afford",
        ]

        if any(x in text for x in price_objection_patterns):
            return "PRICE_OBJECTION"

        timing_objection_patterns = [
            "abhi nahi",
            "abhi nahin",
            "later",
            "baad mein",
            "baad me",
            "phir kabhi",
            "not now",
            "not right now",
            "abhi time nahi",
            "time nahi hai",
            "abhi possible nahi",
            "abhi possible nahin",
            "thoda baad mein",
            "thoda baad me",
        ]

        if any(x in text for x in timing_objection_patterns):
            return "TIMING_OBJECTION"

        trust_objection_patterns = [
            "trust nahi",
            "bharosa nahi",
            "bharosa kaise karu",
            "scam to nahi",
            "fake to nahi",
            "genuine hai",
            "safe hai",
            "is it genuine",
            "is it safe",
            "trust issue",
            "can i trust",
            "is this legit",
            "legit hai",
            "real hai",
            "fraud to nahi",
        ]

        if any(x in text for x in trust_objection_patterns):
            return "TRUST_OBJECTION"

        need_objection_patterns = [
            "zarurat nahi",
            "zaroorat nahi",
            "need nahi hai",
            "mujhe nahi chahiye",
            "don't need",
            "do not need",
            "not needed",
            "iska kya fayda",
            "kya fayda hai",
            "benefit kya hai",
            "mere liye zaroori nahi",
            "mere liye zaruri nahi",
            "mujhe iski zarurat nahi",
            "mujhe iski zaroorat nahi",
            "kyun chahiye",
            "kyon chahiye",
            "why do i need",
            "why should i buy",
        ]

        if any(x in text for x in need_objection_patterns):
            return "NEED_OBJECTION"

        comparison_objection_patterns = [
            "compare kar raha hoon",
            "compare kar rahi hoon",
            "compare karna hai",
            "dusre options dekh raha",
            "dusre options dekh rahi",
            "other options dekh raha",
            "other options dekh rahi",
            "aur options dekhta hoon",
            "aur options dekh leti hoon",
            "dusre se compare",
            "competition se compare",
            "compare with others",
            "looking at other options",
            "checking other options",
            "let me compare",
            "pehle compare karunga",
            "pehle compare karungi",
        ]

        if any(x in text for x in comparison_objection_patterns):
            return "COMPARISON_OBJECTION"

        interest_objection_patterns = [
            "interested nahi",
            "not interested",
            "interest nahi hai",
            "mujhe interest nahi",
            "rehne do",
            "leave it",
            "no thanks",
            "no thank you",
            "not interested right now",
            "i am not interested",
            "i'm not interested",
            "don't want it",
            "do not want it",
            "mujhe nahi lena",
            "mujhe nahi chahiye",
        ]

        if any(x in text for x in interest_objection_patterns):
            return "INTEREST_OBJECTION"

        requirement_objection_patterns = [
            "ye mere kaam ka nahi",
            "mere kaam ka nahi",
            "mujhe suit nahi karta",
            "mujhe suit nahi karti",
            "mujhe suitable nahi",
            "ye suitable nahi",
            "ye nahi chahiye",
            "ye wala nahi",
            "mere liye nahi",
            "mere business ke liye nahi",
            "mere business ke kaam ka nahi",
            "meri requirement ke hisaab se nahi",
            "meri requirement ke hisab se nahi",
            "requirement match nahi",
            "match nahi karta",
            "match nahi karti",
            "doesn't suit me",
            "does not suit me",
            "not suitable for me",
            "not what i need",
        ]

        if any(x in text for x in requirement_objection_patterns):
            return "REQUIREMENT_MISMATCH"

        approval_objection_patterns = [
            "partner se puchna hai",
            "husband se puchna hai",
            "wife se puchna hai",
            "boss se puchna hai",
            "team se puchna hai",
            "approval lena hai",
            "approval chahiye",
            "decision lena hai",
            "decision lena padega",
            "soch ke batata",
            "soch kar batata",
            "soch ke batati",
            "soch kar batati",
            "soch kar bataunga",
            "soch kar bataungi",
            "pehle puchna hai",
            "discuss karna hai",
            "ghar par discuss karna hai",
            "team se discuss karna hai",
            "i need to ask",
            "need to discuss",
            "let me discuss",
            "let me think",
        ]

        if any(x in text for x in approval_objection_patterns):
            return "APPROVAL_OBJECTION"

        availability_objection_patterns = [
            "available nahi",
            "available nahin",
            "stock nahi",
            "stock nahin",
            "out of stock",
            "mil nahi raha",
            "mil nahi rahi",
            "mil nahi raha hai",
            "kab available hoga",
            "kab available hogi",
            "when available",
            "is it available",
            "available hai kya",
            "available hai?",
            "not available",
        ]

        if any(x in text for x in availability_objection_patterns):
            return "AVAILABILITY_OBJECTION"

        technical_objection_patterns = [
            "kaam karega",
            "kaam nahi karega",
            "work karega",
            "work nahi karega",
            "compatible hai",
            "compatible nahi",
            "support karega",
            "support nahi karega",
            "technical problem",
            "technical issue",
            "problem aayegi",
            "issue aayega",
            "properly work",
            "properly kaam",
            "will it work",
            "does it work",
            "is it compatible",
            "will it support",
        ]

        if any(x in text for x in technical_objection_patterns):
            return "TECHNICAL_OBJECTION"

        # --------------------------------------------------------
        # Price inquiry
        # --------------------------------------------------------

        price_patterns = [
            "price",
            "pricing",
            "kitne ka",
            "kitne ki",
            "kitna hai",
            "kitni hai",
            "rate kya",
            "cost kya",
            "how much",
            "price kya",
        ]

        if any(x in text for x in price_patterns):
            return "PRICE_INQUIRY"

        # --------------------------------------------------------
        # Quote
        # --------------------------------------------------------

        quote_patterns = [
            "quote",
            "quotation",
            "estimate",
            "estimated cost",
            "quotation chahiye",
            "quote chahiye",
            "estimate chahiye",
            "kitna lagega",
        ]

        if any(x in text for x in quote_patterns):
            return "QUOTE_REQUEST"

        # --------------------------------------------------------
        # Demo / trial
        # --------------------------------------------------------

        demo_patterns = [
            "demo chahiye",
            "want a demo",
            "book a demo",
            "demo lena hai",
            "demo dikhao",
            "trial chahiye",
            "free trial",
        ]

        if any(x in text for x in demo_patterns):
            return "DEMO_REQUEST"

        # --------------------------------------------------------
        # How-to
        # --------------------------------------------------------

        how_to_patterns = [
            "kaise use",
            "kaise istemal",
            "use kaise",
            "how to use",
            "how do i use",
            "use karna",
            "kaise karte hain",
            "kaise kare",
            "kaise karna hai",
        ]

        if any(x in text for x in how_to_patterns):
            return "HOW_TO"

        # --------------------------------------------------------
        # Delivery / timeframe inquiry
        # --------------------------------------------------------

        delivery_patterns = [
            "shipping",
            "delivery",
            "deliver",
            "kab milega",
            "kab milegi",
            "delivery kab",
            "delivery charge",
        ]

        if any(x in text for x in delivery_patterns):
            return "DELIVERY_INQUIRY"

        # --------------------------------------------------------
        # Payment
        # --------------------------------------------------------

        payment_patterns = [
            "payment",
            "pay kaise",
            "payment kaise",
            "online payment",
            "cash payment",
            "cod",
            "cash on delivery",
        ]

        if any(x in text for x in payment_patterns):
            return "PAYMENT_INQUIRY"

        # --------------------------------------------------------
        # Support
        # --------------------------------------------------------

        support_patterns = [
            "help chahiye",
            "help me",
            "support chahiye",
            "support",
            "problem solve",
            "issue solve",
            "not working",
            "kaam nahi kar",
        ]

        if any(x in text for x in support_patterns):
            return "SUPPORT_REQUEST"

        # --------------------------------------------------------
        # Complaint
        # --------------------------------------------------------

        complaint_patterns = [
            "complaint",
            "complain",
            "shikayat",
            "not happy",
            "unhappy",
            "bad experience",
            "disappointed",
        ]

        if any(x in text for x in complaint_patterns):
            return "COMPLAINT"

        # --------------------------------------------------------
        # Comparison
        # --------------------------------------------------------

        comparison_patterns = [
            "compare",
            "comparison",
            "difference",
            "which is better",
            "kaunsa better",
            "kaunsa achha",
            "better option",
        ]

        if any(x in text for x in comparison_patterns):
            return "COMPARISON"

        # --------------------------------------------------------
        # Requirement / service request
        # --------------------------------------------------------

        requirement_patterns = [
            r"\bi need\b",
            r"\bi want\b",
            r"\bi am looking for\b",
            r"\bi'm looking for\b",
            r"\bmujhe .+ chahiye\b",
            r"\bmujhe .+ karwana hai\b",
            r"\bmujhe .+ karna hai\b",
        ]

        if any(
            re.search(pattern, text)
            for pattern in requirement_patterns
        ):
            return "REQUIREMENT_REQUEST"

        # --------------------------------------------------------
        # General information
        # --------------------------------------------------------

        information_patterns = [
            "information",
            "info",
            "details",
            "batao",
            "tell me",
            "what is",
            "kya hai",
            "kya hota hai",
            "iske baare",
            "iske bare",
        ]

        if any(x in text for x in information_patterns):
            return "GENERAL_INFORMATION"

        return "UNKNOWN"

    def update_intent(
        self,
        session_id,
        client_id,
        message,
    ):

        session = self.create_session(
            session_id,
            client_id,
        )

        intent = self.detect_intent(message)

        session["intent"] = intent

        return intent

    def get_intent(
        self,
        session_id,
        client_id,
    ):

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return None

        return session["intent"]

    # ============================================================
    # TEXT EXTRACTION HELPERS
    # ============================================================

    def _clean_text(self, value):

        if not value:
            return None

        value = value.strip()

        value = re.sub(
            r"^[\s,:;.\-]+|[\s,:;.\-]+$",
            "",
            value,
        )

        return value or None

    def _extract_requirement(self, message):

        text = message.strip()

        patterns = [
            r"\bi need\s+(.+)",
            r"\bi want\s+(.+)",
            r"\bi am looking for\s+(.+)",
            r"\bi'm looking for\s+(.+)",
            r"\bmujhe\s+(.+?)\s+chahiye\b",
            r"\bmujhe\s+(.+?)\s+karwana hai\b",
            r"\bmujhe\s+(.+?)\s+karna hai\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:

                value = self._clean_text(
                    match.group(1)
                )

                if value:
                    return value

        return None

    def _extract_budget(self, message):

        patterns = [
            r"(?:budget|budget hai|budget of)\s*(?:is|:)?\s*(?:â‚¹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)",
            r"(?:under|within)\s*(?:â‚¹|rs\.?|inr)?\s*([\d,]+(?:\.\d+)?)",
            r"(?:â‚¹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)",
            r"\b([\d,]+)\s*(?:rupees|rs)\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                message,
                re.IGNORECASE,
            )

            if match:
                return match.group(1).replace(",", "")

        return None

    def _extract_timeframe(self, message):

        patterns = [
            r"\btoday\b",
            r"\btomorrow\b",
            r"\btonight\b",
            r"\bthis week\b",
            r"\bnext week\b",
            r"\bthis month\b",
            r"\bnext month\b",
            r"\baaj\b",
            r"\bkal\b",
            r"\bis week\b",
            r"\bagle week\b",
            r"\bwithin \d+ days?\b",
            r"\bin \d+ days?\b",
            r"\bnext \d+ days?\b",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                message,
                re.IGNORECASE,
            )

            if match:
                return match.group(0)

        return None

    # ============================================================
    # GENERIC CUSTOMER CONTEXT
    # ============================================================

    def detect_customer_context(self, message):

        if not isinstance(message, str):
            return {}

        text = message.strip()

        if not text:
            return {}

        lower = text.lower()

        context = {}

        # Requirement
        requirement = self._extract_requirement(text)

        if requirement:
            # Prevent non-requirement action words from becoming requirements.
            excluded_requirements = {
                "jaldi",
                "urgent",
                "urgently",
                "asap",
                "immediately",
                "order",
                "buy",
                "purchase",
                "book",
                "booking",
                "kharidna",
                "kharid",
                "khareedna",
                "lena",
            }

            if requirement.lower().strip() not in excluded_requirements:
                context["requirement"] = requirement

        # Need
        need_patterns = [
            r"\bi need\b",
            r"\bi want\b",
            r"\bi am looking for\b",
            r"\bi'm looking for\b",
            r"\bmujhe\b",
            r"\bchahiye\b",
        ]

        if any(
            re.search(pattern, lower)
            for pattern in need_patterns
        ):
            context["has_need"] = True

        # Problem
        problem_keywords = [
            "problem",
            "issue",
            "difficulty",
            "pareshani",
            "dikkat",
            "not working",
            "kaam nahi kar",
            "nahi ho raha",
            "nahi ho rahi",
            "solve nahi",
        ]

        if any(
            keyword in lower
            for keyword in problem_keywords
        ):
            context["has_problem"] = True

        # Goal
        goal_keywords = [
            "goal",
            "goal hai",
            "target",
            "target hai",
            "i want to achieve",
            "main chahta hoon",
            "main chahti hoon",
            "mera aim",
            "my aim",
        ]

        if any(
            keyword in lower
            for keyword in goal_keywords
        ):
            context["has_goal"] = True

        # Preference
        preference_keywords = [
            "prefer",
            "preference",
            "pasand",
            "mujhe pasand",
            "i prefer",
            "i like",
            "i would like",
        ]

        if any(
            keyword in lower
            for keyword in preference_keywords
        ):
            context["has_preference"] = True

        # Constraint
        constraint_keywords = [
            "only",
            "sirf",
            "must",
            "zaroor",
            "required",
            "requirement",
            "important hai",
            "necessary",
            "compulsory",
        ]

        if any(
            keyword in lower
            for keyword in constraint_keywords
        ):
            context["has_constraint"] = True

        # Budget
        budget = self._extract_budget(text)

        if budget:

            context["budget"] = budget
            context["has_budget_signal"] = True

        elif any(
            keyword in lower
            for keyword in [
                "budget",
                "afford",
                "kitne tak",
                "itne tak",
                "within my budget",
                "reasonable price",
            ]
        ):
            context["has_budget_signal"] = True

        # Timeframe
        timeframe = self._extract_timeframe(text)

        if timeframe:

            context["timeframe"] = timeframe
            context["has_timeframe"] = True

        # Urgency
        urgency_keywords = [
            "urgent",
            "urgently",
            "jaldi",
            "jaldi chahiye",
            "as soon as possible",
            "asap",
            "immediately",
            "abhi chahiye",
        ]

        if any(
            keyword in lower
            for keyword in urgency_keywords
        ):
            context["urgency"] = "high"

        # Comparison
        comparison_keywords = [
            "compare",
            "comparison",
            "difference",
            "which is better",
            "kaunsa better",
            "kaunsa achha",
            "better option",
        ]

        if any(
            keyword in lower
            for keyword in comparison_keywords
        ):
            context["comparison_requested"] = True

        return context

    # ============================================================
    # CONTEXT MEMORY
    # ============================================================

    def update_customer_context(
        self,
        session_id,
        client_id,
        context_updates,
    ):

        if not isinstance(context_updates, dict):
            raise ValueError(
                "context_updates must be a dictionary"
            )

        session = self.create_session(
            session_id,
            client_id,
        )

        context = session["customer_context"]

        for key, value in context_updates.items():

            if value is None:
                continue

            if key == "requirement":

                if value not in context["requirements"]:
                    context["requirements"].append(value)

            elif key == "problem":

                if value not in context["problems"]:
                    context["problems"].append(value)

            elif key == "goal":

                if value not in context["goals"]:
                    context["goals"].append(value)

            elif key == "preference":

                if value not in context["preferences"]:
                    context["preferences"].append(value)

            elif key == "constraint":

                if value not in context["constraints"]:
                    context["constraints"].append(value)

            else:
                context[key] = value

        return dict(context)

    def update_customer_context_from_message(
        self,
        session_id,
        client_id,
        message,
    ):

        detected = self.detect_customer_context(
            message
        )

        return self.update_customer_context(
            session_id,
            client_id,
            detected,
        )

    def get_customer_context(
        self,
        session_id,
        client_id,
    ):

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return {}

        return dict(session["customer_context"])

    # ============================================================
    # CUSTOMER BEHAVIOR INTELLIGENCE
    # ============================================================

    def detect_behavior(self, message, intent=None):
        """Detect generic customer behavior signals."""

        text = (message or "").strip().lower()
        behavior = {}

        if not text:
            return behavior

        exploration_patterns = [
            "just looking",
            "just checking",
            "dekh raha hoon",
            "dekh rahi hoon",
            "bas dekh",
            "explore kar",
            "options batao",
            "options dikhao",
            "kya options",
        ]

        if any(x in text for x in exploration_patterns):
            behavior["exploring"] = True

        evaluation_patterns = [
            "compare",
            "comparison",
            "difference",
            "which is better",
            "kaunsa better",
            "kaunsa achha",
            "better option",
            "options compare",
            "pros and cons",
        ]

        if any(x in text for x in evaluation_patterns):
            behavior["evaluating"] = True

        price_sensitive_patterns = [
            "expensive",
            "too expensive",
            "very expensive",
            "costly",
            "mehnga",
            "bahut mehnga",
            "bohot mehnga",
            "price zyada",
            "budget kam",
            "budget low",
            "afford nahi",
            "afford nahin",
        ]

        if any(x in text for x in price_sensitive_patterns):
            behavior["price_sensitive"] = True

        purchase_patterns = [
            "order karna hai",
            "order karna chahta",
            "order karna chahti",
            "buy karna hai",
            "kharidna hai",
            "purchase karna hai",
            "book karna hai",
            "booking karni hai",
            "sign up karna hai",
            "start karna hai",
            "le lena hai",
        ]

        if any(x in text for x in purchase_patterns):
            behavior["high_purchase_intent"] = True

        information_patterns = [
            "details",
            "information",
            "batao",
            "samjhao",
            "explain",
            "kaise",
            "what is",
            "how does",
            "kya hai",
        ]

        if any(x in text for x in information_patterns):
            behavior["information_seeking"] = True

        urgency_patterns = [
            "urgent",
            "urgently",
            "jaldi",
            "asap",
            "immediately",
            "abhi chahiye",
            "aaj chahiye",
            "as soon as possible",
        ]

        if any(x in text for x in urgency_patterns):
            behavior["urgent"] = True

        if intent == "COMPARISON":
            behavior["evaluating"] = True

        if intent == "PURCHASE_INTENT":
            behavior["high_purchase_intent"] = True

        if intent == "PRICE_OBJECTION":
            behavior["price_sensitive"] = True

        return behavior

    def update_behavior(
        self,
        session_id,
        client_id,
        message,
        intent=None,
    ):
        """Update temporary behavior state for this client session."""

        session = self.create_session(
            session_id,
            client_id,
        )

        detected = self.detect_behavior(
            message,
            intent,
        )

        behavior = session["behavior"]

        for key, value in detected.items():
            if value is True:
                behavior[key] = True

        return dict(behavior)

    def get_behavior(
        self,
        session_id,
        client_id,
    ):
        """Return temporary behavior state."""

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return {}

        return dict(session["behavior"])

    # ============================================================
    # BUYING STAGE INTELLIGENCE
    # ============================================================

    def determine_buying_stage(
        self,
        session_id,
        client_id,
    ):
        """Determine the customer's current generic buying stage."""

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return "UNKNOWN"

        intent = session.get("intent")
        behavior = session.get("behavior", {})
        context = session.get(
            "customer_context",
            {},
        )

        if intent == "PURCHASE_INTENT":
            return "READY_TO_BUY"

        if behavior.get("high_purchase_intent"):
            return "READY_TO_BUY"

        if intent in {
            "PRICE_OBJECTION",
            "COMPLAINT",
        }:
            return "OBJECTION"

        if behavior.get("price_sensitive"):
            return "OBJECTION"

        if intent == "COMPARISON":
            return "EVALUATION"

        if behavior.get("evaluating"):
            return "EVALUATION"

        if context.get("comparison_requested"):
            return "EVALUATION"

        if context.get("has_need"):
            return "INTEREST"

        if context.get("requirements"):
            return "INTEREST"

        if intent in {
            "REQUIREMENT_REQUEST",
            "PRICE_INQUIRY",
            "QUOTE_REQUEST",
            "DEMO_REQUEST",
            "HOW_TO",
        }:
            return "INTEREST"

        if intent == "GENERAL_INFORMATION":
            return "DISCOVERY"

        if behavior.get("information_seeking"):
            return "DISCOVERY"

        return "UNKNOWN"

    def update_objections(
        self,
        session_id,
        client_id,
        message,
        intent=None,
    ):
        """Record meaningful customer objections in temporary session state."""

        session = self.create_session(
            session_id,
            client_id,
        )

        detected_intent = intent or self.detect_intent(message)

        objection_intents = {
            "PRICE_OBJECTION",
            "TRUST_OBJECTION",
            "TIMING_OBJECTION",
            "NEED_OBJECTION",
            "COMPARISON_OBJECTION",
            "INTEREST_OBJECTION",
            "APPROVAL_OBJECTION",
            "AVAILABILITY_OBJECTION",
            "TECHNICAL_OBJECTION",
            "REQUIREMENT_MISMATCH",
        }

        if detected_intent not in objection_intents:
            return list(session["objections"])

        objection = {
            "type": detected_intent,
            "message": message,
        }

        # Avoid storing the exact same objection repeatedly.
        if objection not in session["objections"]:
            session["objections"].append(objection)

        return list(session["objections"])   
    def determine_objection_strategy(
        self,
        session_id,
        client_id,
    ):
        """Determine a generic strategy for handling customer objections."""

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return {
                "strategy": "GENERAL_CLARIFICATION",
                "reason": "No active session.",
            }

        objections = session.get(
            "objections",
            [],
        )

        if not objections:
            return {
                "strategy": "NO_OBJECTION",
                "reason": "No objection detected.",
            }

        latest = objections[-1]
        objection_type = latest.get("type")

        strategies = {
            "PRICE_OBJECTION": {
                "strategy": "VALUE_JUSTIFICATION",
                "reason": "Customer is concerned about price.",
            },

            "TIMING_OBJECTION": {
                "strategy": "TIMING_REASSURANCE",
                "reason": "Customer is not ready to act immediately.",
            },

            "TRUST_OBJECTION": {
                "strategy": "TRUST_BUILDING",
                "reason": "Customer needs more confidence before proceeding.",
            },

            "NEED_OBJECTION": {
                "strategy": "NEED_DISCOVERY",
                "reason": "Customer does not currently see enough need or value.",
            },

            "COMPARISON_OBJECTION": {
                "strategy": "COMPARISON_GUIDANCE",
                "reason": "Customer is evaluating this against other options.",
            },

            "INTEREST_OBJECTION": {
                "strategy": "INTEREST_REENGAGEMENT",
                "reason": "Customer is showing low or declining interest.",
            },

            "REQUIREMENT_MISMATCH": {
                "strategy": "REQUIREMENT_CLARIFICATION",
                "reason": "Customer feels the offering may not match their requirement.",
            },

            "APPROVAL_OBJECTION": {
                "strategy": "DECISION_SUPPORT",
                "reason": "Customer needs approval or another person's decision.",
            },

            "AVAILABILITY_OBJECTION": {
                "strategy": "AVAILABILITY_CLARIFICATION",
                "reason": "Customer has a concern about availability or access.",
            },

            "TECHNICAL_OBJECTION": {
                "strategy": "TECHNICAL_CLARIFICATION",
                "reason": "Customer has a technical or practical concern.",
            },
        }

        return strategies.get(
            objection_type,
            {
                "strategy": "UNDERSTAND_AND_CLARIFY",
                "reason": "Customer objection needs clarification.",
            },
        )

    def determine_conversation_decision(
        self,
        session_id,
        client_id,
    ):
        """Determine the next generic conversation action."""

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return {
                "action": "CLARIFY",
                "reason": "No active conversation session.",
            }

        intent = session.get("intent")
        behavior = session.get("behavior", {})
        context = session.get(
            "customer_context",
            {},
        )
        objections = session.get(
            "objections",
            [],
        )

        # --------------------------------------------------------
        # Highest priority: explicit purchase intent
        # --------------------------------------------------------

        if intent == "PURCHASE_INTENT":
            return {
                "action": "MOVE_TO_CONVERSION",
                "reason": "Customer has expressed purchase intent.",
            }

        if behavior.get("high_purchase_intent"):
            return {
                "action": "MOVE_TO_CONVERSION",
                "reason": "Customer is showing strong purchase intent.",
            }

        # --------------------------------------------------------
        # Active objection
        # --------------------------------------------------------

        if objections:
            strategy = self.determine_objection_strategy(
                session_id,
                client_id,
            )

            return {
                "action": "HANDLE_OBJECTION",
                "strategy": strategy["strategy"],
                "reason": strategy["reason"],
            }

        # --------------------------------------------------------
        # Evaluation / comparison
        # --------------------------------------------------------

        if intent == "COMPARISON_OBJECTION":
            return {
                "action": "GUIDE_EVALUATION",
                "reason": "Customer is comparing available options.",
            }

        if behavior.get("evaluating"):
            return {
                "action": "GUIDE_EVALUATION",
                "reason": "Customer is evaluating options.",
            }

        if context.get("comparison_requested"):
            return {
                "action": "GUIDE_EVALUATION",
                "reason": "Customer requested comparison or evaluation.",
            }

        # --------------------------------------------------------
        # Requirement / need discovery
        # --------------------------------------------------------

        if intent == "REQUIREMENT_REQUEST":
            return {
                "action": "UNDERSTAND_REQUIREMENT",
                "reason": "Customer has expressed a requirement.",
            }

        if context.get("requirements"):
            return {
                "action": "UNDERSTAND_REQUIREMENT",
                "reason": "Customer requirement information is available.",
            }

        # --------------------------------------------------------
        # Information / discovery
        # --------------------------------------------------------

        if intent in {
            "PRICE_INQUIRY",
            "QUOTE_REQUEST",
            "DEMO_REQUEST",
            "HOW_TO",
            "GENERAL_INFORMATION",
        }:
            return {
                "action": "PROVIDE_INFORMATION",
                "reason": "Customer is seeking information.",
            }

        if behavior.get("information_seeking"):
            return {
                "action": "PROVIDE_INFORMATION",
                "reason": "Customer is seeking more information.",
            }

        # --------------------------------------------------------
        # Default
        # --------------------------------------------------------

        return {
            "action": "CLARIFY",
            "reason": "Customer intent is not sufficiently clear.",
        }

    def determine_response_guidance(
        self,
        session_id,
        client_id,
    ):
        """Determine generic guidance for the next assistant response."""

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return {
                "tone": "HELPFUL",
                "direction": "CLARIFY",
                "pressure": "LOW",
            }

        intent = session.get("intent")
        behavior = session.get("behavior", {})
        objections = session.get(
            "objections",
            [],
        )

        # --------------------------------------------------------
        # Purchase intent
        # --------------------------------------------------------

        if intent == "PURCHASE_INTENT":
            return {
                "tone": "CONFIDENT",
                "direction": "GUIDE_TO_CONVERSION",
                "pressure": "LOW",
            }

        if behavior.get("high_purchase_intent"):
            return {
                "tone": "CONFIDENT",
                "direction": "GUIDE_TO_CONVERSION",
                "pressure": "LOW",
            }

        # --------------------------------------------------------
        # Objection handling
        # --------------------------------------------------------

        if objections:
            strategy = self.determine_objection_strategy(
                session_id,
                client_id,
            )

            return {
                "tone": "EMPATHETIC",
                "direction": strategy["strategy"],
                "pressure": "LOW",
            }

        # --------------------------------------------------------
        # Evaluation
        # --------------------------------------------------------

        if intent == "COMPARISON_OBJECTION":
            return {
                "tone": "NEUTRAL",
                "direction": "GUIDE_COMPARISON",
                "pressure": "LOW",
            }

        if behavior.get("evaluating"):
            return {
                "tone": "NEUTRAL",
                "direction": "GUIDE_COMPARISON",
                "pressure": "LOW",
            }

        # --------------------------------------------------------
        # Requirement discovery
        # --------------------------------------------------------

        if intent == "REQUIREMENT_REQUEST":
            return {
                "tone": "CURIOUS",
                "direction": "UNDERSTAND_REQUIREMENT",
                "pressure": "LOW",
            }

        # --------------------------------------------------------
        # Information
        # --------------------------------------------------------

        if intent in {
            "PRICE_INQUIRY",
            "QUOTE_REQUEST",
            "DEMO_REQUEST",
            "HOW_TO",
            "GENERAL_INFORMATION",
        }:
            return {
                "tone": "HELPFUL",
                "direction": "PROVIDE_CLEAR_INFORMATION",
                "pressure": "LOW",
            }

        # --------------------------------------------------------
        # Default
        # --------------------------------------------------------

        return {
            "tone": "HELPFUL",
            "direction": "CLARIFY",
            "pressure": "LOW",
        }

    def update_buying_stage(
        self,
        session_id,
        client_id,
    ):
        """Update the temporary buying stage."""

        session = self.create_session(
            session_id,
            client_id,
        )

        stage = self.determine_buying_stage(
            session_id,
            client_id,
        )

        session["buying_stage"] = stage

        return stage

    def get_buying_stage(
        self,
        session_id,
        client_id,
    ):
        """Return current temporary buying stage."""

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return None

        return session.get("buying_stage")

    # ============================================================
    # COMPLETE CONVERSATION STATE
    # ============================================================

    def get_conversation_state(
        self,
        session_id,
        client_id,
    ):
        """Return the complete temporary intelligence state."""

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return {}

        return {
            "client_id": session["client_id"],
            "intent": session["intent"],
            "customer_context": dict(
                session["customer_context"]
            ),
            "behavior": dict(
                session["behavior"]
            ),
            "buying_stage": session["buying_stage"],
            "objections": list(
                session["objections"]
            ),
            "message_count": len(
                session["messages"]
            ),
        }


    # ============================================================
    # LEAD INTELLIGENCE
    # ============================================================

    def detect_lead_information(self, message):
        """Detect generic lead/contact information from a message."""

        if not isinstance(message, str):
            return {}

        text = message.strip()

        if not text:
            return {}

        lead = {}

        # Email
        email_match = re.search(
            r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
            text,
            re.IGNORECASE,
        )

        if email_match:
            lead["email"] = email_match.group(0).strip()

        # Indian / international-style phone number.
        phone_match = re.search(
            r"(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)",
            text,
        )

        if phone_match:
            lead["phone"] = phone_match.group(0).strip()

        # Basic name signals.
        name_patterns = [
            r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{1,60})",
            r"\bi am\s+([A-Za-z][A-Za-z .'-]{1,60})",
            r"\bi'm\s+([A-Za-z][A-Za-z .'-]{1,60})",
            r"\bmera naam\s+([A-Za-z][A-Za-z .'-]{1,60})",
            r"\bmain\s+([A-Za-z][A-Za-z .'-]{1,60})\s+hoon\b",
        ]

        for pattern in name_patterns:
            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if match:
                name = match.group(1).strip()

                # Avoid treating common conversational words as names.
                blocked_names = {
                    "looking",
                    "interested",
                    "interested in",
                    "from",
                    "here",
                    "ready",
                    "not sure",
                    "just checking",
                }

                if name.lower() not in blocked_names:
                    lead["name"] = name
                    break

        # Lead-interest signals.
        interest_patterns = [
            "interested",
            "i am interested",
            "i'm interested",
            "mujhe interest hai",
            "interested hoon",
            "interested ho",
            "pasand aaya",
            "achha laga",
            "looks good",
            "sounds good",
            "i like it",
        ]

        if any(
            pattern in text.lower()
            for pattern in interest_patterns
        ):
            lead["interested"] = True

        # Explicit disinterest signals.
        disinterest_patterns = [
            "not interested",
            "no interest",
            "interested nahi",
            "interest nahi hai",
            "abhi nahi chahiye",
            "don't need",
            "do not need",
        ]

        if any(
            pattern in text.lower()
            for pattern in disinterest_patterns
        ):
            lead["interested"] = False

        # Purchase/readiness signals.
        purchase_patterns = [
            "order karna hai",
            "buy karna hai",
            "purchase karna hai",
            "book karna hai",
            "kharidna hai",
            "let's proceed",
            "lets proceed",
            "proceed karte hain",
            "start karte hain",
            "mujhe lena hai",
        ]

        if any(
            pattern in text.lower()
            for pattern in purchase_patterns
        ):
            lead["ready_to_convert"] = True

        return lead

    def update_lead_information(
        self,
        session_id,
        client_id,
        lead_updates,
    ):
        """Update temporary lead information for this client session."""

        if not isinstance(lead_updates, dict):
            raise ValueError(
                "lead_updates must be a dictionary"
            )

        session = self.create_session(
            session_id,
            client_id,
        )

        lead = session.setdefault(
            "lead",
            {
                "name": None,
                "phone": None,
                "email": None,
                "interested": None,
                "ready_to_convert": False,
                "status": "UNKNOWN",
            },
        )

        for key, value in lead_updates.items():
            if value is None:
                continue

            if key in {
                "name",
                "phone",
                "email",
            }:
                lead[key] = value

            elif key == "interested":
                lead[key] = bool(value)

            elif key == "ready_to_convert":
                if value is True:
                    lead[key] = True

        if lead.get("ready_to_convert"):
            lead["status"] = "READY_TO_CONVERT"
        elif lead.get("interested") is True:
            lead["status"] = "INTERESTED"
        elif lead.get("interested") is False:
            lead["status"] = "NOT_INTERESTED"
        elif any(
            lead.get(key)
            for key in ("name", "phone", "email")
        ):
            lead["status"] = "CONTACT_CAPTURED"

        return dict(lead)

    def update_lead_from_message(
        self,
        session_id,
        client_id,
        message,
    ):
        """Detect and store generic lead signals from the current message."""

        detected = self.detect_lead_information(
            message
        )

        return self.update_lead_information(
            session_id,
            client_id,
            detected,
        )

    def get_lead_information(
        self,
        session_id,
        client_id,
    ):
        """Return temporary lead information for this session."""

        session = self.get_session(
            session_id,
            client_id,
        )

        if session is None:
            return {}

        return dict(
            session.get(
                "lead",
                {},
            )
        )

    # ============================================================
    # MAIN PIPELINE
    # ============================================================

    def process_message(
        self,
        session_id,
        client_id,
        message,
    ):

        if not message:
            raise ValueError("message is required")

        self.add_user_message(
            session_id,
            client_id,
            message,
        )

        intent = self.update_intent(
            session_id,
            client_id,
            message,
        )

        self.update_behavior(
            session_id,
            client_id,
            message,
            intent,
        )

        self.update_buying_stage(
            session_id,
            client_id,
        )

        self.update_objections(
            session_id,
            client_id,
            message,
            intent,
        )

        objection_strategy = self.determine_objection_strategy(
            session_id,
            client_id,
        )

        conversation_decision = self.determine_conversation_decision(
            session_id,
            client_id,
        )

        context = (
            self.update_customer_context_from_message(
                session_id,
                client_id,
                message,
            )
        )

        lead = self.update_lead_from_message(
            session_id,
            client_id,
            message,
        )

        return {
            "success": True,
            "session_id": session_id,
            "client_id": client_id,
            "message": message,
            "intent": intent,
            "customer_context": context,
            "objection_strategy": objection_strategy,
            "conversation_decision": conversation_decision,
            "lead": lead,
            "status": "intelligence_layer_ready",
        }


