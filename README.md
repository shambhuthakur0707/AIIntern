# AIIntern - Agentic Internship Matcher

AIIntern is a full-stack internship recommendation system.
It combines deterministic ranking logic with local LLM analysis to produce top internship matches, reasoning, skill gaps, and a learning roadmap.

## What the project does

- Auth: user registration and login with JWT.
- Profile: stores skills, interests, experience level, and education.
- Matching pipeline: filters internships by skill overlap, ranks them, then enriches results with AI reasoning.
- Dashboard: returns user data and last saved matching result.
- Profile import: extracts skills/interests from CV text and profile links.

## Current backend pipeline (actual code)

1. `matching_engine`: fetch internships from MongoDB and filter below 25% skill overlap.
2. `ranking_engine`: compute weighted score:
   - 60% skill overlap
   - 20% keyword relevance (TF-IDF + cosine similarity)
   - 20% experience-level match
3. `llm_engine`: analyze each top internship with Ollama strict JSON output.
4. `fallback_engine`: deterministic reasoning/roadmap when LLM is unavailable or invalid.
5. `response_formatter`: merges ranking + analysis into final API response.

## Models used

### LLM
- Ollama model: `llama3:latest`
- Used for per-internship reasoning, confidence score, skill-gap analysis, and learning roadmap.

### ML/NLP scoring
- `TfidfVectorizer` + `cosine_similarity` (scikit-learn)
- Used for keyword relevance scoring between user interests and internship text.

### Rule-based fallback
- Deterministic fallback engine with curated resource map for roadmap generation.

## Tech stack

- Frontend: React + Vite + Tailwind
- Backend: Flask + Flask-JWT-Extended + Flask-CORS
- Database: MongoDB (PyMongo)
- LLM runtime: Ollama (local)
- Ranking/ML: scikit-learn
- Auth/security: bcrypt + JWT

## Project structure

```text
AIIntern/
|- backend/
|  |- app.py
|  |- config.py
|  |- seed.py
|  |- requirements.txt
|  |- agents/
|  |  |- internship_agent.py
|  |- engines/
|  |  |- matching_engine.py
|  |  |- ranking_engine.py
|  |  |- llm_engine.py
|  |  |- fallback_engine.py
|  |  |- response_formatter.py
|  |- routes/
|  |  |- auth_routes.py
|  |  |- agent_routes.py
|  |  |- dashboard_routes.py
|  |- services/
|  |  |- profile_import_service.py
|  |- models/
|  |- utils/
|- frontend/
|  |- src/
```

## Setup

## 1) Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set at least:

```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=aiintern_db
JWT_SECRET_KEY=your-secret-key
FLASK_PORT=5000
FLASK_DEBUG=True
```

Seed sample data:

```bash
python seed.py
```

Run backend:

```bash
python app.py
```

Backend URL: `http://localhost:5000`

## 2) Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## API overview

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`

### Agent
- `POST /api/agent/match` (JWT required)

### Dashboard / Profile
- `GET /api/dashboard` (JWT required)
- `PATCH /api/profile/skills/add` (JWT required)
- `PATCH /api/profile/skills/remove` (JWT required)
- `POST /api/profile/import` (JWT required)

### Health
- `GET /api/health`

## Notes

- Runtime analysis currently uses Ollama (`llama3:latest`), not GPT-4o.
- LangChain tool classes exist in `backend/tools/`, but the active orchestration path is the custom engine pipeline in `backend/engines/`.
- If Ollama is down or returns invalid JSON, fallback output is still returned so the API remains usable.
