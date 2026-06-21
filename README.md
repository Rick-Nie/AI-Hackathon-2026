# DietMate - AI-Powered Dietary Preference & Restaurant Matching System

A sophisticated hackathon project that uses AI to understand granular dietary preferences and match users with the most suitable restaurants.

## 🌐 Live Demo

![DietMate demo](docs/demo.gif)

> _Record a ~15s clip of the app and save it as `docs/demo.gif` — see [Recording the demo GIF](#-recording-the-demo-gif) below. Until then, this image link will show as broken._

> **Try it:** **https://dietmate.vercel.app** _(replace with your Vercel URL after deploying)_

| Service | URL |
|---|---|
| 🖥️ Frontend (Vercel) | `https://<your-app>.vercel.app` |
| ⚙️ Backend API (Render) | `https://<your-backend>.onrender.com` |
| 📚 API docs (Swagger) | `https://<your-backend>.onrender.com/docs` |

> ⏳ **Note:** the backend runs on Render's free tier, which sleeps after ~15 min of inactivity. The **first request may take ~50 seconds** to wake it up — after that it's fast. Give the chat or first search a moment on initial load.

See [**Deploy Your Own**](#-deploy-your-own-live-demo) below for one-time setup (~10 min, free, no credit card).

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
- 🌍 **Yelp Integration** - Real restaurant data with mock fallback for demo
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
│   ├── restaurant_matcher.py  # Yelp search + scoring
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
# GOOGLE_PLACES_API_KEY=your_google_places_key (optional, mock data works without it)

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

## 🚢 Deploy Your Own Live Demo

This repo includes deploy configs ([`render.yaml`](render.yaml) for the backend, [`frontend/vercel.json`](frontend/vercel.json) for the frontend). Both platforms have free tiers — no credit card required.

### Step 1 — Push to GitHub
Make sure this project is in a GitHub repo (it is, if you cloned it).

### Step 2 — Deploy the backend to Render
1. Go to [render.com](https://render.com) → sign up with GitHub (free).
2. Click **New → Blueprint**, pick this repo. Render reads `render.yaml` automatically.
3. When prompted, set the environment variables:
   - `ANTHROPIC_API_KEY` → your Claude API key (required for the chatbot)
   - `GOOGLE_PLACES_API_KEY` → optional (mock restaurant data is used if omitted)
4. Click **Apply**. Wait for the build, then copy your backend URL, e.g. `https://dietmate-backend.onrender.com`.
5. Verify it works: open `https://<your-backend>.onrender.com/health` → should show `{"status":"ok"}`.

### Step 3 — Deploy the frontend to Vercel
1. Go to [vercel.com](https://vercel.com) → sign up with GitHub (free).
2. Click **Add New → Project**, import this repo.
3. Set **Root Directory** to `frontend`.
4. Under **Environment Variables**, add:
   - `VITE_API_URL` → your Render backend URL from Step 2 (e.g. `https://dietmate-backend.onrender.com`)
5. Click **Deploy**. Copy your live URL, e.g. `https://dietmate.vercel.app`.

### Step 4 — Update this README
Paste your two URLs into the [Live Demo](#-live-demo) section at the top. Done! 🎉

> **CORS:** the backend already allows all origins, so the Vercel frontend can call the Render backend out of the box.
>
> **Build note:** `frontend/vercel.json` uses `vite build` (not `tsc && vite build`) so the production demo deploys even if there are non-fatal TypeScript warnings. Run `npm run build` locally if you want the full strict typecheck.

## 🎬 Recording the demo GIF

The README embeds `docs/demo.gif`. To create it (Windows, ~2 min):

1. Start both servers locally (backend `run.bat`, frontend `npm run dev`).
2. Install **[ScreenToGif](https://www.screentogif.com/)** (free) — or use the Xbox Game Bar (`Win+G`) to record an MP4 and convert it.
3. Record a short flow that shows off the app, e.g.:
   - Type in chat: *"I love pizza, no allergies, I'm near UC Berkeley"*
   - Click **Search Restaurants**
   - Show the results cards, then the **Map** tab with pins
4. Trim to ~10–15 seconds, export as a GIF.
5. Save it as `docs/demo.gif` (overwrite the placeholder), commit, and push.

**Tips:** keep it under ~10 MB so it loads fast on GitHub; a 800–1000px wide capture looks crisp without being huge. For a higher-quality option, you can embed an MP4 by uploading it to the GitHub issue/PR drag-and-drop and pasting the resulting link instead.

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
- Yelp API (optional)

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