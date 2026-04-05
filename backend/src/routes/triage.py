"""Routes for triage endpoints"""

from fastapi import APIRouter, HTTPException
from src.models.schemas import SymptomInput, PatientContextInput, ContextPromptInput
from src.agents.orchestrator_agent import OrchestratorAgent
from src.agents.context_intake_agent import ContextIntakeAgent
from src.services.symptom_processor import SymptomProcessor
from src.services.ml_predictor import MLPredictor
from src.services.patient_context_store import PatientContextStore

router = APIRouter(prefix="/api/triage", tags=["triage"])

# Initialize agents and services
orchestrator = OrchestratorAgent()
symptom_processor = SymptomProcessor()
ml_predictor = MLPredictor()
patient_context_store = PatientContextStore()
context_intake_agent = ContextIntakeAgent()

@router.post("/assess", responses={400: {"description": "Bad request"}})
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
        stored_context = {}
        if symptom_input.patient_id:
            stored_context = patient_context_store.get(symptom_input.patient_id)

        # Process symptoms
        processed_symptoms = symptom_processor.parse_symptoms(symptom_input.symptoms)
        
        # Get ML predictions
        disease_probs = ml_predictor.predict(processed_symptoms)
        disease_probs = ml_predictor.validate_with_patient_context(disease_probs, stored_context)
        disease_probs = ml_predictor.rank_by_probability(disease_probs)

        merged_medications = list(
            dict.fromkeys([*(stored_context.get('medications', []) or []), *(symptom_input.current_medications or [])])
        )
        merged_allergies = list(
            dict.fromkeys([*(stored_context.get('allergies', []) or []), *(symptom_input.allergies or [])])
        )
        merged_comorbidities = list(
            dict.fromkeys([*(stored_context.get('known_conditions', []) or []), *(symptom_input.comorbidities or [])])
        )
        
        # Prepare orchestrator input
        orchestrator_input = {
            'symptoms': symptom_input.symptoms,
            'disease_probabilities': disease_probs,
            'patient_age': symptom_input.patient_age,
            'current_medications': merged_medications,
            'allergies': merged_allergies,
            'comorbidities': merged_comorbidities,
            'patient_location': getattr(symptom_input, 'patient_location', ''),
            'mobility_status': getattr(symptom_input, 'mobility_status', 'Mobile'),
            'test_reports': stored_context.get('test_reports', []),
            'known_conditions': stored_context.get('known_conditions', []),
            'context_notes': stored_context.get('context_notes', []),
        }
        
        # Get comprehensive triage response from orchestrator
        triage_response = orchestrator.process(orchestrator_input)
        
        return triage_response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/context", responses={400: {"description": "Bad request"}})
async def upsert_patient_context(context_input: PatientContextInput):
    """
    Store patient context data for later triage validation.
    POST /api/triage/context
    """
    try:
        stored = patient_context_store.upsert(
            context_input.patient_id,
            {
                'test_reports': context_input.test_reports or [],
                'medications': context_input.medications or [],
                'allergies': context_input.allergies or [],
                'known_conditions': context_input.known_conditions or [],
                'context_notes': context_input.context_notes or [],
            },
        )
        return {'status': 'ok', 'context': stored}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/context/prompt", responses={400: {"description": "Bad request"}})
async def upsert_patient_context_from_prompt(prompt_input: ContextPromptInput):
    """
    Use prompt text to detect and store patient context automatically.
    POST /api/triage/context/prompt
    """
    try:
        intake_result = context_intake_agent.process({'prompt': prompt_input.prompt})
        if intake_result.get('action') != 'store_context':
            return {
                'status': 'ok',
                'action': 'no_action',
                'message': intake_result.get('message', 'No context update applied.'),
            }

        stored = patient_context_store.upsert(prompt_input.patient_id, intake_result.get('context', {}))
        return {
            'status': 'ok',
            'action': 'stored',
            'message': intake_result.get('message', 'Patient context stored.'),
            'context': stored,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/history/{patient_id}", responses={400: {"description": "Bad request"}})
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
