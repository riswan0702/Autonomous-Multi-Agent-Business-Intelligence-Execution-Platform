# 🤖 Autonomous Multi-Agent Business Intelligence & Execution Platform

> A production-grade AI system where 5 specialized agents collaborate autonomously to research, strategize, critique, plan, and validate complete business intelligence reports — in under 60 seconds.

---

## 🎯 What It Does

Give the platform a company description, product, audience, goals, and constraints.  
It spins up a pipeline of 5 AI agents that work together like a small consulting firm:

**Input:**
> *"We are launching an AI-powered fitness app for working professionals in India. Create a GTM strategy, competitor analysis, pricing strategy, content plan, and growth experiments."*

**Output:** A full BI report with:
- 📊 Market sizing (TAM/SAM/SOM) + 6-competitor analysis
- 🎯 GTM strategy with pricing tiers, channels, and messaging
- 🗓️ 90-day execution roadmap (week-by-week tasks with owners)
- 🔍 Hallucination check + assumption audit + confidence scores
- ✅ QA scorecard with APPROVED / NEEDS REVISION verdict

**Actual result:** QA Score 72/100 — generated in ~30 seconds using ~9,000 tokens.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Input (React UI)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │ POST /api/run
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python 3.11)                   │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Orchestrator Agent                       │  │
│  │  Controls workflow · Loop detection · Retry logic     │  │
│  └──────┬──────────┬───────────┬────────────┬───────────┘  │
│         │          │           │            │               │
│         ▼          ▼           ▼            ▼               │
│  ┌────────┐  ┌──────────┐  ┌───────┐  ┌────────┐          │
│  │Research│→ │ Strategy │→ │Critic │→ │Planner │→ QA       │
│  │ Agent  │  │  Agent   │  │ Agent │  │ Agent  │  Agent    │
│  │ 70b    │  │   70b    │  │  8b   │  │  8b    │  8b       │
│  └────────┘  └──────────┘  └───────┘  └────────┘          │
│         │                                                   │
│         ▼                                                   │
│  ┌──────────────────┐                                      │
│  │  Memory Agent    │ (ChromaDB — persistent vector store) │
│  └──────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
                      │ SSE stream
                      ▼
┌─────────────────────────────────────────────────────────────┐
│           React Dashboard (real-time agent timeline)        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent Roles

| Agent | Responsibility | Model |
|-------|---------------|-------|
| **Orchestrator** | Controls workflow, delegation, failure recovery | — |
| **Research Agent** | Market sizing, competitor matrix, audience deep-dive | llama-3.3-70b |
| **Strategy Agent** | GTM strategy, pricing tiers, growth loops, content plan | llama-3.3-70b |
| **Critic Agent** | Hallucination check, logic gaps, assumption audit, confidence score | llama-3.1-8b |
| **Planner Agent** | 90-day execution roadmap, growth experiments, KPIs | llama-3.1-8b |
| **QA Agent** | Completeness scorecard, goals alignment, final verdict | llama-3.1-8b |
| **Memory Agent** | ChromaDB vector store — persists and retrieves past runs | — |

**LLM Routing:** Heavy reasoning tasks (Research, Strategy) → `llama-3.3-70b-versatile`. Fast tasks (Critic, Planner, QA) → `llama-3.1-8b-instant`. This cuts cost and latency significantly.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Free [Groq API key](https://console.groq.com)

### Backend Setup

```bash
# 1. Go into the backend folder
cd backend

# 2. Create virtual environment
python -m venv venv

# Windows CMD:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key in .env
# Open backend/.env and confirm:
# GROQ_API_KEY=your_key_here

# 5. Start the backend
python main.py
```

Backend runs at: **http://localhost:8000**  
API docs at: **http://localhost:8000/docs**

### Frontend Setup (new terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at: **http://localhost:5173**

### Run Your First Analysis

Open http://localhost:5173, fill in the form, click **Launch Multi-Agent Analysis**.

Watch 5 agents run in real-time on the **Agent Timeline** tab, then see the full report on the **Report** tab.

---

## ⚙️ Configuration

All config lives in `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | *(required)* | Free key from console.groq.com |
| `MAX_TOKENS_PER_RUN` | `80000` | Token budget — prevents cost runaway |
| `MAX_AGENT_LOOPS` | `10` | Max agent iterations — prevents infinite loops |
| `ENABLE_MEMORY` | `true` | ChromaDB persistent memory |
| `MEMORY_PATH` | `./memory_store` | Where memories are stored on disk |
| `ENVIRONMENT` | `development` | Set to `production` to disable hot-reload |

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/run` | Start a new BI workflow |
| `GET` | `/api/run/{id}/stream` | SSE stream of real-time agent events |
| `GET` | `/api/run/{id}` | Get status + final report |
| `GET` | `/api/runs` | List all past runs |
| `GET` | `/api/run/{id}/logs` | Full agent logs |
| `GET` | `/health` | Health check |

### Example Request

```bash
curl -X POST http://localhost:8000/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "company": "FitAI India",
    "product": "AI-powered fitness app for workout tracking, nutrition, and stress management",
    "target_audience": "Working professionals aged 25-40 in Tier 1 Indian cities",
    "goals": "10,000 paying users in 6 months, sustainable growth",
    "constraints": "Bootstrap budget under ₹50L, team of 5"
  }'
```

---

## 🛡️ Security Features

| Feature | Implementation |
|---------|---------------|
| **Prompt injection detection** | Regex pattern matching on all user inputs |
| **Input sanitization** | Control character removal, whitespace normalization |
| **Rate limiting** | 20 requests/hour per IP (in-memory) |
| **Agent loop detection** | Configurable max iterations per agent per run |
| **Token budget protection** | Hard stop at `MAX_TOKENS_PER_RUN` |
| **Sensitive data redaction** | API keys stripped from all log output |

---

## 🔍 Observability

Every agent run is fully traced:
- ✅ Start time, end time, latency (ms)
- ✅ Token usage (input + output, per agent)
- ✅ Model used per agent
- ✅ Output preview (first 300 chars, redacted)
- ✅ Error messages and retry counts
- ✅ Structured JSON logs

All visible in the **Logs** tab of the dashboard and at `GET /api/run/{id}/logs`.

---

## 🧱 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI + Python 3.11 |
| LLM Provider | [Groq](https://console.groq.com) (OpenAI-compatible, free tier) |
| LLM Models | llama-3.3-70b-versatile + llama-3.1-8b-instant |
| Vector Memory | [ChromaDB](https://www.trychroma.com/) (local, persistent) |
| Frontend | React + Vite |
| Streaming | Server-Sent Events (SSE) |
| Retry Logic | Exponential backoff with model fallback |
| Security | Custom prompt injection + rate limiting |
| Deployment | Docker + docker-compose |

---

## 📁 Project Structure

```
agent-bi-gemini/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt           # Python dependencies
│   ├── .env                       # Environment variables (set GROQ_API_KEY here)
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                # Abstract base agent
│   │   ├── orchestrator.py        # Workflow controller
│   │   ├── research.py            # Market research agent
│   │   ├── strategy.py            # GTM strategy agent
│   │   ├── critic.py              # Critic / hallucination checker
│   │   ├── planner.py             # Execution planner
│   │   └── qa.py                  # QA validator
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py              # All API endpoints + SSE streaming
│   ├── core/
│   │   ├── __init__.py
│   │   ├── llm_router.py          # Model selection + Groq API calls
│   │   ├── schemas.py             # Pydantic models
│   │   └── security.py            # Injection detection, rate limiting
│   ├── memory/
│   │   ├── __init__.py
│   │   └── vector_store.py        # ChromaDB memory agent
│   └── observability/
│       ├── __init__.py
│       └── tracer.py              # Agent tracing + token tracking
├── frontend/
│   ├── src/
│   │   └── pages/Dashboard.jsx    # Main React dashboard
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🐳 Docker Deployment

```bash
# Copy env file
cp .env.example .env
# Edit .env and set GROQ_API_KEY

# Build and run
docker-compose up --build

# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
```

---

## 💡 Design Decisions

**Why Groq instead of OpenAI/Gemini?**  
Groq's free tier has no credit card requirement and provides very fast inference (typically <5s per agent). The OpenAI-compatible API means minimal code changes if you want to switch providers later.

**Why separate models for different tasks?**  
Using `llama-3.3-70b` only for heavy reasoning (Research + Strategy) and `llama-3.1-8b` for fast tasks (Critic, Planner, QA) cuts total token cost by ~40% and reduces overall latency by ~30%.

**Why ChromaDB?**  
It runs locally with no external service required, persists to disk, and handles semantic similarity search out of the box. Future runs benefit from relevant past research stored in memory.

**Why SSE instead of WebSockets?**  
SSE is simpler (standard HTTP), one-directional (server → client), and works through proxies and load balancers without special configuration.

---

## 🔮 Potential Improvements

- [ ] Live web search integration (Tavily/Serper) for real-time competitor data
- [ ] PDF export of final report
- [ ] Redis-backed event queue (replace in-memory asyncio.Queue)
- [ ] Authentication (JWT)
- [ ] LangSmith / OpenTelemetry tracing
- [ ] Parallel agent execution where dependencies allow
- [ ] Cloud deployment (Railway / Render / AWS)

---

## 📄 License

MIT — free to use, modify, and distribute.
