from pydantic import BaseModel, Field
from typing import List, Optional


class SymptomInput(BaseModel):
    """Schema for triage assessment input"""
    symptoms: str = Field(..., min_length=3, description="Patient symptom description in natural language")
    patient_id: Optional[str] = None
    patient_age: Optional[int] = Field(None, ge=0, le=120)
    current_medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    comorbidities: Optional[List[str]] = None
    patient_location: Optional[str] = None
    mobility_status: Optional[str] = "Mobile"  # Mobile | Immobile | Assisted


class DiseaseProbability(BaseModel):
    """Disease probability entry"""
    condition: str
    probability: float = Field(..., ge=0.0, le=1.0)


class SafetyWarning(BaseModel):
    """Clinical safety warning"""
    level: str  # critical | warning | info
    message: str


class TriageDecision(BaseModel):
    """Triage decision output"""
    severity_level: str        # High | Medium | Low
    primary_condition: str
    disease_probabilities: List[DiseaseProbability]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: str
    recommended_action: str
    safety_warnings: Optional[List[str]] = []


class PharmaceuticalRecommendation(BaseModel):
    """Single drug recommendation"""
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    side_effects: List[str]
    contraindications: List[str]
    interaction_warnings: Optional[List[str]] = None


class EmergencyRoutingInfo(BaseModel):
    """Emergency facility routing information"""
    facility_name: str
    address: str
    phone: str
    distance_km: float
    estimated_time_minutes: int
    directions_url: str


class RoutingGuidance(BaseModel):
    """Full routing guidance response"""
    routing_pathway: str          # Emergency | Urgent Care | Self-Care
    facility_type: str
    pre_arrival_instructions: List[str]
    follow_up_guidance: List[str]
    emergency_contacts: List[str]
    estimated_wait_time: str
    special_considerations: Optional[List[str]] = []
    nearby_facilities: Optional[List[EmergencyRoutingInfo]] = []


class TriageResponse(BaseModel):
    """Complete triage assessment response"""
    triage_decision: dict
    pharmaceutical_recommendations: Optional[dict] = None
    routing_guidance: dict
    patient_summary: str
    next_steps: List[str]
    warnings: List[str]
    model_used: Optional[str] = "GradientBoosting"
    processing_time_ms: Optional[float] = None
