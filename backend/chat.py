"""
AI chatbot wrapper using Claude API.
The LLM handles conversational UX only — allergen safety is always deterministic.
"""

import os
import json
import anthropic
from models import ChatMessage, UserPreferences

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """You are DietMate, a friendly and conversational AI assistant for dietary preferences and restaurant recommendations.

Your personality:
- Chat like a real person, not a robot
- Be warm, helpful, and respectful
- Remember context from the entire conversation
- Acknowledge off-topic messages gracefully before guiding back to restaurants
- Use natural language, not bullet points (unless specifically asked)

Your goals:
1. Have a natural conversation about what they want to eat
2. Gradually learn their dietary needs, allergens, and food preferences
3. Extract structured data (allergies, diet style, cuisines) from casual chat
4. Suggest restaurant searches when enough info is gathered
5. Never guess on allergen safety — defer to our deterministic engine

Key rules:
- NEVER make allergen safety claims — always use the deterministic rule engine
- When they mention an allergen concern, acknowledge it and recommend searching to let our system verify
- Be granular about allergens (ask specifics if they say "nuts")
- Distinguish between "dislikes" and "allergies" (crucial difference)
- If they ask off-topic questions, respond naturally then gently redirect
- Do not repeat a generic fallback response when the user already provided clear details
- Always answer naturally and directly first, then ask one follow-up question only if needed

Preference extraction:
- Listen for: dietary styles (vegan, halal, kosher, keto, etc.), allergens, cuisines, budget, location
- When you hear preferences, extract them in JSON at the end (wrapped in <preferences_update>...</preferences_update>)
- Only include explicitly mentioned preferences, not assumptions
- Build incrementally—don't force all details at once
- Keep visible text separate from structured output: the user should not see the JSON block

Example good responses:
- User: "I want milk" → You: "Are you looking for restaurants with dairy options, or do you have concerns about milk?"
- User: "I can't drink milk" → You: "Got it, milk allergy! That's important to flag. Any other allergens?"
- User: "Why are you repeating yourself?" → You: "Sorry about that! Let me start fresh. What kind of food are you craving?"

Remember: The conversation should feel natural, not scripted.

Visible response rules:
- Start with a clear, friendly natural-language answer.
- Keep the reply concise and avoid generic statements like "Tell me about your dietary preferences" after the user already gave them.
- If you need more information, ask only one specific follow-up question.
- If you detect preferences, include only the JSON inside <preferences_update>...</preferences_update> after the visible answer.
- Do not expose the JSON block as part of the visible assistant text.
- Do not repeat the same prompt or reintroduce yourself unless the user asks for it.

"""


def _build_messages(
    user_message: str,
    history: list[ChatMessage],
) -> list[dict]:
    messages = []
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": user_message})
    return messages


def _parse_preferences_update(text: str) -> dict | None:
    """Extract structured preference updates from the assistant response."""
    start_tag = "<preferences_update>"
    end_tag = "</preferences_update>"
    start = text.find(start_tag)
    end = text.find(end_tag)
    if start == -1 or end == -1:
        return None
    json_str = text[start + len(start_tag):end].strip()
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        return None


def _clean_response(text: str) -> str:
    """Remove the structured update block from visible response."""
    start_tag = "<preferences_update>"
    end_tag = "</preferences_update>"
    start = text.find(start_tag)
    end = text.find(end_tag)
    if start == -1 or end == -1:
        return text
    return (text[:start] + text[end + len(end_tag):]).strip()


async def chat(
    user_message: str,
    history: list[ChatMessage],
    current_preferences: UserPreferences | None = None,
) -> tuple[str, UserPreferences | None]:
    """
    Send a message to Claude and return (reply, updated_preferences).
    Updated preferences are None if the user didn't provide any new data.
    """
    if not ANTHROPIC_API_KEY:
        return _mock_chat_response(user_message, current_preferences), current_preferences

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    system = SYSTEM_PROMPT
    if current_preferences:
        system += f"\n\nCurrent user preferences:\n{current_preferences.model_dump_json(indent=2)}"

    messages = _build_messages(user_message, history)

    response = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        system=system,
        messages=messages,
    )

    full_text = ""
    for block in response.content:
        if hasattr(block, "text"):
            full_text += block.text

    # Extract any preference updates
    pref_data = _parse_preferences_update(full_text)
    updated_preferences = current_preferences
    if pref_data:
        try:
            if current_preferences:
                current_dict = current_preferences.model_dump()
                # Merge: extend lists, override scalars
                for key, val in pref_data.items():
                    if isinstance(val, list) and isinstance(current_dict.get(key), list):
                        existing = current_dict[key]
                        current_dict[key] = list(set(existing + val))
                    else:
                        current_dict[key] = val
                updated_preferences = UserPreferences(**current_dict)
            else:
                updated_preferences = UserPreferences(**pref_data)
        except Exception:
            pass

    clean_reply = _clean_response(full_text)
    return clean_reply, updated_preferences


def _mock_chat_response(message: str, prefs: UserPreferences | None) -> str:
    msg_lower = message.lower()
    if any(word in msg_lower for word in ["allergen", "allergy", "allergic"]):
        return (
            "I understand you have allergen concerns! Our system uses a deterministic rule engine "
            "to check all allergens — it never relies on AI guessing. Please tell me which specific "
            "allergens you need to avoid (e.g., peanuts, tree nuts, milk, eggs, wheat, soy, fish, "
            "shellfish, sesame) and I'll make sure our restaurant search flags any risks including "
            "cross-contamination. What allergens should I watch for?"
        )
    if any(word in msg_lower for word in ["vegan", "vegetarian", "halal", "kosher", "keto"]):
        return (
            "Great, I can help filter restaurants for your dietary style! "
            "Could you also tell me: (1) any allergens to avoid, (2) specific ingredients you dislike "
            "even if not allergic, and (3) your preferred cuisine types and budget? "
            "The more detail you give, the better I can match you."
        )
    if any(word in msg_lower for word in ["restaurant", "food", "eat", "hungry", "recommend"]):
        return (
            "I'd love to find you the perfect restaurant! To give you the best match, I need a few details:\n"
            "1. Any dietary restrictions or styles (vegan, gluten-free, halal, etc.)?\n"
            "2. Any allergens to strictly avoid?\n"
            "3. What cuisine are you in the mood for?\n"
            "4. What's your location and how far are you willing to travel?\n"
            "5. Budget range ($, $$, $$$)?"
        )
    return (
        "Hi! I'm DietMate. I help you find restaurants that perfectly match your dietary needs — "
        "including allergens, dietary styles, ingredient preferences, and more. "
        "Tell me about your dietary preferences or ask me to find restaurants near you!"
    )
