from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class DietaryStyle(str, Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    PESCATARIAN = "pescatarian"
    HALAL = "halal"
    KOSHER = "kosher"
    KETO = "keto"
    PALEO = "paleo"
    LOW_FODMAP = "low_fodmap"
    RAW = "raw"
    OMNIVORE = "omnivore"


class CuisineType(str, Enum):
    ITALIAN = "italian"
    CHINESE = "chinese"
    JAPANESE = "japanese"
    MEXICAN = "mexican"
    INDIAN = "indian"
    THAI = "thai"
    MEDITERRANEAN = "mediterranean"
    AMERICAN = "american"
    FRENCH = "french"
    KOREAN = "korean"
    VIETNAMESE = "vietnamese"
    GREEK = "greek"
    MIDDLE_EASTERN = "middle_eastern"
    ETHIOPIAN = "ethiopian"
    OTHER = "other"


class SpiceLevel(str, Enum):
    NONE = "none"
    MILD = "mild"
    MEDIUM = "medium"
    HOT = "hot"
    EXTRA_HOT = "extra_hot"


class UserPreferences(BaseModel):
    dietary_styles: list[DietaryStyle] = Field(default_factory=list)
    allergens: list[str] = Field(
        default_factory=list,
        description="Allergens to AVOID (deterministic rule matching)",
    )
    disliked_ingredients: list[str] = Field(
        default_factory=list,
        description="Ingredients user dislikes but aren't safety-critical",
    )
    preferred_cuisines: list[CuisineType] = Field(default_factory=list)
    disliked_cuisines: list[CuisineType] = Field(default_factory=list)
    max_spice_level: SpiceLevel = SpiceLevel.MEDIUM
    calorie_limit_per_meal: Optional[int] = None
    protein_goal_g: Optional[int] = None
    carb_limit_g: Optional[int] = None
    fat_limit_g: Optional[int] = None
    sodium_limit_mg: Optional[int] = None
    budget_max_usd: Optional[float] = None
    preferred_price_range: Optional[str] = Field(
        None, description="$, $$, $$$, $$$$"
    )
    location: Optional[str] = None
    max_distance_miles: float = 5.0
    min_rating: float = 3.5
    requires_open_now: bool = True
    custom_notes: Optional[str] = None


class NutritionInfo(BaseModel):
    calories: Optional[int] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    sugar_g: Optional[float] = None


class MenuItem(BaseModel):
    name: str
    description: Optional[str] = None
    ingredients: list[str] = Field(default_factory=list)
    price_usd: Optional[float] = None
    nutrition: Optional[NutritionInfo] = None
    dietary_tags: list[str] = Field(default_factory=list)
    spice_level: Optional[SpiceLevel] = None
    is_customizable: bool = False


class AllergenSafetyReport(BaseModel):
    overall_risk: str
    is_safe: bool
    safety_score: int = Field(description="0-100, higher is safer")
    unsafe_items: list[str] = Field(default_factory=list)
    high_risk_items: list[str] = Field(default_factory=list)
    safe_item_count: int = 0
    total_item_count: int = 0
    warnings: list[str] = Field(default_factory=list)


class DietaryCompatibilityReport(BaseModel):
    is_compatible: bool
    compatible_styles: list[str] = Field(default_factory=list)
    incompatible_styles: list[str] = Field(default_factory=list)
    disliked_ingredients_found: list[str] = Field(default_factory=list)
    preferred_cuisine_match: bool = False
    notes: list[str] = Field(default_factory=list)


class RestaurantMatch(BaseModel):
    yelp_id: str
    name: str
    rating: float
    review_count: int
    price_range: Optional[str] = None
    cuisine_types: list[str] = Field(default_factory=list)
    address: str
    distance_miles: Optional[float] = None
    phone: Optional[str] = None
    url: Optional[str] = None
    is_open_now: Optional[bool] = None
    image_url: Optional[str] = None

    # Dietary analysis
    allergen_safety: Optional[AllergenSafetyReport] = None
    dietary_compatibility: Optional[DietaryCompatibilityReport] = None
    safe_menu_items: list[MenuItem] = Field(default_factory=list)
    match_score: float = Field(default=0.0, description="0-100 composite match score")
    match_reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class RestaurantSearchRequest(BaseModel):
    preferences: UserPreferences
    limit: int = Field(default=10, ge=1, le=50)


class RestaurantSearchResponse(BaseModel):
    restaurants: list[RestaurantMatch]
    total_found: int
    search_location: str
    preferences_summary: str


class ChatMessage(BaseModel):
    role: str = Field(description="'user' or 'assistant'")
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_history: list[ChatMessage] = Field(default_factory=list)
    user_preferences: Optional[UserPreferences] = None


class ChatResponse(BaseModel):
    reply: str
    updated_preferences: Optional[UserPreferences] = None
    suggested_searches: list[str] = Field(default_factory=list)
