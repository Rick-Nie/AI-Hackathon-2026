# DietMate Frontend

Fast, modern React + TypeScript frontend for the DietMate restaurant matching system.

## Setup

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

The frontend will run on `http://localhost:5173` and proxy API calls to `http://localhost:8000`.

## Features

- 💬 **AI Chatbot Interface** - Conversational preference collection with Claude
- 🍽️ **Restaurant Search** - Real-time results with detailed matching scores
- 🚫 **Allergen Safety Scoring** - Visual indicators for allergen risks
- 🎨 **Modern UI** - Responsive design with Lucide icons
- ⚡ **Vite** - Lightning-fast hot reload development

## Tech Stack

- React 18
- TypeScript
- Vite
- Lucide React (icons)
- Axios (HTTP client)

## API Integration

Frontend connects to FastAPI backend at `http://localhost:8000`. Endpoints:

- `POST /chat` - Conversational preference collection
- `POST /restaurants/search` - Find matching restaurants
- `POST /allergen-check` - Check dish allergen safety
- `GET /health` - Health check

See backend README for full API documentation.
