"""
Restaurant search using OpenStreetMap Overpass API (free, no key required).
Dietary/allergen analysis is deterministic — never LLM-based.
"""

import httpx
import math
from typing import Optional

from allergens import score_restaurant_allergen_safety, RiskLevel
from models import (
    UserPreferences,
    RestaurantMatch,
    MenuItem,
    AllergenSafetyReport,
    DietaryCompatibilityReport,
    DietaryStyle,
    CuisineType,
)

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

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

# OSM cuisine tag → our CuisineType
OSM_CUISINE_MAP: dict[str, CuisineType] = {
    "italian": CuisineType.ITALIAN,
    "pizza": CuisineType.ITALIAN,
    "chinese": CuisineType.CHINESE,
    "japanese": CuisineType.JAPANESE,
    "sushi": CuisineType.JAPANESE,
    "ramen": CuisineType.JAPANESE,
    "mexican": CuisineType.MEXICAN,
    "indian": CuisineType.INDIAN,
    "thai": CuisineType.THAI,
    "mediterranean": CuisineType.MEDITERRANEAN,
    "american": CuisineType.AMERICAN,
    "burger": CuisineType.AMERICAN,
    "french": CuisineType.FRENCH,
    "korean": CuisineType.KOREAN,
    "vietnamese": CuisineType.VIETNAMESE,
    "greek": CuisineType.GREEK,
    "middle_eastern": CuisineType.MIDDLE_EASTERN,
    "lebanese": CuisineType.MIDDLE_EASTERN,
    "turkish": CuisineType.MIDDLE_EASTERN,
    "ethiopian": CuisineType.ETHIOPIAN,
}


async def geocode_location(location: str) -> Optional[tuple[float, float]]:
    """Convert a location string to (lat, lon) using Nominatim."""
    async with httpx.AsyncClient(headers={"User-Agent": "DietMate/1.0"}) as client:
        resp = await client.get(
            NOMINATIM_URL,
            params={"q": location, "format": "json", "limit": 1},
            timeout=10.0,
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return None
        return float(results[0]["lat"]), float(results[0]["lon"])


async def overpass_restaurants(
    lat: float,
    lon: float,
    radius_meters: int = 2000,
    limit: int = 50,
) -> list[dict]:
    """Query OpenStreetMap Overpass API for restaurants near a coordinate."""
    query = f"""
[out:json][timeout:25];
(
  node["amenity"="restaurant"](around:{radius_meters},{lat},{lon});
  node["amenity"="cafe"](around:{radius_meters},{lat},{lon});
  node["amenity"="fast_food"](around:{radius_meters},{lat},{lon});
  way["amenity"="restaurant"](around:{radius_meters},{lat},{lon});
  way["amenity"="cafe"](around:{radius_meters},{lat},{lon});
);
out center {limit};
"""
    async with httpx.AsyncClient(headers={"User-Agent": "DietMate/1.0"}) as client:
        resp = await client.post(OVERPASS_URL, data={"data": query}, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        return data.get("elements", [])


def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 3958.8  # Earth radius in miles
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _osm_to_match(
    element: dict,
    user_lat: float,
    user_lon: float,
    preferences: UserPreferences,
) -> Optional[RestaurantMatch]:
    tags = element.get("tags", {})
    name = tags.get("name") or tags.get("brand")
    if not name:
        return None

    # Coordinates
    if element["type"] == "node":
        lat, lon = element.get("lat", 0.0), element.get("lon", 0.0)
    else:
        center = element.get("center", {})
        lat, lon = center.get("lat", 0.0), center.get("lon", 0.0)

    distance_miles = _haversine_miles(user_lat, user_lon, lat, lon)
    if distance_miles > preferences.max_distance_miles:
        return None

    # Build address
    address_parts = filter(None, [
        tags.get("addr:housenumber"),
        tags.get("addr:street"),
        tags.get("addr:city"),
        tags.get("addr:state"),
        tags.get("addr:postcode"),
    ])
    address = " ".join(address_parts) or f"Near ({lat:.4f}, {lon:.4f})"

    # Cuisine types
    raw_cuisine = tags.get("cuisine", "")
    cuisine_labels = [c.strip() for c in raw_cuisine.split(";") if c.strip()]
    cuisine_types = [c.replace("_", " ").title() for c in cuisine_labels]

    # OSM dietary tags → check compatibility
    osm_diet_tags = {
        "diet:vegan": tags.get("diet:vegan", ""),
        "diet:vegetarian": tags.get("diet:vegetarian", ""),
        "diet:halal": tags.get("diet:halal", ""),
        "diet:kosher": tags.get("diet:kosher", ""),
        "diet:gluten_free": tags.get("diet:gluten_free", ""),
    }

    # Get menu items based on cuisine (realistic mock — OSM has no menu data)
    menu_items = _mock_menu_for_cuisine(cuisine_labels)

    # Allergen safety (deterministic)
    allergen_report = None
    safe_items = menu_items
    if preferences.allergens:
        raw_items = [{"name": i.name, "ingredients": i.ingredients} for i in menu_items]
        scored = score_restaurant_allergen_safety(preferences.allergens, raw_items)
        safe_results = [r for r in scored["item_results"] if r.is_safe]
        safe_items = [i for i in menu_items if any(s.dish_name == i.name for s in safe_results)]
        unsafe = [r for r in scored["item_results"] if r.overall_risk == RiskLevel.UNSAFE]
        high_risk = [r for r in scored["item_results"] if r.overall_risk == RiskLevel.HIGH_RISK]

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

        # Filter out clearly unsafe restaurants
        if allergen_report.safety_score < 20:
            return None

    # Dietary compatibility
    dietary_report = _check_dietary_compatibility(
        preferences, cuisine_labels, menu_items, osm_diet_tags
    )

    # Match score
    score, reasons = _compute_match_score(
        name, distance_miles, preferences, allergen_report, dietary_report, tags
    )

    phone = tags.get("phone") or tags.get("contact:phone")
    website = tags.get("website") or tags.get("contact:website")

    return RestaurantMatch(
        yelp_id=f"osm-{element['type']}-{element['id']}",
        name=name,
        rating=0.0,  # OSM has no ratings
        review_count=0,
        price_range=_osm_price(tags.get("price_range") or tags.get("stars")),
        cuisine_types=cuisine_types,
        address=address,
        distance_miles=round(distance_miles, 2),
        phone=phone,
        url=website,
        is_open_now=None,  # would need opening_hours parsing
        allergen_safety=allergen_report,
        dietary_compatibility=dietary_report,
        safe_menu_items=safe_items[:8],
        match_score=score,
        match_reasons=reasons,
        warnings=allergen_report.warnings if allergen_report else [],
    )


def _osm_price(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    try:
        n = int(raw)
        return "$" * min(n, 4)
    except (ValueError, TypeError):
        return raw if raw in ("$", "$$", "$$$", "$$$$") else None


def _check_dietary_compatibility(
    preferences: UserPreferences,
    cuisine_labels: list[str],
    menu_items: list[MenuItem],
    osm_diet_tags: dict,
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
        # OSM diet tag takes priority
        osm_key = f"diet:{style.value}"
        osm_val = osm_diet_tags.get(osm_key, "")
        if osm_val in ("yes", "only"):
            compatible.append(style.value)
            notes.append(f"Restaurant tagged as {style.value}-friendly (OSM)")
            continue
        if osm_val == "no":
            incompatible.append(style.value)
            notes.append(f"Restaurant tagged as NOT {style.value}-friendly (OSM)")
            continue

        # Fall back to ingredient analysis
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

    # Cuisine preference match
    preferred_vals = [c.value for c in preferences.preferred_cuisines]
    cuisine_match = any(
        any(pref in label.lower() for pref in preferred_vals)
        for label in cuisine_labels
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
    name: str,
    distance_miles: float,
    preferences: UserPreferences,
    allergen_report: Optional[AllergenSafetyReport],
    dietary_report: Optional[DietaryCompatibilityReport],
    tags: dict,
) -> tuple[float, list[str]]:
    score = 0.0
    reasons = []

    # Distance score (0-30 pts): closer is better
    if distance_miles <= 0.5:
        score += 30
        reasons.append(f"{distance_miles:.1f} mi away (very close)")
    elif distance_miles <= 1.5:
        score += 20
        reasons.append(f"{distance_miles:.1f} mi away")
    elif distance_miles <= 3.0:
        score += 10
        reasons.append(f"{distance_miles:.1f} mi away")

    # Allergen safety (0-35 pts)
    if allergen_report:
        safety_pts = (allergen_report.safety_score / 100.0) * 35
        score += safety_pts
        label = (
            "High" if allergen_report.safety_score >= 80
            else "Moderate" if allergen_report.safety_score >= 60
            else "Low"
        )
        reasons.append(f"{label} allergen safety ({allergen_report.safety_score}%)")

    # Dietary compatibility (0-20 pts)
    if dietary_report:
        if dietary_report.is_compatible:
            score += 20
            reasons.append("Matches your dietary style")
        if dietary_report.preferred_cuisine_match:
            score += 10
            reasons.append("Your preferred cuisine type")

    # OSM quality signals (0-5 pts)
    if tags.get("website") or tags.get("contact:website"):
        score += 2
    if tags.get("phone") or tags.get("contact:phone"):
        score += 2
    if tags.get("opening_hours"):
        score += 1

    # Disliked ingredient penalty
    if dietary_report and dietary_report.disliked_ingredients_found:
        penalty = len(dietary_report.disliked_ingredients_found) * 3
        score = max(0, score - penalty)

    return round(min(score, 100), 1), reasons


def _mock_menu_for_cuisine(cuisine_labels: list[str]) -> list[MenuItem]:
    joined = " ".join(cuisine_labels).lower()
    if "italian" in joined or "pizza" in joined:
        return [
            MenuItem(name="Spaghetti Carbonara", ingredients=["pasta", "eggs", "parmesan cheese", "pancetta", "black pepper"]),
            MenuItem(name="Margherita Pizza", ingredients=["wheat flour", "tomato sauce", "mozzarella cheese", "basil"]),
            MenuItem(name="Grilled Salmon", ingredients=["salmon", "lemon", "olive oil", "garlic", "herbs"]),
            MenuItem(name="Bruschetta", ingredients=["bread", "tomato", "garlic", "basil", "olive oil"]),
            MenuItem(name="Caesar Salad", ingredients=["romaine lettuce", "parmesan", "croutons", "caesar dressing", "anchovies"]),
        ]
    if "japanese" in joined or "sushi" in joined or "ramen" in joined:
        return [
            MenuItem(name="Salmon Sashimi", ingredients=["salmon", "soy sauce", "wasabi", "ginger"]),
            MenuItem(name="Vegetable Tempura", ingredients=["broccoli", "sweet potato", "zucchini", "wheat flour", "egg", "sesame oil"]),
            MenuItem(name="Miso Soup", ingredients=["miso paste", "tofu", "seaweed", "scallion", "dashi"]),
            MenuItem(name="Edamame", ingredients=["edamame", "sea salt"]),
            MenuItem(name="Avocado Roll", ingredients=["rice", "nori", "avocado", "sesame seeds"]),
        ]
    if "mexican" in joined:
        return [
            MenuItem(name="Bean Burrito", ingredients=["flour tortilla", "black beans", "rice", "cheese", "sour cream", "salsa"]),
            MenuItem(name="Chicken Tacos", ingredients=["corn tortilla", "grilled chicken", "onion", "cilantro", "lime"]),
            MenuItem(name="Guacamole", ingredients=["avocado", "lime", "onion", "cilantro", "jalapeño", "tomato"]),
            MenuItem(name="Fish Tacos", ingredients=["corn tortilla", "tilapia", "cabbage", "pico de gallo", "crema"]),
        ]
    if "indian" in joined:
        return [
            MenuItem(name="Dal Tadka", ingredients=["lentils", "onion", "tomato", "garlic", "cumin", "ghee"]),
            MenuItem(name="Paneer Tikka", ingredients=["paneer", "yogurt", "spices", "bell pepper", "onion"]),
            MenuItem(name="Chana Masala", ingredients=["chickpeas", "onion", "tomato", "ginger", "garlic", "spices"]),
            MenuItem(name="Butter Chicken", ingredients=["chicken", "butter", "cream", "tomato", "spices"]),
            MenuItem(name="Garlic Naan", ingredients=["wheat flour", "yogurt", "garlic", "butter"]),
        ]
    if "chinese" in joined:
        return [
            MenuItem(name="Vegetable Stir Fry", ingredients=["broccoli", "bell pepper", "carrot", "soy sauce", "garlic", "sesame oil"]),
            MenuItem(name="Kung Pao Chicken", ingredients=["chicken", "peanuts", "chili", "soy sauce", "vinegar"]),
            MenuItem(name="Steamed Dumplings", ingredients=["wheat flour", "pork", "cabbage", "ginger", "sesame oil"]),
            MenuItem(name="Hot and Sour Soup", ingredients=["tofu", "egg", "mushroom", "vinegar", "white pepper"]),
        ]
    if "vegan" in joined or "vegetarian" in joined:
        return [
            MenuItem(name="Buddha Bowl", ingredients=["quinoa", "roasted vegetables", "chickpeas", "tahini", "lemon"]),
            MenuItem(name="Lentil Soup", ingredients=["lentils", "carrot", "celery", "onion", "cumin", "olive oil"]),
            MenuItem(name="Mushroom Burger", ingredients=["portobello mushroom", "whole wheat bun", "lettuce", "tomato", "avocado"]),
            MenuItem(name="Smoothie Bowl", ingredients=["banana", "berries", "oat milk", "granola", "chia seeds"]),
        ]
    # Generic fallback
    return [
        MenuItem(name="Garden Salad", ingredients=["lettuce", "tomato", "cucumber", "carrot", "olive oil", "vinegar"]),
        MenuItem(name="Grilled Chicken", ingredients=["chicken breast", "herbs", "olive oil", "garlic"]),
        MenuItem(name="Veggie Burger", ingredients=["black bean patty", "wheat bun", "lettuce", "tomato", "onion"]),
        MenuItem(name="Pasta Primavera", ingredients=["pasta", "vegetables", "olive oil", "garlic", "parmesan"]),
        MenuItem(name="Tomato Soup", ingredients=["tomato", "onion", "garlic", "basil", "cream"]),
    ]


async def search_restaurants(
    preferences: UserPreferences,
    limit: int = 10,
) -> list[RestaurantMatch]:
    """
    Search OpenStreetMap for nearby restaurants and score them against user preferences.
    Falls back to mock data if geocoding fails or no results found.
    """
    location = preferences.location or "San Francisco, CA"

    # Geocode
    coords = await geocode_location(location)
    if not coords:
        return _fallback_mock_restaurants(preferences, limit, location)

    user_lat, user_lon = coords
    radius_meters = int(preferences.max_distance_miles * 1609.34)

    # Fetch from OSM
    try:
        elements = await overpass_restaurants(user_lat, user_lon, radius_meters, limit=limit * 3)
    except Exception:
        return _fallback_mock_restaurants(preferences, limit, location)

    if not elements:
        return _fallback_mock_restaurants(preferences, limit, location)

    # Build and score matches
    matches = []
    for element in elements:
        match = _osm_to_match(element, user_lat, user_lon, preferences)
        if match:
            matches.append(match)

    matches.sort(key=lambda x: x.match_score, reverse=True)
    return matches[:limit]


def _fallback_mock_restaurants(
    preferences: UserPreferences, limit: int, location: str
) -> list[RestaurantMatch]:
    """Demo-quality mock data when OSM is unavailable."""
    mocks = [
        {"id": "mock-1", "name": "Green Bowl Café", "cuisines": ["vegan", "salads"], "address": f"123 Market St, {location}", "dist": 0.4},
        {"id": "mock-2", "name": "Tokyo Ramen House", "cuisines": ["japanese", "ramen"], "address": f"456 Mission St, {location}", "dist": 0.8},
        {"id": "mock-3", "name": "The Allergen-Free Kitchen", "cuisines": ["vegan", "american"], "address": f"789 Valencia St, {location}", "dist": 1.2},
        {"id": "mock-4", "name": "Bella Italia", "cuisines": ["italian", "pizza"], "address": f"321 Columbus Ave, {location}", "dist": 1.6},
        {"id": "mock-5", "name": "Casa Mexico", "cuisines": ["mexican"], "address": f"654 24th St, {location}", "dist": 2.1},
        {"id": "mock-6", "name": "Spice Garden", "cuisines": ["indian"], "address": f"99 Curry Lane, {location}", "dist": 2.4},
    ]

    results = []
    for m in mocks[:limit]:
        menu_items = _mock_menu_for_cuisine(m["cuisines"])
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
            if allergen_report.safety_score < 20:
                continue

        dietary_report = _check_dietary_compatibility(
            preferences, m["cuisines"], menu_items, {}
        )

        score_val = max(0.0, 30.0 - m["dist"] * 5)  # distance base
        if allergen_report:
            score_val += (allergen_report.safety_score / 100.0) * 35
        if dietary_report.is_compatible:
            score_val += 20
        if dietary_report.preferred_cuisine_match:
            score_val += 10

        results.append(RestaurantMatch(
            yelp_id=m["id"],
            name=m["name"],
            rating=0.0,
            review_count=0,
            cuisine_types=[c.replace("_", " ").title() for c in m["cuisines"]],
            address=m["address"],
            distance_miles=m["dist"],
            allergen_safety=allergen_report,
            dietary_compatibility=dietary_report,
            safe_menu_items=safe_items[:5],
            match_score=round(min(score_val, 100), 1),
            match_reasons=[f"{m['dist']} mi away", f"{len(safe_items)} safe menu items"],
            warnings=allergen_report.warnings if allergen_report else [],
        ))

    results.sort(key=lambda x: x.match_score, reverse=True)
    return results
