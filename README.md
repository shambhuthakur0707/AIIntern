# 🤖 AIIntern — Agentic AI Internship Matcher

> An AI-powered internship recommendation system built with a **LangChain agentic architecture**, Flask, MongoDB, React, and GPT-4o.

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                  React Frontend                     │
│   Login → Register → Dashboard → Run AI Agent       │
└──────────────────────┬──────────────────────────────┘
                       │ JWT + Axios
┌──────────────────────▼──────────────────────────────┐
│              Flask REST API (Python)                │
│   /api/auth/register   /api/auth/login              │
│   /api/agent/match     /api/dashboard               │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│           LangChain Agent (GPT-4o)                  │
│                                                     │
│  User Profile                                       │
│       │                                             │
│       ▼                                             │
│  [1] FetchInternshipsTool  ← MongoDB                │
│  [2] SkillMatchTool        ← TF-IDF Cosine          │
│  [3] SkillGapAnalysisTool  ← Set Difference         │
│  [4] Rank + GPT-4o Reason  ← Structured JSON        │
│       │                                             │
│       ▼                                             │
│  Top 5 Recommendations with:                        │
│  • Match Score  • Reasoning  • Missing Skills       │
│  • Learning Roadmap  • Confidence Score             │
└──────────────────────┬──────────────────────────────┘
                       │
              ┌────────▼────────┐
              │   MongoDB       │
              │  users coll.    │
              │  internships    │
              └─────────────────┘
```

---

## 📁 Project Structure

```
AIIntern/
├── backend/
│   ├── app.py                    # Flask app factory
│   ├── config.py                 # Environment config
│   ├── seed.py                   # Database seeder
│   ├── requirements.txt
│   ├── .env.example
│   ├── agents/
│   │   └── internship_agent.py   # LangChain agent
│   ├── tools/
│   │   ├── db_tool.py            # FetchInternshipsTool
│   │   ├── skill_match_tool.py   # SkillMatchTool (TF-IDF)
│   │   └── skill_gap_tool.py     # SkillGapAnalysisTool
│   ├── routes/
│   │   ├── auth_routes.py        # POST /register /login
│   │   ├── agent_routes.py       # POST /agent/match
│   │   └── dashboard_routes.py   # GET  /dashboard
│   ├── models/
│   │   ├── user_model.py
│   │   └── internship_model.py
│   ├── services/
│   │   └── user_service.py
│   └── utils/
│       ├── jwt_utils.py
│       └── response_utils.py
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── tailwind.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        ├── api/axios.js
        ├── context/AuthContext.jsx
        ├── pages/
        │   ├── LoginPage.jsx
        │   ├── RegisterPage.jsx
        │   └── DashboardPage.jsx
        └── components/
            ├── Navbar.jsx
            ├── InternshipCard.jsx
            ├── ProgressBar.jsx
            ├── RoadmapTimeline.jsx
            └── SkillBadge.jsx
```

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10+
- Node.js 18+
- MongoDB (running locally on port 27017, or use MongoDB Atlas URI)
- OpenAI API key with GPT-4o access

---

### 1. Clone & Configure Environment
```bash
cd backend
copy .env.example .env
```

Edit `.env` and fill in:
```
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=aiintern_db
JWT_SECRET_KEY=your-super-secret-key-here
OPENAI_API_KEY=sk-your-openai-key-here
```

---

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Seed the database (10 internships + 2 sample users)
python seed.py

# Start Flask server
python app.py
```

Backend runs at: `http://localhost:5000`

---

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

### 4. Demo Login

After seeding, use these credentials:

| Name | Email | Password |
|---------|----------------------|-------------|
| Aryan Sharma | aryan@example.com | password123 |
| Priya Singh  | priya@example.com  | password123 |

---

## 🔌 API Reference

### Auth

| Method | Endpoint | Body |
|--------|--------------------------|------|
| POST | `/api/auth/register` | `name, email, password, skills[], interests[], experience_level, education` |
| POST | `/api/auth/login` | `email, password` |

### Agent & Dashboard

| Method | Endpoint | Auth | Description |
|--------|--------------------------|------|-------------|
| POST | `/api/agent/match` | JWT | Runs the LangChain agent, returns top-5 recommendations |
| GET | `/api/dashboard` | JWT | Returns user profile + last match result |

### Sample Response — `/api/agent/match`

```json
{
  "success": true,
  "data": {
    "match_result": {
      "overall_ai_summary": "Aryan has strong Python and ML fundamentals...",
      "confidence_score": 78.5,
      "recommendations": [
        {
          "rank": 1,
          "internship_title": "Machine Learning Engineer Intern",
          "company": "DeepMind Labs",
          "match_score": 87.3,
          "reasoning": "Aryan's Python and Scikit-learn skills align...",
          "missing_skills": ["TensorFlow", "PyTorch"],
          "recommendation_summary": "Apply immediately — your ML foundation is a strong fit.",
          "roadmap": [
            { "skill": "TensorFlow", "resource": "TensorFlow official tutorials", "week_start": 1, "week_end": 2 }
          ],
          "total_learning_weeks": 3
        }
      ]
    }
  }
}
```

---

## 🧠 Agent Tool Descriptions

| Tool | Description |
|------|-------------|
| `FetchInternshipsTool` | Queries MongoDB and returns all internship documents as JSON |
| `SkillMatchTool` | Computes TF-IDF cosine similarity between user skills and required skills (0–100) |
| `SkillGapAnalysisTool` | Set-difference analysis; maps each missing skill to a curated resource + week estimate |

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Agent | LangChain + OpenAI GPT-4o |
| Backend | Python, Flask, Flask-JWT-Extended |
| Database | MongoDB (PyMongo) |
| ML Scoring | Scikit-learn TF-IDF |
| Frontend | React 18, Vite, Tailwind CSS v3 |
| HTTP Client | Axios |
| Auth | JWT (HS256) + bcrypt |

---

## 📝 Notes for Academic Submission

- The system uses a **ReAct-style LangChain OpenAI Functions agent** — not a simple API wrapper
- The agent autonomously decides **how many tool calls to make** and in what order
- Skill matching uses **TF-IDF cosine similarity** (scikit-learn) — a genuine ML technique
- Skill gap roadmap is generated from a **curated resource database** + set arithmetic
- GPT-4o provides **natural language reasoning** for each recommendation
- All results are **persisted to MongoDB** and restored on next dashboard load
