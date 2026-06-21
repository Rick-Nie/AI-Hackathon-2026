"""
Restaurant search and dietary matching logic.
"""

import os
import math
import asyncio
import anthropic
import httpx
from typing import Optional

from allergens import (
    check_dish_for_allergens,
    score_restaurant_allergen_safety,
    RiskLevel,
)
from models import (
    UserPreferences,
    RestaurantMatch,
    MenuItem,
    AllergenSafetyReport,
    DietaryCompatibilityReport,
    DietaryStyle,
    CuisineType,
)

YELP_API_BASE = "https://api.yelp.com/v3"
YELP_API_KEY = os.getenv("YELP_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


import json as _json

# ── Name-based food inference ─────────────────────────────────────────────────
# (keywords_in_name, food_type_tags)
# Used to infer what a restaurant serves purely from its name when reviews are thin.
_NAME_HINTS: list[tuple[list[str], list[str]]] = [
    (["ice cream", "dairy queen", " dq ", "baskin", "cold stone", "gelato",
      "froyo", "frozen yogurt", "custard", "creamery", "scoops",
      "marble slab", "yogurtland", "menchie", "pinkberry", "chill",
      "soft serve", "ice creamery", " cream ", "haagen", "ben & jerry",
      "dippin dots", "kilwins", "carvel", "rita's water ice"],
     ["ice cream", "dessert", "dairy", "sweet", "frozen treat"]),

    (["burger", "burgers", "mcdonald", "wendy", "five guys", "in-n-out",
      "shake shack", "whataburger", "jack in the box", "habit burger",
      "fatburger", "smashburger", "the counter", "umami burger"],
     ["burgers", "beef", "fast food", "american", "fries", "meat"]),

    (["pizza", "pizzeria", "domino", "papa john", "little caesar",
      "round table", "mountain mike", "mod pizza", "blaze pizza",
      "pizza hut", "california pizza", "sbarro"],
     ["pizza", "italian", "cheese", "bread", "tomato sauce"]),

    (["sushi", "japanese", "ramen", "udon", "tempura", "teriyaki",
      "izakaya", "bento", "sakura", "tonkotsu", "miso ramen"],
     ["sushi", "japanese", "fish", "seafood", "rice", "noodles"]),

    (["chinese", "china", "wonton", "dim sum", "panda express", "szechuan",
      "hunan", "cantonese", "mandarin", "hong kong", "beijing",
      "shanghai", "golden dragon", "peking", "kung fu tea"],
     ["chinese", "rice", "noodles", "stir fry", "dumplings"]),

    (["taco", "tacos", "burrito", "burritos", "quesadilla", "enchilada",
      "tamale", "carnitas", "guacamole", "chipotle", "del taco",
      "taco bell", "el pollo loco", "baja fresh", "fajita", "mexican"],
     ["mexican", "tacos", "burritos", "cheese", "salsa", "tortilla"]),

    (["indian", "india", "curry", "biryani", "tandoori", "naan",
      "samosa", "paneer", "tikka", "masala", "dal ", "dosa"],
     ["indian", "curry", "spicy", "rice", "naan"]),

    (["thai", "thailand", "pad thai", "satay", "tom yum", "bangkok",
      "siamese", "thai basil"],
     ["thai", "noodles", "spicy", "peanut"]),

    (["vietnamese", "vietnam", "pho", "banh mi", "bun bo", "com tam"],
     ["vietnamese", "pho", "noodles", "fresh herbs", "beef"]),

    (["korean", "korea", "bulgogi", "bibimbap", "kimchi", "kbbq",
      "korean bbq", "galbi", "k-bbq"],
     ["korean", "bbq", "spicy", "rice", "fermented"]),

    (["mediterranean", "greek", "falafel", "shawarma", "kebab", "gyro",
      "hummus", "baklava", "tzatziki", "souvlaki"],
     ["mediterranean", "greek", "falafel", "hummus", "lamb"]),

    (["seafood", " fish ", "oyster", "lobster", "crab", "shrimp",
      "fisherman", "ocean house", "sea grill", "fresh catch", "tuna bar"],
     ["seafood", "fish", "shellfish"]),

    (["steakhouse", "steak house", "steak", "bbq", "barbecue",
      "smokehouse", "ribs", "brisket", "outback", "longhorn",
      "texas roadhouse", "ruth chris", "flemings", "morton"],
     ["steak", "beef", "grill", "meat", "bbq"]),

    (["chicken", "pollo", "kfc", "chick-fil-a", "popeyes", "wingstop",
      "buffalo wild wings", "raising cane", "zaxby"],
     ["chicken", "poultry", "fried chicken"]),

    (["wings", "wing stop"],
     ["chicken wings", "fried chicken"]),

    (["coffee", "cafe", "café", "starbucks", "dunkin", "peet",
      "blue bottle", "philz", "espresso"],
     ["coffee", "cafe", "beverages", "pastry"]),

    (["bakery", "patisserie", "donut", "doughnut", "bagel",
      "croissant", "cupcake", "muffin", "boulangerie"],
     ["bakery", "pastry", "bread", "sweet", "breakfast"]),

    (["breakfast", "brunch", "pancake", "waffle", "benedict",
      "omelette", "ihop", "denny", "perkins", "first watch"],
     ["breakfast", "brunch", "eggs", "pancakes", "american"]),

    (["vegan", "vegetarian", "plant based", "plant-based",
      "veggie", "herbivore"],
     ["vegan", "vegetarian", "plant-based", "healthy"]),

    (["sandwich", "sub", "hoagie", "panini", "subway",
      "jersey mike", "firehouse", "quiznos", "jimmy john", "deli"],
     ["sandwiches", "deli", "bread", "lunch"]),

    (["bar ", " bar", "pub", "tavern", "brewery", "brewing",
      "ale house", "taproom", "gastropub", "lounge", "saloon"],
     ["bar food", "alcohol", "beer", "pub food"]),

    (["salad", "poke", "acai", "smoothie", "juice bar", "bowl",
      "organic market", "sprouts"],
     ["salad", "healthy", "fresh", "vegetables"]),

    (["pasta", "trattoria", "osteria", "ristorante", "lasagna",
      "spaghetti", "olive garden", "carrabba"],
     ["pasta", "italian", "cheese"]),

    (["french", "brasserie", "bistro", "crepe", "crêpe", "le café"],
     ["french", "crepes", "pastry", "bistro"]),

    (["ethiopian", "eritrean", "african", "injera"],
     ["ethiopian", "african", "injera", "spiced"]),

    (["hot dog", "frank", "portillo", "dog house"],
     ["hot dogs", "american", "fast food"]),
]


def _infer_food_from_name(name: str) -> list[str]:
    """Return food-type tags inferred purely from the restaurant name."""
    name_lower = " " + name.lower() + " "
    hints: set[str] = set()
    for keywords, tags in _NAME_HINTS:
        if any(kw in name_lower for kw in keywords):
            hints.update(tags)
    return list(hints)


# ── Claude Haiku analysis ─────────────────────────────────────────────────────

async def _analyze_restaurant(
    name: str,
    cuisine_tags: list[str],
    editorial: str | None,
    review_texts: list[str],
    preferences: UserPreferences,
    name_hints: list[str] | None = None,
    serves_info: list[str] | None = None,
) -> dict:
    """
    Use Claude Haiku to assess a restaurant's dietary compatibility.
    Returns: food_types, dietary_note, fits_diet, liked_matches, allergen_hits, disliked_hits
    """
    if not ANTHROPIC_API_KEY:
        return {
            "food_types": cuisine_tags, "dietary_note": "", "fits_diet": None,
            "liked_matches": [], "allergen_hits": [], "disliked_hits": [],
        }

    name_hints = name_hints or []
    serves_info = serves_info or []

    context_lines: list[str] = []
    if name_hints:
        context_lines.append(f"Food types inferred from restaurant name: {', '.join(name_hints)}")
    if serves_info:
        context_lines.append(f"Google attributes: {', '.join(serves_info)}")
    if editorial:
        context_lines.append(f"Description: {editorial}")
    if review_texts:
        context_lines.append("Customer reviews:\n" + "\n".join(f"- {r[:300]}" for r in review_texts[:5]))
    context = "\n".join(context_lines) or "No additional information available."

    prefs_lines: list[str] = []
    if preferences.dietary_styles:
        prefs_lines.append(f"Dietary style: {', '.join(s.value for s in preferences.dietary_styles)}")
    if preferences.allergens:
        prefs_lines.append(f"ALLERGENS TO AVOID (critical): {', '.join(preferences.allergens)}")
    if preferences.liked_ingredients:
        prefs_lines.append(f"Liked foods: {', '.join(preferences.liked_ingredients)}")
    if preferences.disliked_ingredients:
        prefs_lines.append(f"Disliked foods: {', '.join(preferences.disliked_ingredients)}")
    prefs_text = "\n".join(prefs_lines) if prefs_lines else "No dietary preferences set."

    prompt = f"""You are analyzing a restaurant to determine dietary compatibility for a user.

Restaurant: {name}
Google cuisine categories: {', '.join(cuisine_tags) or 'restaurant'}

CONTEXT:
{context}

USER PREFERENCES:
{prefs_text}

TASK 1 — Food tags (8-15 tags, lowercase):
Extract specific foods, dishes, ingredients, and dietary attributes this restaurant serves.
IMPORTANT: Use the "Food types inferred from restaurant name" listed above as your PRIMARY source —
include those tags even if reviews don't explicitly confirm them.
Then add any additional tags from reviews/description.
Examples: "ice cream", "burgers", "vegan options", "gluten-free", "sushi", "pork dishes", "brunch"

TASK 2 — Cross-reference preferences:
- liked_matches: user's liked foods/ingredients present here
- allergen_hits: user's allergens that appear in this restaurant's food
- disliked_hits: user's disliked foods present here

TASK 3 — Verdict:
- fits_diet: true if compatible, false if conflicts with allergens/diet, null if unclear
- dietary_note: 1-2 sentences explaining compatibility based on evidence

Return ONLY valid JSON:
{{
  "food_types": ["tag1", "tag2", ...],
  "liked_matches": [],
  "allergen_hits": [],
  "disliked_hits": [],
  "fits_diet": null,
  "dietary_note": ""
}}"""

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        # The Anthropic SDK call is synchronous/blocking. Run it in a worker
        # thread so the ~20 gathered analyses actually execute concurrently
        # instead of serializing on the event loop (was ~40s, now ~3-4s).
        response = await asyncio.to_thread(
            client.messages.create,
            model="claude-haiku-4-5-20251001",
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = (response.content[0].text if response.content else "{}").strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        data = _json.loads(raw)
        return {
            "food_types": data.get("food_types") or cuisine_tags,
            "dietary_note": data.get("dietary_note") or "",
            "fits_diet": data.get("fits_diet"),
            "liked_matches": data.get("liked_matches") or [],
            "allergen_hits": data.get("allergen_hits") or [],
            "disliked_hits": data.get("disliked_hits") or [],
        }
    except Exception as e:
        print(f"[analyze_restaurant] failed for {name}: {e}")
        return {
            "food_types": cuisine_tags, "dietary_note": "", "fits_diet": None,
            "liked_matches": [], "allergen_hits": [], "disliked_hits": [],
        }


# Map DietaryStyle to Yelp categories
DIETARY_STYLE_TO_YELP_CATEGORIES: dict[str, list[str]] = {
    DietaryStyle.VEGAN: ["vegan"],
    DietaryStyle.VEGETARIAN: ["vegetarian"],
    DietaryStyle.HALAL: ["halal"],
    DietaryStyle.KOSHER: ["kosher"],
}

CUISINE_TO_YELP: dict[str, str] = {
    CuisineType.ITALIAN: "italian",
    CuisineType.CHINESE: "chinese",
    CuisineType.JAPANESE: "japanese",
    CuisineType.MEXICAN: "mexican",
    CuisineType.INDIAN: "indpak",
    CuisineType.THAI: "thai",
    CuisineType.MEDITERRANEAN: "mediterranean",
    CuisineType.AMERICAN: "newamerican",
    CuisineType.FRENCH: "french",
    CuisineType.KOREAN: "korean",
    CuisineType.VIETNAMESE: "vietnamese",
    CuisineType.GREEK: "greek",
    CuisineType.MIDDLE_EASTERN: "mideastern",
    CuisineType.ETHIOPIAN: "ethiopian",
}

DIETARY_EXCLUSIONS: dict[str, list[str]] = {
    DietaryStyle.VEGAN: [
        "meat", "beef", "pork", "chicken", "lamb", "turkey", "bacon",
        "fish", "shrimp", "lobster", "crab", "milk", "dairy", "cheese",
        "butter", "cream", "egg", "eggs", "honey", "gelatin",
    ],
    DietaryStyle.VEGETARIAN: [
        "meat", "beef", "pork", "chicken", "lamb", "turkey", "bacon",
        "fish", "shrimp", "lobster", "crab", "anchovies", "gelatin",
    ],
    DietaryStyle.PESCATARIAN: [
        "beef", "pork", "chicken", "lamb", "turkey", "bacon",
    ],
    DietaryStyle.HALAL: [
        "pork", "bacon", "lard", "ham", "alcohol", "wine", "beer", "liquor",
    ],
    DietaryStyle.KOSHER: [
        "pork", "bacon", "ham", "lard", "shellfish", "shrimp", "lobster", "crab",
    ],
    DietaryStyle.KETO: [
        "sugar", "bread", "pasta", "rice", "potato", "corn",
        "flour", "cake", "cookie", "honey", "syrup",
    ],
    DietaryStyle.PALEO: [
        "dairy", "milk", "cheese", "butter", "grain", "wheat", "rice",
        "pasta", "bread", "legume", "bean", "peanut", "sugar", "soy",
    ],
}


async def search_restaurants(
    preferences: UserPreferences,
    limit: int = 10,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> list[RestaurantMatch]:
    if not YELP_API_KEY:
        return _mock_restaurants(preferences, limit)
    raw = await _yelp_search(preferences, limit * 2, latitude, longitude)
    matches = []
    for r in raw:
        match = await _build_restaurant_match(r, preferences)
        if match:
            matches.append(match)
    if not matches and latitude is not None and longitude is not None:
        return await search_restaurants_overpass(preferences, latitude, longitude, limit=limit)
    matches.sort(key=lambda x: x.match_score, reverse=True)
    return matches[:limit]


async def _yelp_search(
    preferences: UserPreferences,
    limit: int,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> list[dict]:
    location = preferences.location or "San Francisco, CA"
    categories = _build_yelp_categories(preferences)
    params: dict = {
        "limit": min(limit, 50),
        "sort_by": "best_match",
        "open_now": preferences.requires_open_now,
    }
    if latitude is not None and longitude is not None:
        params["latitude"] = latitude
        params["longitude"] = longitude
    else:
        params["location"] = location
    if categories:
        params["categories"] = ",".join(categories)

    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{YELP_API_BASE}/businesses/search",
            headers={"Authorization": f"Bearer {YELP_API_KEY}"},
            params=params,
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json().get("businesses", [])


async def _build_restaurant_match(
    raw: dict, preferences: UserPreferences
) -> Optional[RestaurantMatch]:
    location_data = raw.get("location", {})
    address = ", ".join(filter(None, [
        location_data.get("address1"),
        location_data.get("city"),
        location_data.get("state"),
        location_data.get("zip_code"),
    ]))
    categories = [c.get("title", "") for c in raw.get("categories", [])]
    menu_items = await _fetch_menu_items(raw.get("id", ""), categories)

    allergen_report = None
    safe_items = []
    if preferences.allergens and menu_items:
        raw_items = [{"name": item.name, "ingredients": item.ingredients} for item in menu_items]
        scored = score_restaurant_allergen_safety(preferences.allergens, raw_items)
        unsafe = [r for r in scored["item_results"] if r.overall_risk == RiskLevel.UNSAFE]
        high_risk = [r for r in scored["item_results"] if r.overall_risk == RiskLevel.HIGH_RISK]
        safe_results = [r for r in scored["item_results"] if r.is_safe]
        safe_items = [item for item in menu_items if any(s.dish_name == item.name for s in safe_results)]
        warnings = []
        if unsafe:
            warnings.append(f"{len(unsafe)} menu items contain your allergens")
        if high_risk:
            warnings.append(f"{len(high_risk)} items have cross-contamination risk")
        allergen_report = AllergenSafetyReport(
            overall_risk=scored["risk_counts"],
            is_safe=scored["safety_score"] >= 60,
            safety_score=scored["safety_score"],
            unsafe_items=[r.dish_name for r in unsafe],
            high_risk_items=[r.dish_name for r in high_risk],
            safe_item_count=scored["safe_items"],
            total_item_count=scored["total_items"],
            warnings=warnings,
        )

    dietary_report = _check_dietary_compatibility(preferences, categories, menu_items)
    score, reasons = _compute_match_score(raw, preferences, allergen_report, dietary_report)

    if preferences.allergens and allergen_report and allergen_report.safety_score < 20:
        return None

    distance = raw.get("distance")
    distance_miles = round(distance / 1609.34, 2) if distance else None

    return RestaurantMatch(
        yelp_id=raw.get("id", ""),
        name=raw.get("name", ""),
        rating=raw.get("rating", 0.0),
        review_count=raw.get("review_count", 0),
        price_range=raw.get("price"),
        cuisine_types=categories,
        address=address,
        distance_miles=distance_miles,
        phone=raw.get("display_phone"),
        url=raw.get("url"),
        is_open_now=not raw.get("is_closed", True),
        image_url=raw.get("image_url"),
        allergen_safety=allergen_report,
        dietary_compatibility=dietary_report,
        safe_menu_items=safe_items[:10],
        match_score=score,
        match_reasons=reasons,
        warnings=allergen_report.warnings if allergen_report else [],
    )


def _check_dietary_compatibility(
    preferences: UserPreferences,
    restaurant_categories: list[str],
    menu_items: list[MenuItem],
) -> DietaryCompatibilityReport:
    compatible = []
    incompatible = []
    disliked_found = []
    notes = []

    ingredient_pool: list[str] = []
    for item in menu_items:
        ingredient_pool.extend([i.lower() for i in item.ingredients])
    ingredient_text = " ".join(ingredient_pool)

    for style in preferences.dietary_styles:
        exclusions = DIETARY_EXCLUSIONS.get(style, [])
        violations = [e for e in exclusions if e in ingredient_text]
        if violations:
            incompatible.append(style.value)
            notes.append(f"{style.value}: found {', '.join(violations[:3])}")
        else:
            compatible.append(style.value)

    for disliked in preferences.disliked_ingredients:
        if disliked.lower() in ingredient_text:
            disliked_found.append(disliked)

    preferred_cat_lower = [c.value for c in preferences.preferred_cuisines]
    cuisine_match = any(
        any(pref in cat.lower() for pref in preferred_cat_lower)
        for cat in restaurant_categories
    )

    return DietaryCompatibilityReport(
        is_compatible=len(incompatible) == 0,
        compatible_styles=compatible,
        incompatible_styles=incompatible,
        disliked_ingredients_found=disliked_found,
        preferred_cuisine_match=cuisine_match,
        notes=notes,
    )


def _compute_match_score(
    raw: dict,
    preferences: UserPreferences,
    allergen_report: Optional[AllergenSafetyReport],
    dietary_report: Optional[DietaryCompatibilityReport],
) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []

    rating = raw.get("rating", 0.0)
    score += (rating / 5.0) * 40
    reasons.append(f"Rated {rating}/5")

    if allergen_report:
        score += (allergen_report.safety_score / 100.0) * 30
        if allergen_report.safety_score >= 80:
            reasons.append(f"High allergen safety ({allergen_report.safety_score}%)")

    if dietary_report:
        if dietary_report.is_compatible:
            score += 15
            reasons.append("Matches your dietary style")
        if dietary_report.preferred_cuisine_match:
            score += 10
            reasons.append("Your preferred cuisine type")

    if preferences.preferred_price_range and raw.get("price") == preferences.preferred_price_range:
        score += 10
        reasons.append(f"Matches budget ({raw['price']})")

    if dietary_report and dietary_report.disliked_ingredients_found:
        score = max(0, score - len(dietary_report.disliked_ingredients_found) * 3)

    return round(min(score, 100), 1), reasons


def _build_yelp_categories(preferences: UserPreferences) -> list[str]:
    cats: list[str] = []
    for style in preferences.dietary_styles:
        cats.extend(DIETARY_STYLE_TO_YELP_CATEGORIES.get(style, []))
    for cuisine in preferences.preferred_cuisines:
        yelp_cat = CUISINE_TO_YELP.get(cuisine)
        if yelp_cat:
            cats.append(yelp_cat)
    return list(set(cats)) or ["restaurants"]


async def _fetch_menu_items(restaurant_id: str, categories: list[str]) -> list[MenuItem]:
    return _mock_menu_for_cuisine(categories)


def _mock_menu_for_cuisine(categories: list[str]) -> list[MenuItem]:
    cat_lower = " ".join(categories).lower()
    if "italian" in cat_lower:
        return [
            MenuItem(name="Spaghetti Carbonara", ingredients=["pasta", "eggs", "parmesan cheese", "pancetta", "black pepper"]),
            MenuItem(name="Margherita Pizza", ingredients=["wheat flour", "tomato sauce", "mozzarella cheese", "basil"]),
            MenuItem(name="Grilled Salmon", ingredients=["salmon", "lemon", "olive oil", "garlic"]),
            MenuItem(name="Caesar Salad", ingredients=["romaine lettuce", "parmesan", "croutons", "anchovies"]),
        ]
    if "japanese" in cat_lower or "sushi" in cat_lower:
        return [
            MenuItem(name="Salmon Sashimi", ingredients=["salmon", "soy sauce", "wasabi"]),
            MenuItem(name="Vegetable Tempura", ingredients=["broccoli", "sweet potato", "wheat flour", "egg"]),
            MenuItem(name="Miso Soup", ingredients=["miso paste", "tofu", "seaweed"]),
            MenuItem(name="Avocado Roll", ingredients=["rice", "nori", "avocado"]),
        ]
    if "mexican" in cat_lower:
        return [
            MenuItem(name="Bean Burrito", ingredients=["flour tortilla", "black beans", "rice", "cheese", "salsa"]),
            MenuItem(name="Chicken Tacos", ingredients=["corn tortilla", "grilled chicken", "onion", "cilantro"]),
            MenuItem(name="Guacamole", ingredients=["avocado", "lime", "onion", "cilantro", "jalapeño"]),
        ]
    return [
        MenuItem(name="Garden Salad", ingredients=["lettuce", "tomato", "cucumber", "olive oil"]),
        MenuItem(name="Grilled Chicken", ingredients=["chicken breast", "herbs", "olive oil"]),
        MenuItem(name="Veggie Burger", ingredients=["black bean patty", "wheat bun", "lettuce", "tomato"]),
    ]


def _mock_restaurants(preferences: UserPreferences, limit: int) -> list[RestaurantMatch]:
    mocks = [
        {"id": "mock-1", "name": "Green Bowl Café", "rating": 4.5, "review_count": 320,
         "categories": ["Vegan", "Salads", "Healthy"], "address": "123 Market St", "distance_miles": 0.4, "is_open_now": True},
        {"id": "mock-2", "name": "Tokyo Ramen House", "rating": 4.3, "review_count": 210,
         "categories": ["Japanese", "Ramen", "Noodles"], "address": "456 Mission St", "distance_miles": 0.8, "is_open_now": True},
        {"id": "mock-3", "name": "The Allergen-Free Kitchen", "rating": 4.7, "review_count": 180,
         "categories": ["Gluten-Free", "Vegan"], "address": "789 Valencia St", "distance_miles": 1.2, "is_open_now": True},
        {"id": "mock-4", "name": "Bella Italia", "rating": 4.1, "review_count": 450,
         "categories": ["Italian", "Pizza", "Pasta"], "address": "321 Columbus Ave", "distance_miles": 1.6, "is_open_now": False},
        {"id": "mock-5", "name": "Casa Mexico", "rating": 4.4, "review_count": 290,
         "categories": ["Mexican", "Tacos"], "address": "654 24th St", "distance_miles": 2.1, "is_open_now": True},
    ]
    results = []
    for m in mocks[:limit]:
        menu_items = _mock_menu_for_cuisine(m["categories"])
        raw_items = [{"name": i.name, "ingredients": i.ingredients} for i in menu_items]
        allergen_report = None
        safe_items = menu_items
        if preferences.allergens:
            scored = score_restaurant_allergen_safety(preferences.allergens, raw_items)
            safe_results = [r for r in scored["item_results"] if r.is_safe]
            safe_items = [i for i in menu_items if any(s.dish_name == i.name for s in safe_results)]
            unsafe = [r for r in scored["item_results"] if r.overall_risk == RiskLevel.UNSAFE]
            high_risk = [r for r in scored["item_results"] if r.overall_risk == RiskLevel.HIGH_RISK]
            allergen_report = AllergenSafetyReport(
                overall_risk="MIXED", is_safe=scored["safety_score"] >= 60,
                safety_score=scored["safety_score"],
                unsafe_items=[r.dish_name for r in unsafe],
                high_risk_items=[r.dish_name for r in high_risk],
                safe_item_count=scored["safe_items"],
                total_item_count=scored["total_items"],
                warnings=[f"{len(unsafe)} items contain your allergens"] if unsafe else [],
            )
        dietary_report = _check_dietary_compatibility(preferences, m["categories"], menu_items)
        score_val = (m["rating"] / 5.0) * 40
        if allergen_report:
            score_val += (allergen_report.safety_score / 100.0) * 30
        if dietary_report.is_compatible:
            score_val += 15
        if dietary_report.preferred_cuisine_match:
            score_val += 10
        results.append(RestaurantMatch(
            yelp_id=m["id"], name=m["name"], rating=m["rating"],
            review_count=m["review_count"], cuisine_types=m["categories"],
            address=m["address"], distance_miles=m["distance_miles"],
            is_open_now=m["is_open_now"],
            allergen_safety=allergen_report, dietary_compatibility=dietary_report,
            safe_menu_items=safe_items[:5],
            match_score=round(min(score_val, 100), 1),
            match_reasons=[f"Rated {m['rating']}/5"],
            warnings=allergen_report.warnings if allergen_report else [],
        ))
    results.sort(key=lambda x: x.match_score, reverse=True)
    return results


async def search_restaurants_overpass(
    preferences: UserPreferences,
    latitude: float,
    longitude: float,
    radius_m: int = 2000,
    limit: int = 50,
) -> list[RestaurantMatch]:
    overpass_url = "https://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
    (
      node(around:{radius_m},{latitude},{longitude})["amenity"="restaurant"];
      way(around:{radius_m},{latitude},{longitude})["amenity"="restaurant"];
      relation(around:{radius_m},{latitude},{longitude})["amenity"="restaurant"];
    );
    out center tags;
    """
    async with httpx.AsyncClient(headers={"User-Agent": "DietMate67/1.0"}) as client:
        resp = await client.post(overpass_url, data={"data": query}, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()

    matches: list[RestaurantMatch] = []
    for el in data.get("elements", []):
        tags = el.get("tags", {}) or {}
        if el.get("type") == "node":
            lat, lon = el.get("lat"), el.get("lon")
        else:
            center = el.get("center", {})
            lat, lon = center.get("lat"), center.get("lon")
        if lat is None or lon is None:
            continue

        distance_m = _haversine(latitude, longitude, lat, lon)
        distance_miles = round(distance_m / 1609.34, 2)
        name = tags.get("name") or "Unnamed"
        cuisines = [c.strip() for c in (tags.get("cuisine", "") or "").split(";") if c.strip()]

        info_score = sum([
            bool(tags.get("opening_hours")) * 10,
            bool(tags.get("phone") or tags.get("contact:phone")) * 10,
            bool(tags.get("website") or tags.get("contact:website")) * 10,
        ])
        pref_cuisines_lower = [c.value for c in preferences.preferred_cuisines]
        cuisine_match = any(any(pc in c.lower() for c in cuisines) for pc in pref_cuisines_lower)
        if cuisine_match:
            info_score += 20
        prox_score = max(0, (1 - distance_m / max(radius_m, 1)) * 50)
        match_score = round(min(info_score + prox_score, 100), 1)

        address_parts = [tags.get(k) for k in
                         ("addr:housenumber", "addr:street", "addr:city", "addr:state") if tags.get(k)]
        matches.append(RestaurantMatch(
            yelp_id=f"osm-{el.get('type')}-{el.get('id')}",
            name=name, rating=0.0, review_count=0,
            cuisine_types=cuisines, address=", ".join(address_parts),
            latitude=lat, longitude=lon, distance_miles=distance_miles,
            phone=tags.get("phone") or tags.get("contact:phone"),
            url=tags.get("website") or tags.get("contact:website"),
            is_open_now=None, image_url=None,
            allergen_safety=None, dietary_compatibility=None, safe_menu_items=[],
            match_score=match_score,
            match_reasons=["Cuisine matches preference" if cuisine_match else f"{distance_miles} mi away"],
            warnings=[],
        ))

    matches.sort(key=lambda x: (-x.match_score, x.distance_miles or 9999))
    return matches[:limit]


# Google Places "serves_*" fields and their human-readable label
_SERVES_FIELDS = {
    "serves_beer": "serves beer/alcohol",
    "serves_wine": "serves wine/alcohol",
    "serves_breakfast": "serves breakfast",
    "serves_brunch": "serves brunch",
    "serves_dinner": "serves dinner",
    "serves_lunch": "serves lunch",
    "serves_vegetarian_food": "has vegetarian options",
    "dine_in": "dine-in available",
    "takeout": "takeout available",
    "delivery": "delivery available",
}


async def search_restaurants_google(
    preferences: UserPreferences,
    latitude: float,
    longitude: float,
    radius_m: int = 2000,
    limit: int = 50,
) -> list[RestaurantMatch]:
    """Query Google Places Nearby + Details, score with AI preference analysis."""
    if not GOOGLE_API_KEY:
        return []

    places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    details_url = "https://maps.googleapis.com/maps/api/place/details/json"

    nearby_params: dict = {
        "key": GOOGLE_API_KEY,
        "location": f"{latitude},{longitude}",
        "radius": radius_m,
        "type": "restaurant",
    }
    if preferences.preferred_cuisines:
        nearby_params["keyword"] = " ".join(c.value for c in preferences.preferred_cuisines)

    async with httpx.AsyncClient() as client:
        resp = await client.get(places_url, params=nearby_params, timeout=15.0)
        resp.raise_for_status()
        results = resp.json().get("results", [])

        enrich_limit = min(len(results), limit, 20)
        detail_tasks = [
            client.get(
                details_url,
                params={
                    "place_id": p["place_id"],
                    "key": GOOGLE_API_KEY,
                    "fields": (
                        "name,formatted_address,geometry,formatted_phone_number,"
                        "website,opening_hours,rating,user_ratings_total,types,"
                        "reviews,price_level,editorial_summary,"
                        "dine_in,takeout,delivery,serves_beer,serves_breakfast,"
                        "serves_brunch,serves_dinner,serves_lunch,"
                        "serves_vegetarian_food,serves_wine"
                    ),
                },
                timeout=10.0,
            )
            for p in results[:enrich_limit]
        ]
        detail_responses = await asyncio.gather(*detail_tasks, return_exceptions=True)

    # Build intermediate list with all enriched data
    intermediate = []
    for idx, item in enumerate(results[:limit]):
        loc = item.get("geometry", {}).get("location", {})
        lat = loc.get("lat")
        lon = loc.get("lng")
        name = item.get("name") or "Unknown"
        vicinity = item.get("vicinity") or ""
        rating = item.get("rating") or 0.0
        user_ratings = item.get("user_ratings_total") or 0
        types = item.get("types") or []
        website = phone = opening_hours = editorial = None
        reviews_raw: list[dict] = []
        serves_info: list[str] = []

        if idx < enrich_limit:
            dr = detail_responses[idx]
            detail = {} if isinstance(dr, Exception) else dr.json().get("result", {})
            website = detail.get("website")
            phone = detail.get("formatted_phone_number")
            opening_hours = detail.get("opening_hours")
            editorial = (detail.get("editorial_summary") or {}).get("overview")
            reviews_raw = detail.get("reviews") or []
            if detail.get("rating"):
                rating = detail["rating"]
            if detail.get("user_ratings_total"):
                user_ratings = detail["user_ratings_total"]
            if detail.get("types"):
                types = detail["types"]
            # Extract serves_* attributes
            for field, label in _SERVES_FIELDS.items():
                if detail.get(field) is True:
                    serves_info.append(label)

        distance_m = _haversine(latitude, longitude, lat, lon) if lat and lon else None
        distance_miles = round(distance_m / 1609.34, 2) if distance_m else None

        # Clean up overly generic Google types
        skip_tags = {"point_of_interest", "establishment", "food"}
        cuisines = [t.replace("_", " ") for t in types if t not in skip_tags]

        # Pre-compute name-based food hints
        name_hints = _infer_food_from_name(name)

        review_texts = [r.get("text", "") for r in reviews_raw if r.get("text")]
        is_open_now: Optional[bool] = (opening_hours or {}).get("open_now")
        opening_hours_text: list[str] = (opening_hours or {}).get("weekday_text") or []

        intermediate.append({
            "place_id": item.get("place_id", ""),
            "name": name,
            "address": vicinity,
            "rating": rating,
            "user_ratings": user_ratings,
            "cuisines": cuisines,
            "website": website,
            "phone": phone,
            "opening_hours": opening_hours,
            "opening_hours_text": opening_hours_text,
            "is_open_now": is_open_now,
            "editorial": editorial,
            "reviews_raw": reviews_raw,
            "review_texts": review_texts,
            "lat": lat,
            "lon": lon,
            "distance_miles": distance_miles,
            "name_hints": name_hints,
            "serves_info": serves_info,
        })

    # Parallel Claude analysis
    analysis_tasks = [
        _analyze_restaurant(
            r["name"], r["cuisines"], r["editorial"], r["review_texts"],
            preferences, r["name_hints"], r["serves_info"],
        )
        for r in intermediate
    ]
    analyses = list(await asyncio.gather(*analysis_tasks))

    has_prefs = bool(
        preferences.dietary_styles or preferences.allergens
        or preferences.liked_ingredients or preferences.disliked_ingredients
        or preferences.preferred_cuisines or preferences.disliked_cuisines
    )

    matches: list[RestaurantMatch] = []
    for r, analysis in zip(intermediate, analyses):
        food_types: list[str] = analysis.get("food_types") or r["cuisines"]
        ai_note: str = analysis.get("dietary_note") or ""
        fits_diet = analysis.get("fits_diet")
        liked_matches: list[str] = list(analysis.get("liked_matches") or [])
        allergen_hits: list[str] = list(analysis.get("allergen_hits") or [])
        disliked_hits: list[str] = list(analysis.get("disliked_hits") or [])

        # ── Deterministic fallback ────────────────────────────────────────────
        # Scan food_types + cuisines + name + name_hints + serves_info.
        # name_hints are the KEY addition: "Dairy Queen" → includes "ice cream"
        # so disliked "ice cream" will be caught even if reviews didn't mention it.
        food_context = " ".join(
            food_types + r["cuisines"] + [r["name"]] + r["name_hints"] + r["serves_info"]
        ).lower()

        for item in preferences.disliked_ingredients:
            if item.lower() in food_context and item not in disliked_hits:
                disliked_hits.append(item)
                if fits_diet is True:
                    fits_diet = None

        # If the disliked item is a PRIMARY food of this restaurant (appears in name_hints),
        # it's not just "has some dishes we dislike" — it IS that food. Force fits_diet=False.
        if disliked_hits and r["name_hints"]:
            name_hint_text = " ".join(r["name_hints"]).lower()
            for item in disliked_hits:
                if item.lower() in name_hint_text:
                    fits_diet = False
                    break

        for item in preferences.allergens:
            if item.lower() in food_context and item not in allergen_hits:
                allergen_hits.append(item)
                fits_diet = False

        for item in preferences.liked_ingredients:
            if item.lower() in food_context and item not in liked_matches:
                liked_matches.append(item)
        # ─────────────────────────────────────────────────────────────────────

        # ── Scoring ──────────────────────────────────────────────────────────
        rating_pts = (r["rating"] / 5.0) * 25 if r["rating"] else 0

        if r["distance_miles"] is not None:
            dist_pts = max(0, (1 - r["distance_miles"] / (radius_m / 1609.34)) * 15)
        else:
            dist_pts = 0

        if has_prefs:
            if fits_diet is True:
                diet_pts = 50
            elif fits_diet is False:
                diet_pts = 0
            else:
                diet_pts = 20

            diet_pts += min(18, len(liked_matches) * 6)
            diet_pts -= len(allergen_hits) * 20
            diet_pts -= len(disliked_hits) * 12

            food_lower = " ".join(food_types + r["name_hints"]).lower()
            pref_cuisines = [c.value.lower() for c in preferences.preferred_cuisines]
            disliked_cuisines = [c.value.lower() for c in preferences.disliked_cuisines]
            if any(c in food_lower for c in pref_cuisines):
                diet_pts += 10
            if any(c in food_lower for c in disliked_cuisines):
                diet_pts -= 10
        else:
            diet_pts = 10

        info_pts = sum([
            bool(r["website"]) * 4,
            bool(r["phone"]) * 3,
            bool(r["opening_hours"]) * 3,
        ])

        total = rating_pts + dist_pts + diet_pts + info_pts
        score = round(max(0, min(100, total)), 1)
        # ─────────────────────────────────────────────────────────────────────

        reasons: list[str] = []
        if r["rating"]:
            reasons.append(f"Rated {r['rating']}/5 ({r['user_ratings']} reviews)")
        if r["distance_miles"] is not None:
            reasons.append(f"{r['distance_miles']} miles away")
        if liked_matches:
            reasons.append(f"Serves: {', '.join(liked_matches)}")
        if r["editorial"]:
            reasons.append(r["editorial"])

        warnings: list[str] = []
        if allergen_hits:
            warnings.append(f"⚠️ May contain your allergens: {', '.join(allergen_hits)}")
        if disliked_hits:
            warnings.append(f"👎 Contains items you dislike: {', '.join(disliked_hits)}")

        # Combine name_hints + AI food_types for display (deduplicated)
        display_food_types = list(dict.fromkeys(food_types + r["name_hints"]))

        matches.append(RestaurantMatch(
            yelp_id=f"g-{r['place_id']}",
            name=r["name"],
            rating=r["rating"],
            review_count=r["user_ratings"],
            price_range=None,
            cuisine_types=r["cuisines"],
            address=r["address"],
            latitude=r["lat"],
            longitude=r["lon"],
            distance_miles=r["distance_miles"],
            phone=r["phone"],
            url=r["website"],
            is_open_now=r["is_open_now"],
            image_url=None,
            allergen_safety=None,
            dietary_compatibility=None,
            safe_menu_items=[],
            match_score=score,
            match_reasons=reasons,
            warnings=warnings,
            google_reviews=r["reviews_raw"],
            food_types=display_food_types,
            ai_dietary_note=ai_note,
            fits_diet=fits_diet,
        ))

    # Apply open-now filter if user requires it
    if preferences.requires_open_now:
        matches = [m for m in matches if m.is_open_now is not False]

    matches.sort(key=lambda x: (-x.match_score, x.distance_miles or 9999))
    return matches[:limit]
