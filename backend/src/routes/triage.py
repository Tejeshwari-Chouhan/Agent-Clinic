"""Routes for triage endpoints"""

from fastapi import APIRouter, HTTPException

from src.agents.orchestrator_agent import OrchestratorAgent
from src.models.schemas import SymptomInput

router = APIRouter(prefix="/api/triage", tags=["triage"])

orchestrator = OrchestratorAgent()


def _patient_context_from_request(symptom_input: SymptomInput) -> dict:
    """Structured context for ML validation only (from this request; no persisted history)."""
    return {
        "test_reports": [],
        "medications": symptom_input.current_medications or [],
        "allergies": symptom_input.allergies or [],
        "known_conditions": symptom_input.comorbidities or [],
        "context_notes": [],
    }


@router.post("/assess", responses={400: {"description": "Bad request"}})
async def assess_symptoms(symptom_input: SymptomInput):
    """
    Run the full agent pipeline: symptom understanding → ML → severity → orchestration.
    POST /api/triage/assess
    """
    try:
        patient_context = _patient_context_from_request(symptom_input)

        orchestrator_input = {
            "symptoms": symptom_input.symptoms,
            "patient_age": symptom_input.patient_age,
            "current_medications": patient_context["medications"],
            "allergies": patient_context["allergies"],
            "comorbidities": symptom_input.comorbidities or [],
            "patient_location": symptom_input.patient_location or "",
            "mobility_status": getattr(symptom_input, "mobility_status", "Mobile"),
            "patient_context": patient_context,
        }

        return orchestrator.process(orchestrator_input)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
