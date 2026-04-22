# Agent-Clinic (Healthcare Triage System)

An intelligent healthcare **triage demonstrator**: natural-language symptoms, **machine-learned** disease probability hints, **deterministic** severity scoring and red-flag handling, and **LLM-based** agents for triage, routing, clinic guidance, and pharmacy-oriented messaging—coordinated by a single **orchestrator** pipeline.

**Scope:** This repository is a **prototype for education and evaluation**. It is **not** a regulated medical device and **does not** replace professional care. Optional patient context is sent **only with each assessment request**; the documented flow does **not** persist longitudinal medical records.

---

## Features

- Symptom text → structured features (**SymptomUnderstandingAgent**) for ML and downstream agents  
- **Decision-tree** disease probabilities (**MLPredictor**, scikit-learn) with on-disk model cache  
- **SeverityScoringAgent** (non-LLM score + High/Medium/Low) and **TriageDecisionAgent** (LLM), with orchestrator **severity merge** and **keyword red-flag override**  
- **High** severity: **EmergencyRoutingAgent** (regional dispatch numbers, ER / facility discovery via optional Google Maps)  
- **Non-High**: **RoutingAgent**, **ClinicAgent**, **PharmaceuticalAgent** (Medium/Low), optional **HospitalKnowledgeAgent**-style hints  
- **Patient summary** (Markdown-friendly) plus structured JSON for the UI (`agent_flow`, `decision_trace`, etc.)  
- **React** frontend: geolocation or India state/city fallback, `POST /api/triage/assess`, emergency vs non-emergency panels  

---

## Project structure

```
.
├── docs/                          # Project report, internal flow notes
├── frontend/                      # React + TypeScript + Vite
│   ├── src/
│   │   ├── App.tsx                # Main UI and triage API integration
│   │   └── lib/reverseGeocode.ts
│   ├── package.json
│   └── vite.config.ts             # Proxies /api → backend (VITE_PROXY_API)
├── backend/                       # FastAPI (Python 3)
│   ├── app.py                     # ASGI app entry
│   ├── config.py                  # Pydantic settings / env
│   ├── requirements.txt
│   ├── .env.example
│   ├── data/ml/                   # symptom_disease_training.csv (ML)
│   ├── scripts/
│   │   └── build_symptom_ml_dataset.py   # Regenerate training CSV
│   └── src/
│       ├── agents/
│       │   ├── base_agent.py
│       │   ├── orchestrator_agent.py
│       │   ├── symptom_understanding_agent.py
│       │   ├── severity_scoring_agent.py
│       │   ├── triage_decision_agent.py
│       │   ├── routing_agent.py
│       │   ├── emergency_routing_agent.py
│       │   ├── clinic_agent.py
│       │   ├── pharmaceutical_agent.py
│       │   └── hospital_knowledge_agent.py
│       ├── services/
│       │   ├── ml_predictor.py
│       │   └── emergency_router.py
│       ├── models/schemas.py
│       └── routes/triage.py       # POST /api/triage/assess
└── agent-clinic/documents/specs/  # Legacy design/requirements notes
```

---

## Prerequisites

- **Node.js** 18+  
- **Python** 3.10+ (recommended)  
- **OpenAI API key** (or compatible usage via the client) for LLM agents and optional hospital suggestions  
- **Google Maps API key** (optional): richer place-based emergency routing when configured  

---

## Getting started

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Dev server: **http://localhost:5173** — requests to `/api` are proxied to the backend (default **http://127.0.0.1:3000**; override with `VITE_PROXY_API` in `.env`).

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # edit OPENAI_API_KEY, optional keys
python app.py
```

Or explicitly:

```bash
uvicorn app:app --host 0.0.0.0 --port 3000 --reload
```

- **API base:** `http://localhost:3000` (or `PORT` from `.env`)  
- **Interactive docs:** `http://localhost:3000/docs`  
- **Health:** `GET /api/health`  
- **Triage:** `POST /api/triage/assess` — JSON body matches **`SymptomInput`** in `backend/src/models/schemas.py` (required: symptoms, patient_age; optional: location, medications, allergies, comorbidities, etc.)  

Regenerate synthetic ML data (from `backend/`):

```bash
python scripts/build_symptom_ml_dataset.py
```

If the training CSV changes, the predictor refreshes the cached model when the file’s modification time changes.

---

## Technology stack

| Layer | Stack |
|--------|--------|
| Frontend | React 19, TypeScript, Vite, Axios, Zustand, react-markdown |
| Backend | FastAPI, Uvicorn, Pydantic / pydantic-settings, OpenAI Python SDK |
| ML | scikit-learn (DecisionTreeClassifier), pandas, numpy |
| CORS | Configurable via `CORS_ORIGIN` (default `http://localhost:5173`) |

Default LLM model is controlled by **`OPENAI_MODEL`** in `.env` (see `.env.example`; commonly `gpt-4o-mini`). Not every agent is LLM-only (e.g. **SeverityScoringAgent** is rule-based).

---

## Agent pipeline (high level)

Order is fixed in **`OrchestratorAgent.process`**: symptom understanding → **MLPredictor** → severity scoring → red-flag safety branch → triage (unless overridden) → **merge severity** → emergency vs non-emergency branches → patient summary.

For a concise description suitable for coursework or handoff, see **`docs/Agent-Clinic-Project-Report.md`**.

---

## Performance targets (engineering goals)

Targets stated for a production-oriented product; **measure and report** your own numbers on this codebase.

| Metric | Target |
|--------|--------|
| F1-score | ≥ 0.75 (on agreed evaluation tasks) |
| Triage latency | Under 3 seconds for 95% of cases |
| Emergency recall | ≥ 0.95 |
| Emergency routing | Under 2 seconds |

---

## Security and privacy (read carefully)

Production healthcare systems require **TLS**, **access control**, **audit logging**, **BAA** / regulatory alignment where applicable, and **no sensitive data in logs**. This repo is a **development prototype**: treat **HIPAA-style** or “compliant” wording in older copy as **design goals**, not certifications of this repository.

---

## License

Proprietary — Agent-Clinic / Healthcare Triage System.
