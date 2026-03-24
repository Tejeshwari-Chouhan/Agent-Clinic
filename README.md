# Healthcare Triage System

An intelligent healthcare intermediary system that synthesizes natural language symptom input, predicts disease probability using machine learning, and orchestrates appropriate clinical actions through an LLM-based agent.

## Project Structure

```
.
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── backend/                  # Python Flask backend
│   ├── src/
│   │   ├── agents/          # LLM-based agents
│   │   │   ├── base_agent.py
│   │   │   ├── triage_decision_agent.py
│   │   │   ├── pharmaceutical_agent.py
│   │   │   ├── routing_agent.py
│   │   │   └── orchestrator_agent.py
│   │   ├── services/        # Business logic services
│   │   ├── models/          # Data schemas
│   │   └── routes/          # API endpoints
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   └── .env.example
└── specs/             # Specification documents
    └── healthcare-triage-system/
        ├── requirements.md
        ├── design.md
        └── tasks.md
```

## Getting Started

### Prerequisites
- Node.js 18+
- npm or yarn

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Update .env with your API keys
python app.py
```

Backend runs on `http://localhost:3000` with interactive API docs at `http://localhost:3000/docs`

## Features

- Natural language symptom input processing
- ML-based disease probability prediction
- LLM-based triage agent decision-making
- Emergency routing with Google Maps integration
- Pharmaceutical guidance with drug interaction checking
- Severity-based patient routing
- Closed-loop healthcare experience
- Performance metrics and monitoring
- HIPAA-compliant data privacy and security

## Development

### Frontend
- React 18 with TypeScript
- Vite for fast development
- Zustand for state management
- Axios for API calls

### Backend
- FastAPI with Python
- Uvicorn ASGI server
- OpenAI API integration for LLM-based agents
- Google Maps API integration
- Scikit-learn for ML models
- Pydantic for data validation
- CORS enabled for frontend communication
- Interactive API documentation (Swagger UI)

### Agents Architecture

The system uses a multi-agent architecture with specialized LLM-based agents:

1. **Orchestrator Agent** - Master coordinator that manages the entire workflow
2. **Triage Decision Agent** - Analyzes disease probabilities and makes severity classifications
3. **Pharmaceutical Agent** - Provides medication recommendations and drug interaction analysis
4. **Routing Agent** - Determines appropriate care pathways and coordinates routing

Each agent:
- Maintains conversation history for context
- Uses GPT-4 for intelligent decision-making
- Provides structured JSON outputs
- Includes fallback mechanisms for robustness

## Performance Targets

- F1-Score: ≥ 0.75
- Triage Latency: < 3 seconds (95% of cases)
- Emergency Case Recall: ≥ 0.95
- Emergency Routing: < 2 seconds

## Security

- TLS 1.2+ for data in transit
- AES-256 encryption for data at rest
- HIPAA compliance
- No PII in logs

## License

Proprietary - Healthcare Triage System
