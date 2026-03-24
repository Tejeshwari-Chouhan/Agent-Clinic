"""Orchestrator Agent - Coordinates all agents and manages the triage workflow"""

from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.agents.triage_decision_agent import TriageDecisionAgent
from src.agents.pharmaceutical_agent import PharmaceuticalAgent
from src.agents.routing_agent import RoutingAgent
import json

class OrchestratorAgent(BaseAgent):
    """Master agent that orchestrates the entire triage workflow"""
    
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
        
        # Step 1: Get triage decision
        triage_input = {
            'disease_probabilities': input_data.get('disease_probabilities', []),
            'symptoms': input_data.get('symptoms', ''),
            'patient_age': input_data.get('patient_age'),
            'comorbidities': input_data.get('comorbidities', [])
        }
        triage_decision = self.triage_agent.process(triage_input)
        
        # Step 2: Get pharmaceutical recommendations (for non-emergency cases)
        pharma_recommendations = {}
        if triage_decision.get('severity_level') in ['Medium', 'Low']:
            pharma_input = {
                'condition': triage_decision.get('primary_condition', ''),
                'severity': triage_decision.get('severity_level', ''),
                'current_medications': input_data.get('current_medications', []),
                'allergies': input_data.get('allergies', []),
                'patient_age': input_data.get('patient_age')
            }
            pharma_recommendations = self.pharma_agent.process(pharma_input)
        
        # Step 3: Get routing guidance
        routing_input = {
            'severity_level': triage_decision.get('severity_level', ''),
            'condition': triage_decision.get('primary_condition', ''),
            'patient_location': input_data.get('patient_location', ''),
            'comorbidities': input_data.get('comorbidities', []),
            'mobility_status': input_data.get('mobility_status', 'Mobile')
        }
        routing_guidance = self.routing_agent.process(routing_input)
        
        # Step 4: Synthesize all outputs
        synthesis_prompt = f"""Synthesize the following triage components into a comprehensive patient guidance:

Triage Decision: {json.dumps(triage_decision)}
Pharmaceutical Recommendations: {json.dumps(pharma_recommendations)}
Routing Guidance: {json.dumps(routing_guidance)}

Provide a patient-friendly summary and clear next steps."""
        
        synthesis = self.get_response(synthesis_prompt)
        
        return {
            'triage_decision': triage_decision,
            'pharmaceutical_recommendations': pharma_recommendations,
            'routing_guidance': routing_guidance,
            'patient_summary': synthesis,
            'next_steps': routing_guidance.get('pre_arrival_instructions', []),
            'warnings': triage_decision.get('safety_warnings', [])
        }
