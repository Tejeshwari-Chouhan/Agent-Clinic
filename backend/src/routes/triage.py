"""Routes for triage endpoints"""

from fastapi import APIRouter, HTTPException
from src.models.schemas import SymptomInput
from src.agents.orchestrator_agent import OrchestratorAgent
from src.services.symptom_processor import SymptomProcessor
from src.services.ml_predictor import MLPredictor

router = APIRouter(prefix="/api/triage", tags=["triage"])

# Initialize agents and services
orchestrator = OrchestratorAgent()
symptom_processor = SymptomProcessor()
ml_predictor = MLPredictor()

@router.post("/assess")
async def assess_symptoms(symptom_input: SymptomInput):
    """
    Assess symptoms and return comprehensive triage decision
    POST /api/triage/assess
    
    Request body:
    {
        'symptoms': str,
        'patient_age': int (optional),
        'current_medications': [str] (optional),
        'allergies': [str] (optional),
        'comorbidities': [str] (optional),
        'patient_location': str (optional)
    }
    """
    try:
        # Process symptoms
        processed_symptoms = symptom_processor.parse_symptoms(symptom_input.symptoms)
        
        # Get ML predictions
        disease_probs = ml_predictor.predict(processed_symptoms)
        disease_probs = ml_predictor.rank_by_probability(disease_probs)
        
        # Prepare orchestrator input
        orchestrator_input = {
            'symptoms': symptom_input.symptoms,
            'disease_probabilities': disease_probs,
            'patient_age': symptom_input.patient_age,
            'current_medications': symptom_input.current_medications or [],
            'allergies': getattr(symptom_input, 'allergies', []),
            'comorbidities': getattr(symptom_input, 'comorbidities', []),
            'patient_location': getattr(symptom_input, 'patient_location', ''),
            'mobility_status': getattr(symptom_input, 'mobility_status', 'Mobile')
        }
        
        # Get comprehensive triage response from orchestrator
        triage_response = orchestrator.process(orchestrator_input)
        
        return triage_response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history/{patient_id}")
async def get_triage_history(patient_id: str):
    """Get triage history for a patient"""
    try:
        # Placeholder implementation
        return {
            'patient_id': patient_id,
            'history': []
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
