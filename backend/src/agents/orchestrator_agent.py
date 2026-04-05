"""Orchestrator Agent - Coordinates all agents and manages the triage workflow"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
from src.agents.triage_decision_agent import TriageDecisionAgent
from src.agents.pharmaceutical_agent import PharmaceuticalAgent
from src.agents.routing_agent import RoutingAgent
import json

class OrchestratorAgent(BaseAgent):
    """Master agent that orchestrates the entire triage workflow"""

    RED_FLAG_KEYWORDS = [
        'chest pain',
        'shortness of breath',
        'trouble breathing',
        'difficulty breathing',
        'stroke',
        'slurred speech',
        'one sided weakness',
        'unconscious',
        'fainting',
        'seizure',
        'severe bleeding',
        'vomiting blood',
        'blood in vomit',
        'suicidal',
        'severe allergic reaction',
        'anaphylaxis',
    ]
    PATHWAY_EMERGENCY = 'Emergency'
    PATHWAY_URGENT_CARE = 'Urgent Care'
    PATHWAY_SELF_CARE = 'Self-Care'
    
    def __init__(self):
        system_prompt = """You are the master orchestrator agent for the healthcare triage system. Your role is to:
1. Coordinate all specialized agents (Triage Decision, Pharmaceutical, Routing)
2. Synthesize their outputs into a cohesive triage response
3. Ensure consistency and safety across all recommendations
4. Provide a comprehensive patient guidance package

You manage the workflow:
1. Triage Decision Agent analyzes disease probabilities
2. Pharmaceutical Agent provides medication recommendations
3. Routing Agent determines care pathway
4. You synthesize all outputs into final guidance"""
        
        super().__init__('OrchestratorAgent', system_prompt)
        
        # Initialize specialized agents
        self.triage_agent = TriageDecisionAgent()
        self.pharma_agent = PharmaceuticalAgent()
        self.routing_agent = RoutingAgent()
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate the complete triage workflow
        
        Input:
        {
            'symptoms': str,
            'disease_probabilities': [('condition', probability), ...],
            'patient_age': int (optional),
            'current_medications': [str] (optional),
            'allergies': [str] (optional),
            'comorbidities': [str] (optional),
            'patient_location': str (optional)
        }
        
        Output:
        {
            'triage_decision': {...},
            'pharmaceutical_recommendations': {...},
            'routing_guidance': {...},
            'patient_summary': str,
            'next_steps': [str],
            'warnings': [str]
        }
        """
        
        normalized_input = self._normalize_input(input_data)
        decision_trace = {
            'safety_override_triggered': False,
            'override_keywords': [],
            'triage_confidence': None,
            'fallback_used': False,
            'pharma_invoked': False,
        }

        # Step 1: triage decision with deterministic emergency override
        override = self._safety_override(normalized_input.get('symptoms', ''))
        if override:
            triage_decision = override
            decision_trace['safety_override_triggered'] = True
            decision_trace['override_keywords'] = override.get('matched_keywords', [])
        else:
            triage_input = {
                'disease_probabilities': normalized_input.get('disease_probabilities', []),
                'symptoms': normalized_input.get('symptoms', ''),
                'patient_age': normalized_input.get('patient_age'),
                'comorbidities': normalized_input.get('comorbidities', []),
                'test_reports': normalized_input.get('test_reports', []),
                'known_conditions': normalized_input.get('known_conditions', []),
            }
            try:
                raw_triage = self.triage_agent.process(triage_input)
            except Exception:
                raw_triage = {}
            triage_decision = self._validate_triage_output(
                raw_triage, normalized_input.get('disease_probabilities', [])
            )
            decision_trace['fallback_used'] = triage_decision.get('_fallback_used', False)
            decision_trace['triage_confidence'] = triage_decision.get('confidence_score')

        triage_decision.pop('matched_keywords', None)
        triage_decision.pop('_fallback_used', None)

        # Step 2: routing guidance
        routing_input = {
            'severity_level': triage_decision.get('severity_level', ''),
            'condition': triage_decision.get('primary_condition', ''),
            'patient_location': normalized_input.get('patient_location', ''),
            'comorbidities': normalized_input.get('comorbidities', []),
            'mobility_status': normalized_input.get('mobility_status', 'Mobile')
        }
        try:
            raw_routing = self.routing_agent.process(routing_input)
        except Exception:
            raw_routing = {}
        routing_guidance = self._validate_routing_output(
            raw_routing, triage_decision.get('severity_level', 'Medium')
        )

        # Step 3: pharmaceutical recommendations only for low/medium
        if triage_decision.get('severity_level') in ['Medium', 'Low']:
            pharma_input = {
                'condition': triage_decision.get('primary_condition', ''),
                'severity': triage_decision.get('severity_level', ''),
                'current_medications': normalized_input.get('current_medications', []),
                'allergies': normalized_input.get('allergies', []),
                'patient_age': normalized_input.get('patient_age'),
            }
            try:
                pharma_recommendations = self.pharma_agent.process(pharma_input)
            except Exception:
                pharma_recommendations = {
                    'recommendations': [],
                    'drug_interactions': [],
                    'otc_alternatives': [],
                    'warnings': ['Unable to generate pharmaceutical guidance. Consult a clinician.'],
                }
            decision_trace['pharma_invoked'] = True
        else:
            pharma_recommendations = {
                'recommendations': [],
                'drug_interactions': [],
                'otc_alternatives': [],
                'warnings': [
                    'High-severity case detected. Seek emergency care immediately before self-medication.'
                ],
            }

        # Step 4: Synthesize all outputs
        synthesis_prompt = f"""Synthesize the following triage components into a comprehensive patient guidance:

Triage Decision: {json.dumps(triage_decision)}
Pharmaceutical Recommendations: {json.dumps(pharma_recommendations)}
Routing Guidance: {json.dumps(routing_guidance)}

Provide a patient-friendly summary and clear next steps."""
        
        try:
            synthesis = self.get_response(synthesis_prompt)
        except Exception:
            synthesis = self._build_fallback_summary(triage_decision, routing_guidance)
        
        return {
            'triage_decision': triage_decision,
            'pharmaceutical_recommendations': pharma_recommendations,
            'routing_guidance': routing_guidance,
            'patient_summary': synthesis,
            'next_steps': routing_guidance.get('pre_arrival_instructions', []),
            'warnings': triage_decision.get('safety_warnings', []),
            'decision_trace': decision_trace,
        }

    def _build_fallback_summary(self, triage_decision: Dict[str, Any], routing_guidance: Dict[str, Any]) -> str:
        """Provide summary when LLM synthesis is unavailable."""
        return (
            f"Severity: {triage_decision.get('severity_level', 'Unknown')}. "
            f"Likely condition: {triage_decision.get('primary_condition', 'Unknown')}. "
            f"Recommended action: {triage_decision.get('recommended_action', 'Consult a healthcare provider')}. "
            f"Routing: {routing_guidance.get('routing_pathway', 'Unknown')}."
        )

    def _normalize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize incoming data to stable defaults."""
        return {
            'symptoms': str(input_data.get('symptoms', '')).strip(),
            'disease_probabilities': input_data.get('disease_probabilities', []) or [],
            'patient_age': input_data.get('patient_age'),
            'current_medications': input_data.get('current_medications', []) or [],
            'allergies': input_data.get('allergies', []) or [],
            'comorbidities': input_data.get('comorbidities', []) or [],
            'patient_location': str(input_data.get('patient_location', '') or ''),
            'mobility_status': str(input_data.get('mobility_status', 'Mobile') or 'Mobile'),
            'test_reports': input_data.get('test_reports', []) or [],
            'known_conditions': input_data.get('known_conditions', []) or [],
            'context_notes': input_data.get('context_notes', []) or [],
        }

    def _safety_override(self, symptoms: str) -> Dict[str, Any]:
        """Deterministically classify obvious emergencies as high severity."""
        symptoms_lower = symptoms.lower()
        matched = [k for k in self.RED_FLAG_KEYWORDS if k in symptoms_lower]
        if not matched:
            return {}

        return {
            'severity_level': 'High',
            'primary_condition': 'Potential emergency condition',
            'confidence_score': 1.0,
            'reasoning': 'Emergency red-flag symptoms detected via deterministic safety policy.',
            'recommended_action': 'Call emergency services or go to the nearest emergency department now.',
            'safety_warnings': ['Do not delay care. If symptoms worsen, call emergency services immediately.'],
            'matched_keywords': matched,
            '_fallback_used': False,
        }

    def _validate_triage_output(
        self, triage_decision: Dict[str, Any], disease_probabilities: List[Any]
    ) -> Dict[str, Any]:
        """Validate triage response and fill safe defaults if malformed."""
        if not isinstance(triage_decision, dict):
            triage_decision = {}

        severity = triage_decision.get('severity_level', 'Medium')
        if severity not in ['High', 'Medium', 'Low']:
            severity = 'Medium'

        primary_condition = triage_decision.get('primary_condition')
        if not primary_condition:
            if disease_probabilities and isinstance(disease_probabilities[0], (list, tuple)):
                primary_condition = str(disease_probabilities[0][0])
            else:
                primary_condition = 'Unknown'

        confidence = triage_decision.get('confidence_score', 0.5)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))

        warnings = triage_decision.get('safety_warnings', [])
        if not isinstance(warnings, list):
            warnings = [str(warnings)] if warnings else []

        fallback_used = bool(
            not triage_decision
            or 'severity_level' not in triage_decision
            or 'recommended_action' not in triage_decision
        )

        return {
            'severity_level': severity,
            'primary_condition': primary_condition,
            'confidence_score': confidence,
            'reasoning': triage_decision.get('reasoning', 'Clinical triage reasoning unavailable.'),
            'recommended_action': triage_decision.get(
                'recommended_action', 'Consult a healthcare provider for further evaluation.'
            ),
            'safety_warnings': warnings,
            '_fallback_used': fallback_used,
        }

    def _validate_routing_output(self, routing_guidance: Dict[str, Any], severity: str) -> Dict[str, Any]:
        """Validate routing response and provide deterministic fallback."""
        if not isinstance(routing_guidance, dict):
            routing_guidance = {}

        pathway = routing_guidance.get('routing_pathway')
        if pathway not in [self.PATHWAY_EMERGENCY, self.PATHWAY_URGENT_CARE, self.PATHWAY_SELF_CARE]:
            if severity == 'High':
                pathway = self.PATHWAY_EMERGENCY
            elif severity == 'Low':
                pathway = self.PATHWAY_SELF_CARE
            else:
                pathway = self.PATHWAY_URGENT_CARE

        return {
            'routing_pathway': pathway,
            'facility_type': routing_guidance.get('facility_type', self._default_facility_type(pathway)),
            'pre_arrival_instructions': self._to_list(routing_guidance.get('pre_arrival_instructions')),
            'follow_up_guidance': self._to_list(routing_guidance.get('follow_up_guidance')),
            'emergency_contacts': self._to_list(routing_guidance.get('emergency_contacts')) or ['911'],
            'estimated_wait_time': routing_guidance.get('estimated_wait_time', 'Unknown'),
            'special_considerations': self._to_list(routing_guidance.get('special_considerations')),
        }

    def _default_facility_type(self, pathway: str) -> str:
        facility_map = {
            self.PATHWAY_EMERGENCY: 'Emergency Department',
            self.PATHWAY_URGENT_CARE: 'Urgent Care Center',
            self.PATHWAY_SELF_CARE: 'Pharmacy',
        }
        return facility_map.get(pathway, 'Healthcare Facility')

    def _to_list(self, value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if value:
            return [str(value)]
        return []
