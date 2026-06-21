"""
AI chatbot wrapper using Claude API.
The LLM handles conversational UX only — allergen safety is always deterministic.
"""

import os
import json
import anthropic
from models import ChatMessage, UserPreferences

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

SYSTEM_PROMPT = """You are DietMate, a chill AI friend helping people find restaurants.

Your job:
- Chat naturally about food and dietary needs
- Listen for: what they LIKE, what they CAN'T HAVE (allergies), and what they DISLIKE
- Acknowledge when you learn something: "Got it, you're allergic to milk" or "So you love sushi!"
- Use their preferences to suggest restaurants
- Build a profile as you chat

How to handle preference changes:
- Users can change their mind. If they contradict an earlier preference, update the profile accordingly.
- If they say "I no longer want gluten" or "I'm not vegan anymore", remove the old preference.
- If they say "I used to like cheese but now I avoid it", move it from likes to dislikes.
- Always prefer the most recent user intent when preferences conflict.

Silent extraction (do this in the background, don't announce it):
- Extract: dietary_styles, allergens, liked_ingredients, disliked_ingredients, preferred_cuisines, disliked_cuisines, etc.
- Put extracted data in <preferences_update>{"allergens": ["milk"], "disliked_ingredients": ["cheese"], ...}</preferences_update>
- If the user changes their mind, output the updated current profile so the app can override the old context.
- Only extract what they actually said—don't guess

When they mention food/diet:
- ACKNOWLEDGE it explicitly: "Ah, gluten-free, got it!" or "So no fish, noted!"
- Use their profile when suggesting: "Based on your likes and allergies..."
- Reference their preferences: "You mentioned you like Italian and can't have shellfish..."

Example flow:
User: "I'm allergic to milk"
You: "Got it, milk allergy—that's important. Any other foods you need to avoid?"
(Extract: allergens: ["milk"])

User: "I love sushi"
You: "Nice! Sushi is great. Any restrictions I should know about?"
(Extract: preferred_cuisines: ["japanese"])

User: "Actually, I don't like cheese anymore"
You: "Understood, cheese is off the list now. Anything else you want me to avoid?"
(Extract: disliked_ingredients: ["cheese"])

Keep it conversational and real."""


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

    def _remove_conflicts(current_dict: dict, new_data: dict) -> dict:
        # If an item moves from liked to disliked or allergic, remove the old conflicting value.
        for item in new_data.get("liked_ingredients", []):
            if item in current_dict.get("disliked_ingredients", []):
                current_dict["disliked_ingredients"] = [x for x in current_dict["disliked_ingredients"] if x != item]
            if item in current_dict.get("allergens", []):
                current_dict["allergens"] = [x for x in current_dict["allergens"] if x != item]

        for item in new_data.get("disliked_ingredients", []):
            if item in current_dict.get("liked_ingredients", []):
                current_dict["liked_ingredients"] = [x for x in current_dict["liked_ingredients"] if x != item]

        for item in new_data.get("allergens", []):
            if item in current_dict.get("liked_ingredients", []):
                current_dict["liked_ingredients"] = [x for x in current_dict["liked_ingredients"] if x != item]
            if item in current_dict.get("disliked_ingredients", []):
                current_dict["disliked_ingredients"] = [x for x in current_dict["disliked_ingredients"] if x != item]

        # If user switches dietary style from one to another, we preserve new intent while not removing unrelated styles.
        return current_dict

    if pref_data:
        try:
            if current_preferences:
                current_dict = current_preferences.model_dump()
                for key, val in pref_data.items():
                    if isinstance(val, list) and key in current_dict and isinstance(current_dict.get(key), list):
                        existing = current_dict[key]
                        current_dict[key] = list(dict.fromkeys(existing + val))
                        current_dict = _remove_conflicts(current_dict, {key: val})
                    elif val:
                        current_dict[key] = val
                updated_preferences = UserPreferences(**current_dict)
            else:
                updated_preferences = UserPreferences(**pref_data)
        except Exception as e:
            print(f"Preference merge error: {e}")
            updated_preferences = current_preferences

    if not updated_preferences and current_preferences:
        updated_preferences = current_preferences

    clean_reply = _clean_response(full_text)
    return clean_reply, updated_preferences


def _mock_chat_response(message: str, prefs: UserPreferences | None) -> str:
    """Fallback when API key isn't set. Keep it simple."""
    msg_lower = message.lower()
    
    # Very minimal keyword matching
    if any(word in msg_lower for word in ["search", "find", "restaurant", "where"]):
        return "I'd help you search for restaurants! Add your Anthropic API key to get started."
    if any(word in msg_lower for word in ["allerg", "allergic"]):
        return "Got it—allergies are important. Our system has a deterministic allergen checker that'll help with that."
    
    # Default: just chat back
    return f"I hear you! Tell me more about what you're looking for in a restaurant."
