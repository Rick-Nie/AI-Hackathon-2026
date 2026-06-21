export enum DietaryStyle {
  VEGAN = "vegan",
  VEGETARIAN = "vegetarian",
  PESCATARIAN = "pescatarian",
  HALAL = "halal",
  KOSHER = "kosher",
  KETO = "keto",
  PALEO = "paleo",
  LOW_FODMAP = "low_fodmap",
  RAW = "raw",
  OMNIVORE = "omnivore",
}

export enum CuisineType {
  ITALIAN = "italian",
  CHINESE = "chinese",
  JAPANESE = "japanese",
  MEXICAN = "mexican",
  INDIAN = "indian",
  THAI = "thai",
  MEDITERRANEAN = "mediterranean",
  AMERICAN = "american",
  FRENCH = "french",
  KOREAN = "korean",
  VIETNAMESE = "vietnamese",
  GREEK = "greek",
  MIDDLE_EASTERN = "middle_eastern",
  ETHIOPIAN = "ethiopian",
  OTHER = "other",
}

export enum SpiceLevel {
  NONE = "none",
  MILD = "mild",
  MEDIUM = "medium",
  HOT = "hot",
  EXTRA_HOT = "extra_hot",
}

export interface UserPreferences {
  dietary_styles: DietaryStyle[];
  allergens: string[];
  liked_ingredients: string[];
  disliked_ingredients: string[];
  preferred_cuisines: CuisineType[];
  disliked_cuisines: CuisineType[];
  max_spice_level: SpiceLevel;
  calorie_limit_per_meal?: number;
  protein_goal_g?: number;
  carb_limit_g?: number;
  fat_limit_g?: number;
  sodium_limit_mg?: number;
  budget_max_usd?: number;
  preferred_price_range?: string;
  location?: string;
  max_distance_miles: number;
  min_rating: number;
  requires_open_now: boolean;
  custom_notes?: string;
}

export interface NutritionInfo {
  calories?: number;
  protein_g?: number;
  carbs_g?: number;
  fat_g?: number;
  fiber_g?: number;
  sodium_mg?: number;
  sugar_g?: number;
}

export interface MenuItem {
  name: string;
  description?: string;
  ingredients: string[];
  price_usd?: number;
  nutrition?: NutritionInfo;
  dietary_tags: string[];
  spice_level?: SpiceLevel;
  is_customizable: boolean;
}

export interface AllergenSafetyReport {
  overall_risk: string;
  is_safe: boolean;
  safety_score: number;
  unsafe_items: string[];
  high_risk_items: string[];
}

export interface Restaurant {
  name: string;
  yelp_id: string;
  address: string;
  rating: number;
  review_count: number;
  cuisines: string[];
  price_range?: string;
  phone?: string;
  url?: string;
  distance_miles?: number;
  is_open: boolean;
  match_score: number;
  dietary_tags: string[];
  recommended_dishes: MenuItem[];
  allergen_report: AllergenSafetyReport;
}

export interface RestaurantSearchRequest {
  preferences: UserPreferences;
  limit: number;
}

export interface RestaurantSearchResponse {
  restaurants: Restaurant[];
  total_found: number;
  search_location: string;
  preferences_summary: string;
}

export interface ChatRequest {
  message: string;
  conversation_history: Array<{ role: string; content: string }>;
  user_preferences?: UserPreferences;
}

export interface ChatResponse {
  reply: string;
  updated_preferences?: UserPreferences;
  suggested_searches: string[];
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}
