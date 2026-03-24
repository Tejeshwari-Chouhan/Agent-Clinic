from pydantic import BaseModel
from typing import List, Optional

class SymptomInput(BaseModel):
    """Schema for symptom input"""
    symptoms: str
    patient_id: Optional[str] = None
    current_medications: Optional[List[str]] = None

class DiseaseProbability(BaseModel):
    """Schema for disease probability"""
    condition: str
    probability: float

class TriageDecision(BaseModel):
    """Schema for triage decision"""
    severity_level: str  # High, Medium, Low
    primary_condition: str
    disease_probabilities: List[DiseaseProbability]
    confidence_score: float
    reasoning: str
    recommended_action: str

class EmergencyRoutingInfo(BaseModel):
    """Schema for emergency routing information"""
    facility_name: str
    address: str
    phone: str
    distance_km: float
    estimated_time_minutes: int
    directions_url: str

class PharmaceuticalRecommendation(BaseModel):
    """Schema for pharmaceutical recommendation"""
    medication_name: str
    dosage: str
    frequency: str
    duration: str
    side_effects: List[str]
    contraindications: List[str]
    interaction_warnings: Optional[List[str]] = None
