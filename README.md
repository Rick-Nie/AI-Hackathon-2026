# DietMate - AI-Powered Dietary Preference & Restaurant Matching System

A sophisticated hackathon project that uses AI to understand granular dietary preferences and match users with the most suitable restaurants.

## 🎯 Project Overview

**Problem:** Current restaurant matching systems are insufficient for users with specific dietary needs, allergies, or preferences. They lack:
- Granular dietary preference collection
- Deterministic allergen safety (not LLM-based)
- Cross-contamination modeling
- Conversational preference discovery

**Solution:** DietMate uses a two-part system:
1. **Backend:** Deterministic allergen matching + AI chatbot for preference collection
2. **Frontend:** Beautiful React UI with real-time restaurant search and allergen safety visualizations

## ✨ Key Features

### Backend (Python/FastAPI)
- 🚫 **Deterministic Allergen Engine** - Rule-based matching against 300+ ingredient aliases across 14 allergen categories
- 💬 **Claude Chatbot Integration** - Conversational dietary preference collection via Claude API
- 🔍 **Smart Restaurant Matching** - Weighted scoring: rating (40%) + allergen safety (30%) + diet compatibility (15%) + cuisine (10%) + price (5%)
- 🌍 **Google Places Integration** - Real restaurant data with mock fallback for demo
- 📊 **Cross-contamination Modeling** - E.g., peanut-allergic users get HIGH_RISK on tree nut dishes
- ✅ **Nutrition Tracking** - Calorie, protein, carb, fat, fiber, sodium goals
- 💯 **No Safety Guessing** - Allergens are NEVER decided by LLM

### Frontend (React/TypeScript/Vite)
- 💬 **Chat Assistant** - Interactive preference builder using conversational AI
- 🎨 **Modern UI** - Gradient design, smooth animations, responsive layout
- 📱 **Real-time Updates** - Preferences update as you chat
- 🍽️ **Restaurant Cards** - Visual match scores, allergen warnings, recommended dishes
- 🚫 **Safety Badges** - Color-coded allergen indicators (Green → Safe, Red → Unsafe)
- ⚡ **Fast** - Vite + React hot reload

## 🗂️ Project Structure

```
AI-Hackathon-2026/
├── backend/
│   ├── allergens.py           # Deterministic allergen rule engine
│   ├── models.py              # Pydantic data models
│   ├── restaurant_matcher.py  # Places search + scoring
│   ├── chat.py                # Claude chatbot wrapper
│   ├── main.py                # FastAPI app (4 endpoints)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.tsx            # Main app layout
    │   ├── App.css
    │   ├── types.ts           # TypeScript definitions (mirrored from backend)
    │   ├── api.ts             # Axios API client
    │   ├── index.css          # Global styles
    │   ├── main.tsx           # React entry
    │   └── components/
    │       ├── ChatInterface.tsx/.css   # Chat UI
    │       ├── RestaurantResults.tsx/.css  # Results grid
    │       └── PreferenceBuilder.tsx/.css  # Preference tags
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── .env.example
    └── index.html
```

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
cp .env.example .env

# Add your API keys to .env
# ANTHROPIC_API_KEY=your_claude_api_key
# GOOGLE_PLACES_API_KEY=your_google_places_api_key (optional, mock data works without it)

uvicorn main:app --reload
# API runs at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env

# .env is pre-configured to http://localhost:8000
npm run dev
# Frontend runs at http://localhost:5173
```

Visit `http://localhost:5173` in your browser. Backend must be running!

## 📊 API Endpoints

### POST `/restaurants/search`
Search for restaurants matching user preferences.
```json
{
  "preferences": {
    "dietary_styles": ["vegan", "keto"],
    "allergens": ["peanut", "shellfish"],
    "preferred_cuisines": ["japanese", "thai"],
    "location": "San Francisco",
    "max_distance_miles": 5,
    "min_rating": 3.5
  },
  "limit": 10
}
```

### POST `/chat`
Conversational preference collection with Claude.
```json
{
  "message": "I'm vegan and allergic to tree nuts",
  "conversation_history": [...],
  "user_preferences": {...}
}
```

### POST `/allergen-check`
Deterministic allergen safety check for a dish.
```json
{
  "dish_name": "Pad Thai",
  "ingredients": ["peanuts", "shrimp", "rice noodles"],
  "user_allergens": ["peanut", "shellfish"]
}
```

### GET `/health`
Health check endpoint.

## 🔧 Tech Stack

**Backend:**
- Python 3.9+
- FastAPI
- Pydantic
- Anthropic Claude API
- Google Places API (optional)

**Frontend:**
- React 18
- TypeScript
- Vite
- Lucide React (icons)
- Axios

## 🎓 Design Decisions

1. **Deterministic Allergens First** - Safety is too critical to rely on LLM inference. Backend uses curated rule matching.
2. **Conversational UX** - Chatbot collects preferences naturally rather than forcing users through forms.
3. **Weighted Scoring** - Restaurants are ranked by multiple factors, not just rating.
4. **No Backend Coupling** - Frontend types are standalone copies of models, allowing independent deployments.
5. **Mock Data Support** - Run the entire demo without API keys (for hackathon environments).

## 🌟 Hackathon Differentiator

This goes deeper than most restaurant apps:
- Users describe allergies **conversationally** (not checkboxes)
- System thinks in terms of **cross-contamination** risk
- **Granular preferences** (10 dietary styles, 14+ allergen categories, nutrition goals, etc.)
- **Deterministic safety** - No guessing on allergens
- **Specific dish recommendations** with price & nutrition info

## 📝 Example Use Case

1. User: *"I'm vegan and have a severe peanut allergy"*
2. Chatbot: *"Got it! Any other allergies? How do you feel about spicy food?"*
3. User: *"Tree nuts too, and I like mild food"*
4. Chatbot: *"Perfect! Prefer any cuisines?"*
5. User: *"Thai and Japanese"*
6. → **Search restaurants** with 10 results ranked by match score, all marked SAFE for allergens

## 🛠️ Development

### Adding New Allergens
Edit `backend/allergens.py` → Add to `ALLERGEN_KEYWORDS` dict.

### Adding New Dietary Styles
Edit `backend/models.py` → Add to `DietaryStyle` enum in both backend and `frontend/src/types.ts`.

### Customizing Match Scoring
Edit `backend/restaurant_matcher.py` → Adjust weights in `calculate_match_score()`.

### Extending Chatbot
Edit `backend/chat.py` → Modify Claude system prompt and preference extraction logic.

## 📦 Dependencies

See:
- [backend/requirements.txt](backend/requirements.txt)
- [frontend/package.json](frontend/package.json)

## 🤝 Team Credit

- **Backend:** Comprehensive allergen engine, Claude integration, FastAPI API
- **Frontend:** React UI with chat interface, restaurant cards, real-time preference builder

## 📄 License

Hackathon project - MIT License

---

**Happy eating! 🍽️**