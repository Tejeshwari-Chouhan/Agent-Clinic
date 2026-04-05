"""Triage Decision Agent - Makes clinical triage decisions based on disease probabilities"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
import json

class TriageDecisionAgent(BaseAgent):
    """Agent responsible for making triage decisions"""
    
    def __init__(self):
        system_prompt = """You are an expert healthcare triage agent. Your role is to:
1. Analyze disease probability vectors from symptom analysis
2. Classify cases into severity levels (High, Medium, Low)
3. Provide clinical reasoning for triage decisions
4. Recommend appropriate clinical actions

Severity Classification:
- High: Life-threatening conditions requiring immediate emergency care
- Medium: Urgent conditions requiring same-day medical attention
- Low: Non-urgent conditions suitable for self-care or pharmacy consultation

Always provide:
- Clear severity classification
- Confidence score (0-1)
- Clinical reasoning
- Recommended action
- Any safety warnings"""
        
        super().__init__('TriageDecisionAgent', system_prompt)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process disease probabilities and make triage decision
        
        Input:
        {
            'disease_probabilities': [('condition', probability), ...],
            'symptoms': str,
            'patient_age': int (optional),
            'comorbidities': [str] (optional)
        }
        
        Output:
        {
            'severity_level': str,
            'primary_condition': str,
            'confidence_score': float,
            'reasoning': str,
            'recommended_action': str,
            'safety_warnings': [str]
        }
        """
        disease_probs = input_data.get('disease_probabilities', [])
        symptoms = input_data.get('symptoms', '')
        patient_age = input_data.get('patient_age')
        comorbidities = input_data.get('comorbidities', [])
        known_conditions = input_data.get('known_conditions', [])
        test_reports = input_data.get('test_reports', [])
        
        # Format disease probabilities for the agent
        prob_text = '\n'.join([f"- {cond}: {prob:.2%}" for cond, prob in disease_probs])
        
        prompt = f"""Analyze the following clinical data and provide a triage decision:

Symptoms: {symptoms}
Patient Age: {patient_age if patient_age else 'Not provided'}
Comorbidities: {', '.join(comorbidities) if comorbidities else 'None'}
Known Conditions (Historical): {', '.join(known_conditions) if known_conditions else 'None'}
Test Reports (Historical): {', '.join([str(report) for report in test_reports]) if test_reports else 'None'}

Disease Probability Analysis:
{prob_text}

Please provide your triage decision in the following JSON format:
{{
    "severity_level": "High|Medium|Low",
    "primary_condition": "most likely condition",
    "confidence_score": 0.0-1.0,
    "reasoning": "clinical reasoning",
    "recommended_action": "specific action to take",
    "safety_warnings": ["warning1", "warning2"]
}}"""
        
        response = self.get_response(prompt)
        
        try:
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            decision = json.loads(json_str)
            return decision
        except ValueError:
            # Fallback if JSON parsing fails
            return {
                'severity_level': 'Medium',
                'primary_condition': disease_probs[0][0] if disease_probs else 'Unknown',
                'confidence_score': 0.5,
                'reasoning': response,
                'recommended_action': 'Consult healthcare provider',
                'safety_warnings': []
            }
