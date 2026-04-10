"""Routes for triage endpoints"""

import time
from fastapi import APIRouter, HTTPException, Query
from src.models.schemas import SymptomInput
from src.agents.orchestrator_agent import OrchestratorAgent
from src.services.symptom_processor import SymptomProcessor
from src.services.ml_predictor import MLPredictor

router = APIRouter(prefix="/api/triage", tags=["triage"])

# Singletons — initialized once at import time
orchestrator = OrchestratorAgent()
symptom_processor = SymptomProcessor()
ml_predictor = MLPredictor()


@router.post("/assess")
async def assess_symptoms(symptom_input: SymptomInput):
    """
    Triage assessment endpoint.

    POST /api/triage/assess
    Body: SymptomInput (symptoms required; patient_age, medications, allergies, etc. optional)
    Returns: Full triage decision, routing guidance, and pharmaceutical recommendations.
    """
    # Validate that symptoms contain recognizable content
    if not symptom_processor.validate_input(symptom_input.symptoms):
        raise HTTPException(
            status_code=422,
            detail="Please describe your symptoms in more detail (e.g., 'I have fever and headache')"
        )

    try:
        # ── Step 1: Parse symptoms → binary feature vector ─────────────────
        parsed = symptom_processor.parse_symptoms(symptom_input.symptoms)
        feature_vector = parsed['feature_vector']

        # ── Step 2: ML prediction → P(Disease | Symptoms) ─────────────────
        disease_probs = ml_predictor.predict(feature_vector)
        disease_probs = ml_predictor.rank_by_probability(disease_probs)

        # ── Step 3: Orchestrate agents (Triage → Pharma → Routing) ────────
        orchestrator_input = {
            'symptoms': symptom_input.symptoms,
            'disease_probabilities': disease_probs,
            'patient_age': symptom_input.patient_age,
            'current_medications': symptom_input.current_medications or [],
            'allergies': symptom_input.allergies or [],
            'comorbidities': symptom_input.comorbidities or [],
            'patient_location': symptom_input.patient_location or '',
            'mobility_status': symptom_input.mobility_status or 'Mobile',
        }

        triage_response = orchestrator.process(orchestrator_input)

        # Attach ML metadata to response
        triage_response['ml_features'] = {
            'extracted_symptoms': parsed['extracted_symptoms'],
            'severity_indicators': parsed['severity_indicators'],
            'model_loaded': ml_predictor.is_model_loaded,
        }
        triage_response['disease_probabilities'] = [
            {'condition': c, 'probability': round(p, 4)} for c, p in disease_probs
        ]

        return triage_response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Triage processing error: {str(e)}")


@router.get("/health")
async def triage_health():
    """Check triage service health including model status."""
    return {
        "status": "healthy",
        "model_loaded": ml_predictor.is_model_loaded,
        "conditions_supported": ["Pneumonia", "Typhoid", "Malaria"],
        "features_count": len(symptom_processor.feature_cols),
    }


@router.get("/history/{patient_id}")
async def get_triage_history(patient_id: str):
    """Get triage history for a patient (placeholder — connect to DB when available)."""
    return {
        'patient_id': patient_id,
        'history': [],
        'note': 'Persistent history requires database configuration'
    }
