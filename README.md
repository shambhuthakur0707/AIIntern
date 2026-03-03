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
3. `llm_engine`: analyse each top internship with the configured LLM provider (Ollama **or** Groq), enforcing strict JSON output.
4. `fallback_engine`: deterministic reasoning/roadmap when LLM is unavailable or returns invalid JSON. Returns an explicit `fallback_reason` so the cause is visible in the API response.
5. `response_formatter`: merges ranking + analysis into final API response.

## Models used

### LLM
The provider is selected at startup via the `LLM_PROVIDER` env var.

| `LLM_PROVIDER` | Default model | Notes |
|---|---|---|
| `ollama` (default) | `llama3:latest` | Runs locally; no API key needed. Override with `OLLAMA_MODEL`. |
| `groq` | `llama3-8b-8192` | Cloud API; requires `GROQ_API_KEY`. Override with `GROQ_MODEL`. |

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

### LLM provider setup

Choose **one** of the following providers and add the relevant variables to `.env`.

#### Option A — Ollama (local, default)

1. Install Ollama: https://ollama.com/download
2. Pull the model:

   ```bash
   ollama pull llama3:latest
   ```

3. Add to `.env`:

   ```env
   LLM_PROVIDER=ollama
   OLLAMA_MODEL=llama3:latest      # optional, this is the default
   OLLAMA_TIMEOUT_SEC=30           # seconds before a single call times out
   OLLAMA_HEALTH_TTL_SEC=20        # seconds between availability re-checks
   LLM_MAX_RETRIES=1               # extra retries on JSON parse failure
   ```

4. Make sure the Ollama daemon is running before starting the backend:

   ```bash
   ollama serve
   ```

5. Install the Python client (already in `requirements.txt`):

   ```bash
   pip install ollama
   ```

#### Option B — Groq (cloud)

1. Sign up at https://console.groq.com and create an API key.
2. Add to `.env`:

   ```env
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
   GROQ_MODEL=llama3-8b-8192       # optional, this is the default
   GROQ_TIMEOUT_SEC=30             # seconds before a single call times out
   LLM_MAX_RETRIES=1               # extra retries on JSON parse failure
   ```

3. Install the Groq Python client:

   ```bash
   pip install groq
   ```

> **Fallback behaviour**: if the selected provider is unreachable or returns invalid JSON after all retries, the rule-based `fallback_engine` is used automatically. The `fallback_reason` field in each recommendation explains why.

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

- The active LLM provider is controlled by `LLM_PROVIDER` in `.env` (`ollama` or `groq`).
- LangChain tool classes exist in `backend/tools/`, but the active orchestration path is the custom engine pipeline in `backend/engines/`.
- If the LLM provider is down or returns invalid JSON after all retries, the rule-based fallback engine is used automatically. Every recommendation includes a `fallback_used` boolean and a `fallback_reason` string so clients know which engine produced the analysis.
