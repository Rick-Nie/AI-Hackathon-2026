"""
AI chatbot wrapper using Claude API.
Conversational response uses Opus; structured preference extraction uses a dedicated Haiku call
so preferences are reliably saved regardless of what the main model outputs.
"""

import os
import json
import anthropic
from models import ChatMessage, UserPreferences

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """You are DietMate67, a friendly AI helping people find restaurants that fit their diet.

Your job:
- Chat naturally about food, dietary needs, and location
- Acknowledge what you learn: "Got it, you're allergic to milk!" / "No pizza, noted!"
- Ask follow-up questions to build a clear picture (e.g. if they say allergic to pizza, ask which ingredient triggers it)
- Reference what you already know: "You mentioned you like Italian and can't have shellfish..."
- Suggest searching for restaurants once you have enough info

Location:
- If they mention a city or neighborhood, acknowledge it and use it for suggestions
- If location is already in their profile, reference it naturally

Dietary changes:
- Users can change their mind. Honor the most recent statement.
- If they say "actually I eat fish now", update your understanding accordingly

Keep responses concise, warm, and conversational."""

# Extraction prompt for the dedicated Haiku call
EXTRACTION_PROMPT = """You are a structured data extractor. Extract dietary preferences from the user's message.

Return ONLY a valid JSON object with any of these keys (omit keys that have no data, use empty list [] only if explicitly cleared):

{{
  "liked_ingredients": ["foods the user likes, e.g. toast, pasta"],
  "disliked_ingredients": ["foods the user dislikes but isn't allergic to, e.g. bagels, mushrooms"],
  "allergens": ["foods/ingredients the user says they're allergic to, e.g. peanuts, gluten, milk"],
  "dietary_styles": ["from: vegan, vegetarian, pescatarian, halal, kosher, keto, paleo, low_fodmap, raw, omnivore"],
  "preferred_cuisines": ["from: italian, chinese, japanese, mexican, indian, thai, mediterranean, american, french, korean, vietnamese, greek, middle_eastern, ethiopian"],
  "disliked_cuisines": ["same options as preferred_cuisines"],
  "location": "city or neighborhood string"
}}

Rules:
- Only extract what was explicitly stated. Do not infer or assume.
- "allergic to pizza" → allergens: ["pizza"] AND disliked_ingredients: ["pizza"] (it's both unsafe and disliked)
- "don't like bagels" → disliked_ingredients: ["bagels"]
- "love toast" → liked_ingredients: ["toast"]
- "I'm vegan" → dietary_styles: ["vegan"]
- "I'm in Berkeley" → location: "Berkeley"
- If nothing dietary was mentioned, return {{}}

Conversation context:
{context}

Return ONLY the JSON object, no explanation, no markdown."""


def _build_messages(user_message: str, history: list[ChatMessage]) -> list[dict]:
    messages = []
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})
    return messages


def _extract_preferences_via_haiku(
    user_message: str,
    history: list[ChatMessage],
) -> dict | None:
    """
    Dedicated Claude Haiku call to reliably extract structured preferences.
    Returns a dict of preference fields, or None on failure.
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build a short context window (last 4 exchanges + current message)
    recent = history[-4:] if len(history) > 4 else history
    context_lines = [f"{m.role}: {m.content}" for m in recent]
    context_lines.append(f"user: {user_message}")
    context = "\n".join(context_lines)

    prompt = EXTRACTION_PROMPT.format(context=context)

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text.strip() if response.content else "{}"

        # Strip accidental markdown code fences
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        data = json.loads(raw)
        # Drop keys with empty values so we don't wipe existing prefs
        return {k: v for k, v in data.items() if v or v == 0}
    except Exception as e:
        print(f"[extraction] Haiku extraction failed: {e}")
        return None


def _merge_preferences(
    current: UserPreferences | None,
    new_data: dict,
) -> UserPreferences:
    """Merge extracted preference data into existing preferences, resolving conflicts."""
    base = current.model_dump() if current else {}

    # Lists: append new items deduped; strings/scalars: overwrite
    for key, val in new_data.items():
        if isinstance(val, list) and isinstance(base.get(key), list):
            combined = list(dict.fromkeys(base[key] + val))
            base[key] = combined
        elif val is not None:
            base[key] = val

    # Conflict resolution: if something is now an allergen, remove it from liked
    for allergen in base.get("allergens", []):
        base["liked_ingredients"] = [x for x in base.get("liked_ingredients", []) if x != allergen]

    # If something is now liked, remove from allergens/disliked
    for liked in base.get("liked_ingredients", []):
        base["allergens"] = [x for x in base.get("allergens", []) if x != liked]
        base["disliked_ingredients"] = [x for x in base.get("disliked_ingredients", []) if x != liked]

    # Disliked should not be in liked
    for disliked in base.get("disliked_ingredients", []):
        base["liked_ingredients"] = [x for x in base.get("liked_ingredients", []) if x != disliked]

    try:
        return UserPreferences(**base)
    except Exception as e:
        print(f"[merge] Preference merge error: {e}")
        return current or UserPreferences()


async def chat(
    user_message: str,
    history: list[ChatMessage],
    current_preferences: UserPreferences | None = None,
) -> tuple[str, UserPreferences | None]:
    """
    Returns (reply, updated_preferences).
    Two parallel concerns:
      1. Conversational reply via Opus
      2. Structured preference extraction via Haiku
    Both run sequentially (sync anthropic client); Haiku call adds ~200ms.
    """
    if not ANTHROPIC_API_KEY:
        return _mock_chat_response(user_message, current_preferences), current_preferences

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system = SYSTEM_PROMPT
    if current_preferences:
        prefs_json = current_preferences.model_dump_json(indent=2)
        system += f"\n\nCurrent saved preferences (already known — don't re-ask):\n{prefs_json}"

    messages = _build_messages(user_message, history)

    # 1. Conversational response
    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=system,
        messages=messages,
    )
    reply = "".join(block.text for block in response.content if hasattr(block, "text"))

    # 2. Dedicated preference extraction (always runs, regardless of what Opus said)
    extracted = _extract_preferences_via_haiku(user_message, history)
    print(f"[extraction] raw extracted: {extracted}")

    updated_preferences = current_preferences
    if extracted:
        updated_preferences = _merge_preferences(current_preferences, extracted)
        print(f"[extraction] merged preferences: {updated_preferences.model_dump()}")

    return reply, updated_preferences


def _mock_chat_response(message: str, prefs: UserPreferences | None) -> str:
    msg_lower = message.lower()
    if any(w in msg_lower for w in ["search", "find", "restaurant", "where"]):
        return "I'd help you search for restaurants! Add your Anthropic API key to get started."
    if any(w in msg_lower for w in ["allerg", "allergic"]):
        return "Got it—allergies are important. Our allergen checker will help keep you safe."
    return "Tell me more about what you're looking for in a restaurant!"
