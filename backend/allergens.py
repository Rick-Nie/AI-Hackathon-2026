"""
Deterministic allergen rule engine.
All allergen safety decisions are made via explicit rules — never via LLM inference.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    LOW_RISK = "LOW_RISK"
    MODERATE_RISK = "MODERATE_RISK"
    HIGH_RISK = "HIGH_RISK"
    UNSAFE = "UNSAFE"


# FDA Big 9 allergens + common extras, with all known aliases/forms
ALLERGEN_KEYWORDS: dict[str, list[str]] = {
    "milk": [
        "milk", "dairy", "lactose", "butter", "cream", "cheese", "whey", "casein",
        "lactalbumin", "lactoglobulin", "ghee", "kefir", "yogurt", "yoghurt",
        "buttermilk", "half-and-half", "sour cream", "ice cream", "gelato",
        "custard", "pudding", "crème", "brie", "cheddar", "mozzarella", "parmesan",
        "ricotta", "gouda", "feta", "goat cheese", "condensed milk", "evaporated milk",
        "milk powder", "milk solids", "nonfat milk", "skim milk", "whole milk",
    ],
    "eggs": [
        "egg", "eggs", "albumin", "globulin", "lecithin (egg)", "lysozyme",
        "mayonnaise", "meringue", "ovalbumin", "ovomucin", "ovomucoid",
        "ovotransferrin", "ovovitellin", "silici albuminate", "surimi",
        "hollandaise", "aioli", "egg white", "egg yolk", "egg wash",
        "dried egg", "egg powder", "egg solids",
    ],
    "fish": [
        "fish", "cod", "salmon", "tuna", "tilapia", "bass", "flounder",
        "grouper", "haddock", "mahi", "mahi-mahi", "pollock", "snapper",
        "swordfish", "trout", "anchovy", "anchovies", "anchoveta", "herring",
        "catfish", "halibut", "pike", "sardine", "sole", "carp", "branzino",
        "sea bass", "rockfish", "mackerel", "fish sauce", "worcestershire",
        "caesar dressing", "caesar salad", "bonito", "dashi",
    ],
    "shellfish": [
        "shellfish", "shrimp", "crab", "lobster", "crayfish", "crawfish",
        "prawn", "clam", "scallop", "oyster", "mussel", "squid", "calamari",
        "octopus", "abalone", "barnacle", "cuttlefish", "langostino",
        "langoustine", "limpet", "periwinkle", "snail", "escargot",
        "sea urchin", "uni", "surimi", "imitation crab",
    ],
    "tree_nuts": [
        "tree nut", "almond", "cashew", "walnut", "pecan", "pistachio",
        "brazil nut", "hazelnut", "filbert", "macadamia", "pine nut", "pignoli",
        "coconut", "chestnut", "beechnut", "hickory nut", "lichee nut", "ginkgo",
        "praline", "marzipan", "nougat", "nut meal", "nut butter", "nut oil",
        "nut paste", "nut flour", "gianduja", "nutella",
    ],
    "peanuts": [
        "peanut", "peanuts", "groundnut", "groundnuts", "goober", "goobers",
        "earth nut", "mixed nuts", "peanut oil", "arachis oil", "peanut butter",
        "peanut flour", "peanut protein", "beer nuts", "monkey nuts",
    ],
    "wheat": [
        "wheat", "flour", "bread", "gluten", "semolina", "spelt", "kamut",
        "einkorn", "emmer", "farro", "triticale", "durum", "bulgur",
        "cracker", "pasta", "noodle", "couscous", "bran", "wheat germ",
        "wheat starch", "wheat bran", "wheat flour", "bread crumbs", "panko",
        "soy sauce", "teriyaki", "miso (wheat-based)",
    ],
    "soy": [
        "soy", "soya", "soybean", "tofu", "tempeh", "edamame", "miso",
        "natto", "soy sauce", "tamari", "shoyu", "textured vegetable protein",
        "tvp", "hydrolyzed soy", "soy milk", "soy flour", "soy protein",
        "soy isolate", "soy lecithin", "soy oil",
    ],
    "sesame": [
        "sesame", "tahini", "til", "gingelly", "benne", "sesame oil",
        "sesame seed", "sesame flour", "sesame paste",
    ],
    # Common non-FDA extras
    "gluten": [
        "gluten", "wheat", "barley", "rye", "malt", "brewer's yeast",
        "farro", "spelt", "kamut", "triticale", "semolina",
    ],
    "mustard": [
        "mustard", "mustard seed", "mustard oil", "mustard flour", "mustard leaf",
    ],
    "celery": [
        "celery", "celeriac", "celery seed", "celery salt", "celery oil",
    ],
    "lupin": [
        "lupin", "lupine", "lupin flour", "lupin seed", "lupin bean",
    ],
    "molluscs": [
        "mollusc", "mollusk", "snail", "squid", "octopus", "clam",
        "oyster", "mussel", "scallop", "abalone", "escargot",
    ],
    "sulphites": [
        "sulphite", "sulfite", "sulphur dioxide", "sulfur dioxide",
        "sodium bisulphite", "sodium bisulfite", "potassium bisulphite",
        "potassium bisulfite", "potassium metabisulphite",
    ],
}

# Cross-contamination risk: facilities that commonly share equipment
CROSS_CONTAMINATION_PAIRS: dict[str, list[str]] = {
    "peanuts": ["tree_nuts"],
    "tree_nuts": ["peanuts"],
    "wheat": ["gluten", "barley", "rye"],
    "gluten": ["wheat"],
    "fish": ["shellfish", "molluscs"],
    "shellfish": ["fish", "molluscs"],
    "molluscs": ["fish", "shellfish"],
    "milk": ["eggs"],
    "eggs": ["milk"],
}


@dataclass
class AllergenMatch:
    allergen: str
    matched_keyword: str
    risk_level: RiskLevel
    is_cross_contamination: bool = False
    note: str = ""


@dataclass
class DishSafetyResult:
    dish_name: str
    overall_risk: RiskLevel
    matches: list[AllergenMatch] = field(default_factory=list)
    is_safe: bool = True
    summary: str = ""


def _normalize(text: str) -> str:
    return text.lower().strip()


def check_dish_for_allergens(
    dish_name: str,
    ingredients: list[str],
    user_allergens: list[str],
    cross_contamination_aware: bool = True,
) -> DishSafetyResult:
    """
    Deterministically checks a dish against a user's allergen list.
    Returns structured safety result with risk levels.
    Never uses LLM inference — pure keyword matching against FDA + extended allergen database.
    """
    normalized_ingredients = [_normalize(i) for i in ingredients]
    normalized_user_allergens = [_normalize(a) for a in user_allergens]
    full_text = " ".join(normalized_ingredients)

    matches: list[AllergenMatch] = []

    for user_allergen in normalized_user_allergens:
        # Find the canonical allergen key
        canonical = _find_canonical_allergen(user_allergen)
        if canonical is None:
            # Try direct keyword match for unlisted allergens
            if user_allergen in full_text:
                matches.append(AllergenMatch(
                    allergen=user_allergen,
                    matched_keyword=user_allergen,
                    risk_level=RiskLevel.UNSAFE,
                    note="Direct match (custom allergen)",
                ))
            continue

        keywords = ALLERGEN_KEYWORDS.get(canonical, [user_allergen])
        direct_hit = _find_keyword_match(full_text, keywords)

        if direct_hit:
            matches.append(AllergenMatch(
                allergen=canonical,
                matched_keyword=direct_hit,
                risk_level=RiskLevel.UNSAFE,
                is_cross_contamination=False,
                note=f"Contains '{direct_hit}'",
            ))
        elif cross_contamination_aware:
            # Check cross-contamination risk
            related = CROSS_CONTAMINATION_PAIRS.get(canonical, [])
            for related_allergen in related:
                related_keywords = ALLERGEN_KEYWORDS.get(related_allergen, [])
                cross_hit = _find_keyword_match(full_text, related_keywords)
                if cross_hit:
                    matches.append(AllergenMatch(
                        allergen=canonical,
                        matched_keyword=cross_hit,
                        risk_level=RiskLevel.HIGH_RISK,
                        is_cross_contamination=True,
                        note=f"Cross-contamination risk: dish contains '{cross_hit}' (related to {canonical})",
                    ))
                    break

    overall_risk = _compute_overall_risk(matches)
    is_safe = overall_risk in (RiskLevel.SAFE, RiskLevel.LOW_RISK)

    summary = _build_summary(dish_name, matches, overall_risk)

    return DishSafetyResult(
        dish_name=dish_name,
        overall_risk=overall_risk,
        matches=matches,
        is_safe=is_safe,
        summary=summary,
    )


def _find_canonical_allergen(user_allergen: str) -> Optional[str]:
    """Maps a user-supplied allergen string to a canonical key."""
    if user_allergen in ALLERGEN_KEYWORDS:
        return user_allergen
    # Check if it's a keyword itself
    for canonical, keywords in ALLERGEN_KEYWORDS.items():
        if user_allergen in [k.lower() for k in keywords]:
            return canonical
    return None


def _find_keyword_match(text: str, keywords: list[str]) -> Optional[str]:
    """Returns the first keyword found in text, or None."""
    for kw in keywords:
        if kw.lower() in text:
            return kw
    return None


def _compute_overall_risk(matches: list[AllergenMatch]) -> RiskLevel:
    if not matches:
        return RiskLevel.SAFE
    levels = [m.risk_level for m in matches]
    if RiskLevel.UNSAFE in levels:
        return RiskLevel.UNSAFE
    if RiskLevel.HIGH_RISK in levels:
        return RiskLevel.HIGH_RISK
    if RiskLevel.MODERATE_RISK in levels:
        return RiskLevel.MODERATE_RISK
    if RiskLevel.LOW_RISK in levels:
        return RiskLevel.LOW_RISK
    return RiskLevel.SAFE


def _build_summary(dish_name: str, matches: list[AllergenMatch], risk: RiskLevel) -> str:
    if not matches:
        return f"{dish_name}: No allergen concerns detected."
    issues = "; ".join(m.note for m in matches)
    return f"{dish_name} [{risk.value}]: {issues}"


def score_restaurant_allergen_safety(
    user_allergens: list[str],
    menu_items: list[dict],  # Each: {"name": str, "ingredients": [str]}
) -> dict:
    """
    Scores an entire restaurant's menu against user allergens.
    Returns counts by risk level and per-item results.
    """
    results = []
    risk_counts = {r.value: 0 for r in RiskLevel}

    for item in menu_items:
        result = check_dish_for_allergens(
            dish_name=item.get("name", "Unknown"),
            ingredients=item.get("ingredients", []),
            user_allergens=user_allergens,
        )
        results.append(result)
        risk_counts[result.overall_risk.value] += 1

    total = len(menu_items)
    safe_count = risk_counts[RiskLevel.SAFE.value] + risk_counts[RiskLevel.LOW_RISK.value]
    safety_score = round((safe_count / total) * 100) if total > 0 else 0

    return {
        "safety_score": safety_score,
        "risk_counts": risk_counts,
        "item_results": results,
        "total_items": total,
        "safe_items": safe_count,
    }
