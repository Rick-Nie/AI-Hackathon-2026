"""
Restaurant search and dietary matching logic.
Uses Google Places Text Search API for restaurant data. Falls back to mock data if no API key.
"""

import os
import math
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

GOOGLE_PLACES_TEXTSEARCH = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GOOGLE_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")

# Keywords we can append to a Google text search query for dietary styles
DIETARY_STYLE_KEYWORDS: dict[str, list[str]] = {
    DietaryStyle.VEGAN: ["vegan"],
    DietaryStyle.VEGETARIAN: ["vegetarian"],
    DietaryStyle.HALAL: ["halal"],
    DietaryStyle.KOSHER: ["kosher"],
}

# Map CuisineType to simple keywords used in Google text search queries
CUISINE_TO_KEYWORD: dict[str, str] = {
    CuisineType.ITALIAN: "italian",
    CuisineType.CHINESE: "chinese",
    CuisineType.JAPANESE: "japanese",
    CuisineType.MEXICAN: "mexican",
    CuisineType.INDIAN: "indian",
    CuisineType.THAI: "thai",
    CuisineType.MEDITERRANEAN: "mediterranean",
    CuisineType.AMERICAN: "american",
    CuisineType.FRENCH: "french",
    CuisineType.KOREAN: "korean",
    CuisineType.VIETNAMESE: "vietnamese",
    CuisineType.GREEK: "greek",
    CuisineType.MIDDLE_EASTERN: "middle eastern",
    CuisineType.ETHIOPIAN: "ethiopian",
}

# Dietary style incompatible ingredients (for menu-level checking)
DIETARY_EXCLUSIONS: dict[str, list[str]] = {
    DietaryStyle.VEGAN: [
        "meat", "beef", "pork", "chicken", "lamb", "turkey", "bacon", "prosciutto",
        "fish", "shrimp", "lobster", "crab", "milk", "dairy", "cheese", "butter",
        "cream", "egg", "eggs", "honey", "gelatin",
    ],
    DietaryStyle.VEGETARIAN: [
        "meat", "beef", "pork", "chicken", "lamb", "turkey", "bacon", "prosciutto",
        "fish", "shrimp", "lobster", "crab", "anchovies", "gelatin",
    ],
    DietaryStyle.PESCATARIAN: [
        "beef", "pork", "chicken", "lamb", "turkey", "bacon", "prosciutto",
    ],
    DietaryStyle.HALAL: [
        "pork", "bacon", "lard", "ham", "prosciutto", "pancetta",
        "alcohol", "wine", "beer", "liquor",
    ],
    DietaryStyle.KOSHER: [
        "pork", "bacon", "ham", "lard", "shellfish", "shrimp", "lobster", "crab",
    ],
    DietaryStyle.KETO: [
        "sugar", "bread", "pasta", "rice", "potato", "corn", "oats",
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
) -> list[RestaurantMatch]:
    """Search restaurants (Google Places) and return matched + scored restaurants."""
    if not GOOGLE_API_KEY:
        return _mock_restaurants(preferences, limit)

    raw = await _google_text_search(preferences, limit * 2)  # fetch extra to allow filtering
    matches = []
    for r in raw:
        match = await _build_restaurant_match(r, preferences)
        if match:
            matches.append(match)

    matches.sort(key=lambda x: x.match_score, reverse=True)
    return matches[:limit]


async def _google_text_search(preferences: UserPreferences, limit: int) -> list[dict]:
    """Use Google Places Text Search to find restaurants matching keywords.

    Returns a list of Google place result dicts (as returned by the API).
    """
    location = preferences.location or "San Francisco, CA"
    query_parts = [f"restaurants in {location}"]

    # Add dietary style keywords
    for style in preferences.dietary_styles:
        kws = DIETARY_STYLE_KEYWORDS.get(style, [])
        query_parts.extend(kws)

    # Add cuisine keywords
    for cuisine in preferences.preferred_cuisines:
        kw = CUISINE_TO_KEYWORD.get(cuisine)
        if kw:
            query_parts.append(kw)

    # Add avoid/allergen keywords as negative hints (we'll still deterministically check allergens later)
    # Google Text Search doesn't support negative operators reliably, so we just include them for context.
    if preferences.preferred_price_range:
        query_parts.append(f"price {preferences.preferred_price_range}")

    query = " ".join(query_parts)

    params = {"query": query, "key": GOOGLE_API_KEY}

    async with httpx.AsyncClient() as client:
        resp = await client.get(GOOGLE_PLACES_TEXTSEARCH, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        # Truncate to requested limit
        return results[: min(limit, len(results))]


async def _build_restaurant_match(
    raw: dict, preferences: UserPreferences
) -> Optional[RestaurantMatch]:
    # Google Places result structure
    address = raw.get("formatted_address") or ""
    categories = raw.get("types", [])

    # Fetch menu details if available (external menu providers may be needed)
    menu_items = await _fetch_menu_items(raw.get("place_id", ""), categories)

    # Allergen safety analysis (deterministic)
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

    # Dietary compatibility
    dietary_report = _check_dietary_compatibility(preferences, categories, menu_items)

    # Scoring
    score, reasons = _compute_match_score(raw, preferences, allergen_report, dietary_report)

    # Filter out restaurants that are clearly unsafe for allergen users
    if preferences.allergens and allergen_report and allergen_report.safety_score < 20:
        return None

    # Google provides geometry.location with lat/lng; distance calculation requires user geocode.
    distance_miles = None
    if raw.get("geometry") and raw["geometry"].get("location") and preferences.location is None:
        # if we had user's lat/lng we could compute distance; skip for now
        pass

    return RestaurantMatch(
        yelp_id=raw.get("place_id", ""),
        name=raw.get("name", ""),
        rating=raw.get("rating", 0.0),
        review_count=raw.get("user_ratings_total", 0),
        price_range=str(raw.get("price_level")) if raw.get("price_level") is not None else None,
        cuisine_types=categories,
        address=address,
        distance_miles=distance_miles,
        phone=None,
        url=raw.get("url"),
        is_open_now=raw.get("opening_hours", {}).get("open_now") if raw.get("opening_hours") else None,
        image_url=None,
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

    ingredient_pool = []
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

    is_compatible = len(incompatible) == 0

    return DietaryCompatibilityReport(
        is_compatible=is_compatible,
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

    # Base: rating (0-40 pts)
    rating = raw.get("rating", 0.0)
    score += (rating / 5.0) * 40
    reasons.append(f"Rated {rating}/5")

    # Allergen safety (0-30 pts)
    if allergen_report:
        safety_pts = (allergen_report.safety_score / 100.0) * 30
        score += safety_pts
        if allergen_report.safety_score >= 80:
            reasons.append(f"High allergen safety ({allergen_report.safety_score}%)")
        elif allergen_report.safety_score >= 60:
            reasons.append(f"Moderate allergen safety ({allergen_report.safety_score}%)")

    # Dietary compatibility (0-15 pts)
    if dietary_report:
        if dietary_report.is_compatible:
            score += 15
            reasons.append("Matches your dietary style")
        if dietary_report.preferred_cuisine_match:
            score += 10
            reasons.append("Your preferred cuisine type")

    # Price match (0-10 pts)
    if preferences.preferred_price_range and raw.get("price") == preferences.preferred_price_range:
        score += 10
        reasons.append(f"Matches budget ({raw['price']})")

    # Disliked ingredients penalty
    if dietary_report and dietary_report.disliked_ingredients_found:
        penalty = len(dietary_report.disliked_ingredients_found) * 3
        score = max(0, score - penalty)

    return round(min(score, 100), 1), reasons


# Legacy category builder removed; Google Text Search builds queries inline.


async def _fetch_menu_items(restaurant_id: str, categories: list[str]) -> list[MenuItem]:
    """
    In a real implementation this would call a menu API (e.g., Place Details, Locu, SinglePlatform).
    For now we return realistic mock items based on cuisine type.
    """
    return _mock_menu_for_cuisine(categories)


def _mock_menu_for_cuisine(categories: list[str]) -> list[MenuItem]:
    cat_lower = " ".join(categories).lower()
    if "italian" in cat_lower:
        return [
            MenuItem(name="Spaghetti Carbonara", ingredients=["pasta", "eggs", "parmesan cheese", "pancetta", "black pepper"]),
            MenuItem(name="Margherita Pizza", ingredients=["wheat flour", "tomato sauce", "mozzarella cheese", "basil"]),
            MenuItem(name="Grilled Salmon", ingredients=["salmon", "lemon", "olive oil", "garlic", "herbs"]),
            MenuItem(name="Bruschetta", ingredients=["bread", "tomato", "garlic", "basil", "olive oil"]),
            MenuItem(name="Caesar Salad", ingredients=["romaine lettuce", "parmesan", "croutons", "caesar dressing", "anchovies"]),
        ]
    if "japanese" in cat_lower or "sushi" in cat_lower:
        return [
            MenuItem(name="Salmon Sashimi", ingredients=["salmon", "soy sauce", "wasabi", "ginger"]),
            MenuItem(name="Vegetable Tempura", ingredients=["broccoli", "sweet potato", "zucchini", "wheat flour", "egg", "sesame oil"]),
            MenuItem(name="Miso Soup", ingredients=["miso paste", "tofu", "seaweed", "scallion", "dashi"]),
            MenuItem(name="Edamame", ingredients=["edamame", "sea salt"]),
            MenuItem(name="Avocado Roll", ingredients=["rice", "nori", "avocado", "sesame seeds"]),
        ]
    if "mexican" in cat_lower:
        return [
            MenuItem(name="Bean Burrito", ingredients=["flour tortilla", "black beans", "rice", "cheese", "sour cream", "salsa"]),
            MenuItem(name="Chicken Tacos", ingredients=["corn tortilla", "grilled chicken", "onion", "cilantro", "lime"]),
            MenuItem(name="Guacamole", ingredients=["avocado", "lime", "onion", "cilantro", "jalapeño", "tomato"]),
            MenuItem(name="Fish Tacos", ingredients=["corn tortilla", "tilapia", "cabbage", "pico de gallo", "crema"]),
        ]
    # Default generic menu
    return [
        MenuItem(name="Garden Salad", ingredients=["lettuce", "tomato", "cucumber", "carrot", "olive oil", "vinegar"]),
        MenuItem(name="Grilled Chicken", ingredients=["chicken breast", "herbs", "olive oil", "garlic"]),
        MenuItem(name="Veggie Burger", ingredients=["black bean patty", "wheat bun", "lettuce", "tomato", "onion"]),
        MenuItem(name="Pasta Primavera", ingredients=["pasta", "vegetables", "olive oil", "garlic", "parmesan"]),
    ]


def _mock_restaurants(preferences: UserPreferences, limit: int) -> list[RestaurantMatch]:
    """Returns mock restaurant data when no Google Places API key is configured."""
    from models import AllergenSafetyReport, DietaryCompatibilityReport

    mocks = [
        {
            "id": "mock-1", "name": "Green Bowl Café", "rating": 4.5, "review_count": 320,
            "price": "$$", "categories": ["Vegan", "Salads", "Healthy"],
            "address": "123 Market St, San Francisco, CA",
            "distance_miles": 0.4, "is_open_now": True,
        },
        {
            "id": "mock-2", "name": "Tokyo Ramen House", "rating": 4.3, "review_count": 210,
            "price": "$$", "categories": ["Japanese", "Ramen", "Noodles"],
            "address": "456 Mission St, San Francisco, CA",
            "distance_miles": 0.8, "is_open_now": True,
        },
        {
            "id": "mock-3", "name": "The Allergen-Free Kitchen", "rating": 4.7, "review_count": 180,
            "price": "$$$", "categories": ["Gluten-Free", "Vegan", "American"],
            "address": "789 Valencia St, San Francisco, CA",
            "distance_miles": 1.2, "is_open_now": True,
        },
        {
            "id": "mock-4", "name": "Bella Italia", "rating": 4.1, "review_count": 450,
            "price": "$$$", "categories": ["Italian", "Pizza", "Pasta"],
            "address": "321 Columbus Ave, San Francisco, CA",
            "distance_miles": 1.6, "is_open_now": False,
        },
        {
            "id": "mock-5", "name": "Casa Mexico", "rating": 4.4, "review_count": 290,
            "price": "$", "categories": ["Mexican", "Tacos", "Burritos"],
            "address": "654 24th St, San Francisco, CA",
            "distance_miles": 2.1, "is_open_now": True,
        },
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
                overall_risk="MIXED",
                is_safe=scored["safety_score"] >= 60,
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
            yelp_id=m["id"],
            name=m["name"],
            rating=m["rating"],
            review_count=m["review_count"],
            price_range=m["price"],
            cuisine_types=m["categories"],
            address=m["address"],
            distance_miles=m["distance_miles"],
            is_open_now=m["is_open_now"],
            allergen_safety=allergen_report,
            dietary_compatibility=dietary_report,
            safe_menu_items=safe_items[:5],
            match_score=round(min(score_val, 100), 1),
            match_reasons=[f"Rated {m['rating']}/5", f"{len(safe_items)} safe menu items"],
            warnings=allergen_report.warnings if allergen_report else [],
        ))

    results.sort(key=lambda x: x.match_score, reverse=True)
    return results
