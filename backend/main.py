from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from models import (
    RestaurantSearchRequest,
    RestaurantSearchResponse,
    ChatRequest,
    ChatResponse,
    UserPreferences,
)
from restaurant_matcher import search_restaurants
from restaurant_matcher import search_restaurants_overpass, search_restaurants_google
from chat import chat
from allergens import check_dish_for_allergens, RiskLevel
from models import MapSearchRequest

app = FastAPI(
    title="DietMate API",
    description="Granular dietary preference & restaurant matching system",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/restaurants/search", response_model=RestaurantSearchResponse)
async def restaurant_search(request: RestaurantSearchRequest):
    try:
        restaurants = await search_restaurants(
            request.preferences,
            request.limit,
            latitude=request.latitude,
            longitude=request.longitude,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restaurant search failed: {str(e)}")

    location = request.preferences.location or (
        f"{request.preferences.latitude},{request.preferences.longitude}"
        if request.preferences.latitude is not None and request.preferences.longitude is not None
        else "your area"
    )
    prefs = request.preferences
    pref_parts = []
    if prefs.dietary_styles:
        pref_parts.append(", ".join(s.value for s in prefs.dietary_styles))
    if prefs.allergens:
        pref_parts.append(f"avoiding {', '.join(prefs.allergens)}")
    if prefs.preferred_cuisines:
        pref_parts.append(f"prefer {', '.join(c.value for c in prefs.preferred_cuisines)}")
    summary = " | ".join(pref_parts) if pref_parts else "No specific preferences"

    return RestaurantSearchResponse(
        restaurants=restaurants,
        total_found=len(restaurants),
        search_location=location,
        preferences_summary=summary,
    )


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        reply, updated_prefs = await chat(
            user_message=request.message,
            history=request.conversation_history,
            current_preferences=request.user_preferences,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

    suggestions = []
    if updated_prefs and (updated_prefs.allergens or updated_prefs.dietary_styles):
        suggestions.append("Search restaurants with your current preferences")

    return ChatResponse(
        reply=reply,
        updated_preferences=updated_prefs,
        suggested_searches=suggestions,
    )


@app.post("/allergen-check")
async def allergen_check(
    dish_name: str,
    ingredients: list[str],
    user_allergens: list[str],
):
    result = check_dish_for_allergens(
        dish_name=dish_name,
        ingredients=ingredients,
        user_allergens=user_allergens,
    )
    return {
        "dish_name": result.dish_name,
        "overall_risk": result.overall_risk.value,
        "is_safe": result.is_safe,
        "summary": result.summary,
        "matches": [
            {
                "allergen": m.allergen,
                "matched_keyword": m.matched_keyword,
                "risk_level": m.risk_level.value,
                "is_cross_contamination": m.is_cross_contamination,
                "note": m.note,
            }
            for m in result.matches
        ],
    }


@app.get("/allergens/list")
async def list_allergens():
    from allergens import ALLERGEN_KEYWORDS
    return {
        "allergen_categories": list(ALLERGEN_KEYWORDS.keys()),
        "total_categories": len(ALLERGEN_KEYWORDS),
        "keywords_by_category": ALLERGEN_KEYWORDS,
    }


@app.post("/restaurants/osm", response_model=RestaurantSearchResponse)
async def restaurants_osm(request: MapSearchRequest):
    try:
        restaurants = await search_restaurants_overpass(
            request.preferences,
            request.latitude,
            request.longitude,
            radius_m=request.radius_meters,
            limit=min(request.limit, 100),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OSM restaurant search failed: {str(e)}")

    location = f"{request.latitude},{request.longitude}"
    prefs = request.preferences
    pref_parts = []
    if prefs.dietary_styles:
        pref_parts.append(", ".join(s.value for s in prefs.dietary_styles))
    if prefs.allergens:
        pref_parts.append(f"avoiding {', '.join(prefs.allergens)}")
    if prefs.preferred_cuisines:
        pref_parts.append(f"prefer {', '.join(c.value for c in prefs.preferred_cuisines)}")
    summary = " | ".join(pref_parts) if pref_parts else "No specific preferences"

    return RestaurantSearchResponse(
        restaurants=restaurants,
        total_found=len(restaurants),
        search_location=location,
        preferences_summary=summary,
    )


@app.post("/restaurants/google", response_model=RestaurantSearchResponse)
async def restaurants_google(request: MapSearchRequest):
    try:
        restaurants = await search_restaurants_google(
            request.preferences,
            request.latitude,
            request.longitude,
            radius_m=request.radius_meters,
            limit=min(request.limit, 60),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Google Places search failed: {str(e)}")

    location = f"{request.latitude},{request.longitude}"
    prefs = request.preferences
    pref_parts = []
    if prefs.dietary_styles:
        pref_parts.append(", ".join(s.value for s in prefs.dietary_styles))
    if prefs.allergens:
        pref_parts.append(f"avoiding {', '.join(prefs.allergens)}")
    if prefs.preferred_cuisines:
        pref_parts.append(f"prefer {', '.join(c.value for c in prefs.preferred_cuisines)}")
    summary = " | ".join(pref_parts) if pref_parts else "No specific preferences"

    return RestaurantSearchResponse(
        restaurants=restaurants,
        total_found=len(restaurants),
        search_location=location,
        preferences_summary=summary,
    )
