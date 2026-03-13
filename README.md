# AIIntern — Agentic AI Internship Recommendation System

AIIntern is a full-stack, AI-powered internship recommendation platform that automatically discovers internships from external job platforms, matches students to relevant opportunities using a multi-stage agentic pipeline, and generates personalised learning roadmaps to close skill gaps.

---

## Features

### 1. Automated Internship Scraping

A background scheduler fetches live internship listings every 6 hours (configurable) from multiple external platforms and stores them in MongoDB, de-duplicated by `apply_url`.

| Data source | What it covers | API key required? |
|---|---|---|
| **JSearch** (RapidAPI) | LinkedIn, Indeed, Glassdoor, ZipRecruiter | Yes — free tier 200 req/month |
| **Remotive** | Remote tech internships (6 categories) | No — completely free |
| **Adzuna** | Global job boards across 7 countries (US, GB, IN, AU, CA, DE, FR) | Yes — free tier 250 req/month |

- **Internship-only filtering** — API-level params (`employment_types=INTERN`, search terms contain "internship") **plus** a code-level guard that checks every listing for intern/trainee/apprentice/co-op markers.
- Skill extraction from descriptions (50+ recognised tech skills).
- Domain inference (ML, Web Dev, DevOps, Cloud, Cybersecurity, etc.).
- Manual trigger via `POST /api/scraper/trigger` and status check via `GET /api/scraper/status`.

### 2. Agentic AI Matching Pipeline

When a user clicks **"Run AI Agent"** the backend orchestrates a multi-step pipeline:

```
User Profile
     │
     ▼
┌─────────────────────────┐
│  1. Matching Engine      │  Filter internships with ≥25% skill overlap
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  2. Ranking Engine       │  Weighted scoring (60% skills, 20% keywords, 20% experience)
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  3. LLM Engine           │  Per-internship AI analysis with strict JSON output
│     ↓ on failure         │
│  3b. Fallback Engine     │  Rule-based deterministic analysis
└────────────┬────────────┘
             ▼
┌─────────────────────────┐
│  4. Response Formatter   │  Merges ranking + analysis → final API response
└─────────────────────────┘
```

Each recommendation includes:
- **Confidence score** — how well the student fits
- **Reasoning** — natural-language explanation
- **Matched & missing skills**
- **Skill gap analysis**
- **4-week learning roadmap** with curated resources
- **Improvement priority** — what to learn first

### 3. Multi-Provider LLM Support

| Provider | Default model | Notes |
|---|---|---|
| **Ollama** (default) | `llama3:latest` | Runs locally, no API key needed. Override with `OLLAMA_MODEL`. |
| **Groq** (cloud) | `llama3-8b-8192` | Requires `GROQ_API_KEY`. Override with `GROQ_MODEL`. |

- Strict JSON schema enforcement with retry logic.
- Health checks and timeout handling per provider.
- Automatic fallback to the rule-based engine if the LLM is down, with transparent `fallback_used` / `fallback_reason` flags.

### 4. ML / NLP Scoring

| Technique | Library | Usage |
|---|---|---|
| **TF-IDF Vectorization** | scikit-learn `TfidfVectorizer` | Converts user interests and internship text into feature vectors |
| **Cosine Similarity** | scikit-learn `cosine_similarity` | Computes keyword relevance score between user and internship |
| **Set Intersection** | Python builtins | Case-insensitive skill overlap percentage |

### 5. Rule-Based Fallback Engine

When the LLM is unavailable or returns invalid JSON:
- Generates the same JSON schema deterministically.
- Maps 50+ skills to curated learning resources with estimated time.
- Produces a 4-week roadmap with weekly focus areas and tasks.
- Marks output with `fallback_used: true` so the frontend can display the source.

### 6. Profile Import (NLP Skill Extraction)

Users can import their profile from:
- **CV / Resume** — upload `.txt`, `.md`, or `.rtf` files
- **LinkedIn URL** — parsed for skill mentions
- **GitHub URL** — parsed for tech stack indicators

Uses regex-based NLP matching against a dynamic skill catalogue (base skills + all internship requirements from DB).

### 7. User Authentication & Profiles

- JWT-based auth with 24-hour token expiry.
- Password hashing with bcrypt.
- Profile fields: skills, interests, education, experience level, LinkedIn/GitHub URLs, bio, location.
- Dynamic skill management (add/remove individual skills).

### 8. Internship Browsing & Filtering

- **Filter by**: sector, domain, location.
- **Pagination**: configurable page size.
- **AI-enriched listings**: each internship optionally includes match score, reasoning, and roadmap.
- **Sector derivation**: automatically maps domains to broader sectors (e.g. "Machine Learning" → "Artificial Intelligence").
- **Apply URL generation**: uses the original link or generates a LinkedIn search fallback.

### 9. Interactive Dashboard

- **Match results** with animated confidence arcs (SVG circular progress).
- **Skills gap chart** (Recharts bar chart) comparing market demand vs user skills.
- **Match history** persisted in localStorage.
- **Onboarding wizard** (3-step modal) for new users with no skills set.
- **Profile import** from CV/LinkedIn/GitHub directly from the dashboard.

### 10. Modern Frontend UI

- **Glass morphism** design with animated gradient backgrounds.
- **Responsive** — full mobile support with hamburger navigation.
- **Toast notifications** (success, error, info, warning) with auto-dismiss.
- **Skeleton loading** states for every data-fetching view.
- **Copy-to-clipboard** for learning roadmaps.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18, React Router 6, Recharts, Axios |
| **Build tools** | Vite 5, Tailwind CSS 3, PostCSS, Autoprefixer |
| **Backend** | Flask, Flask-JWT-Extended, Flask-CORS |
| **Database** | MongoDB (PyMongo) |
| **LLM runtime** | Ollama (local) / Groq (cloud) |
| **ML / NLP** | scikit-learn (TF-IDF, cosine similarity) |
| **Job scraping** | Requests, APScheduler |
| **Auth / Security** | bcrypt, JWT |
| **LangChain tools** | BaseTool wrappers (db_tool, skill_match_tool, skill_gap_tool) |

---

## Project Structure

```
AIIntern/
├── backend/
│   ├── app.py                      # Flask application factory
│   ├── config.py                   # Environment configuration
│   ├── seed.py                     # Database seeder (10 internships, 2 users)
│   ├── requirements.txt
│   ├── .env.example
│   ├── agents/
│   │   └── internship_agent.py     # Main matching pipeline orchestrator
│   ├── engines/
│   │   ├── matching_engine.py      # Skill overlap filtering (≥25%)
│   │   ├── ranking_engine.py       # Weighted multi-factor scoring
│   │   ├── llm_engine.py           # Ollama / Groq LLM integration
│   │   ├── fallback_engine.py      # Rule-based deterministic fallback
│   │   └── response_formatter.py   # Final API response assembly
│   ├── models/
│   │   ├── user_model.py           # User document schema
│   │   └── internship_model.py     # Internship document schema
│   ├── routes/
│   │   ├── auth_routes.py          # Register, login, profile update
│   │   ├── agent_routes.py         # AI matching endpoint
│   │   ├── dashboard_routes.py     # Dashboard + skill management
│   │   ├── internships_routes.py   # Browse & filter internships
│   │   └── scraper_routes.py       # Trigger scraper / check status
│   ├── scrapers/
│   │   ├── scheduler.py            # APScheduler background job
│   │   ├── jsearch_scraper.py      # JSearch API (LinkedIn, Indeed, etc.)
│   │   ├── remotive_scraper.py     # Remotive API (free, remote jobs)
│   │   └── adzuna_scraper.py       # Adzuna API (7 countries)
│   ├── services/
│   │   ├── user_service.py         # User CRUD operations
│   │   ├── profile_import_service.py  # NLP skill extraction
│   │   └── matching_service.py     # Matching service stub
│   ├── tools/
│   │   ├── db_tool.py              # LangChain FetchInternshipsTool
│   │   ├── skill_match_tool.py     # LangChain SkillMatchTool (TF-IDF)
│   │   └── skill_gap_tool.py       # LangChain SkillGapAnalysisTool
│   └── utils/
│       ├── jwt_utils.py            # JWT identity extraction
│       └── response_utils.py       # JSON response wrappers
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js              # Dev server on :5173, proxy /api → :5000
│   ├── tailwind.config.js          # Custom brand palette + animations
│   ├── postcss.config.js
│   └── src/
│       ├── App.jsx                 # Route definitions
│       ├── main.jsx                # React entry point
│       ├── index.css               # Tailwind + custom glass-card styles
│       ├── api/
│       │   └── axios.js            # Axios instance with JWT interceptor
│       ├── context/
│       │   ├── AuthContext.jsx      # JWT + user state management
│       │   └── ToastContext.jsx     # Toast notification system
│       ├── components/
│       │   ├── InternshipCard.jsx   # AI-enriched recommendation card
│       │   ├── Navbar.jsx           # Responsive navigation bar
│       │   ├── OnboardingWizard.jsx # 3-step new-user onboarding
│       │   ├── ProgressBar.jsx      # Animated score progress bar
│       │   ├── RoadmapTimeline.jsx  # 4-week learning roadmap visual
│       │   ├── Skeleton.jsx         # Loading skeleton components
│       │   └── SkillBadge.jsx       # Coloured skill pill badge
│       └── pages/
│           ├── DashboardPage.jsx    # Main hub with charts & agent trigger
│           ├── InternshipsPage.jsx  # Browse, filter, paginate internships
│           ├── ProfilePage.jsx      # Edit user profile
│           ├── LoginPage.jsx        # Login form
│           └── RegisterPage.jsx     # Registration with skill input
└── README.md
```

---

## Database Schema (MongoDB)

### `users` collection

| Field | Type | Description |
|---|---|---|
| `name` | string | Full name |
| `email` | string | Unique, lowercased |
| `password_hash` | string | bcrypt hash |
| `skills` | string[] | User's technical skills |
| `interests` | string[] | Domains of interest |
| `experience_level` | string | beginner / intermediate / advanced |
| `education` | string | Degree or current education |
| `linkedin_url` | string | LinkedIn profile link |
| `github_url` | string | GitHub profile link |
| `resume` | string | Uploaded resume filename |
| `last_match_result` | object | Persisted AI agent output |
| `created_at` / `updated_at` | datetime | Timestamps |

### `internships` collection

| Field | Type | Description |
|---|---|---|
| `title` | string | Position title |
| `company` | string | Company name |
| `required_skills` | string[] | Skills needed |
| `description` | string | Full description (up to 1200 chars from scrapers) |
| `domain` | string | e.g. Machine Learning, Web Development |
| `stipend` | string | e.g. "$1,200/month" or "Not disclosed" |
| `duration` | string | e.g. "3 months" |
| `location` | string | e.g. "Bangalore, India" or "Remote" |
| `openings` | int | Number of positions |
| `apply_url` | string | Direct application link |
| `source` | string | "seed", "jsearch", "remotive", or "adzuna" |
| `scraped_at` | datetime | When the scraper fetched this listing |
| `created_at` | datetime | First insertion time |

### `scraper_meta` collection

| Field | Type | Description |
|---|---|---|
| `_id` | string | Always `"last_run"` |
| `run_at` | datetime | When the last scrape completed |
| `total_inserted` | int | New internships added |
| `total_updated` | int | Existing internships refreshed |
| `errors` | string[] | Any scraper errors from the run |

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | — | Create a new user account |
| `POST` | `/api/auth/login` | — | Login and receive JWT |
| `GET` | `/api/auth/me` | JWT | Get current user profile |
| `PUT` | `/api/auth/profile` | JWT | Update user profile fields |
| `POST` | `/api/agent/match` | JWT | Run the AI matching pipeline |
| `GET` | `/api/dashboard` | JWT | Dashboard data + last match result |
| `PATCH` | `/api/profile/skills/add` | JWT | Add a skill to user profile |
| `PATCH` | `/api/profile/skills/remove` | JWT | Remove a skill from user profile |
| `POST` | `/api/profile/import` | JWT | Import skills from CV / LinkedIn / GitHub |
| `GET` | `/api/internships` | JWT | Browse & filter internships (paginated) |
| `POST` | `/api/scraper/trigger` | JWT | Manually trigger a scraper run |
| `GET` | `/api/scraper/status` | JWT | Scraper scheduler & last-run status |
| `GET` | `/api/health` | — | Health check |

---

## Setup

### 1) Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

Create a `.env` file from `.env.example` and set at least:

```env
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=aiintern_db
JWT_SECRET_KEY=your-secret-key
FLASK_PORT=5000
FLASK_DEBUG=True
```

### LLM Provider Setup

Choose **one** of the following and add the relevant variables to `.env`.

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
   OLLAMA_TIMEOUT_SEC=30
   OLLAMA_HEALTH_TTL_SEC=20
   LLM_MAX_RETRIES=1
   ```

4. Start the Ollama daemon:

   ```bash
   ollama serve
   ```

#### Option B — Groq (cloud)

1. Sign up at https://console.groq.com and create an API key.
2. Add to `.env`:

   ```env
   LLM_PROVIDER=groq
   GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxx
   GROQ_MODEL=llama3-8b-8192       # optional, this is the default
   GROQ_TIMEOUT_SEC=30
   LLM_MAX_RETRIES=1
   ```

> **Fallback behaviour**: if the LLM is unreachable or returns invalid JSON after retries, the rule-based `fallback_engine` kicks in automatically. Every recommendation includes `fallback_used` (boolean) and `fallback_reason` (string) so the cause is always visible.

### Internship Scraper Setup (optional but recommended)

The Remotive scraper works instantly with **no API key**. To also pull from LinkedIn / Indeed / Glassdoor / Adzuna, add:

```env
# JSearch (RapidAPI) — sign up free at https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
JSEARCH_API_KEY=your-rapidapi-key

# Adzuna — sign up free at https://developer.adzuna.com/
ADZUNA_APP_ID=your-app-id
ADZUNA_API_KEY=your-api-key

# Scrape interval (default: every 6 hours)
SCRAPER_INTERVAL_HOURS=6
```

### Seed & Run

```bash
python seed.py       # populate 10 sample internships + 2 demo users
python app.py        # start backend at http://localhost:5000
```

Demo login: `aryan@example.com` / `password123`

### 2) Frontend

```bash
cd frontend
npm install
npm run dev          # starts at http://localhost:5173
```

The Vite dev server proxies `/api` requests to the Flask backend on port 5000.

### Google Sign-In Setup

1. Create a Google OAuth Web application in Google Cloud Console.
2. Add your frontend origin to `Authorized JavaScript origins`.
3. Set the same web client ID in both `frontend/.env` as `VITE_GOOGLE_CLIENT_ID` and `backend/.env` as `GOOGLE_CLIENT_ID`.
4. Restart both frontend and backend after updating the env files.

The Google sign-in button is hidden automatically when the frontend client ID is missing or still set to the placeholder value.

---

## Models & Algorithms Summary

| Component | Model / Algorithm | Purpose |
|---|---|---|
| **LLM Analysis** | Llama 3 (via Ollama or Groq) | Per-internship reasoning, skill gap analysis, learning roadmap |
| **Keyword Relevance** | TF-IDF + Cosine Similarity (scikit-learn) | Score how well user interests match internship text |
| **Skill Overlap** | Set Intersection | Percentage of required skills the user already has |
| **Experience Matching** | Keyword-based heuristic | Maps beginner/intermediate/advanced to job requirements |
| **Skill Extraction** | Regex NLP matching | Extracts skills from CVs, LinkedIn, and GitHub profiles |
| **Fallback Reasoning** | Rule-based engine with curated resource map | Deterministic roadmap generation when LLM is unavailable |
| **Ranking** | Weighted composite (60/20/20) | Combines skill overlap, keyword relevance, and experience match |

---

## Notes

- The active LLM provider is controlled by `LLM_PROVIDER` in `.env` (`ollama` or `groq`).
- LangChain `BaseTool` wrappers exist in `backend/tools/` (`FetchInternshipsTool`, `SkillMatchTool`, `SkillGapAnalysisTool`), but the primary orchestration runs through the custom engine pipeline in `backend/engines/`.
- If the LLM provider is down, the rule-based fallback engine is used automatically. Every recommendation includes `fallback_used` and `fallback_reason` so clients always know which engine produced the analysis.
- The scraper runs as a daemon thread via APScheduler — it starts automatically when the Flask app boots and does not block the main server.
- Internships are de-duplicated by `apply_url` during upsert, so repeated scraper runs never create duplicate entries.
