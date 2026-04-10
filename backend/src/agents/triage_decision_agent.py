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
        self.model = 'gpt-4o-mini'
    
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
        
        # Format disease probabilities for the agent
        prob_text = '\n'.join([f"- {cond}: {prob:.2%}" for cond, prob in disease_probs])
        
        prompt = f"""Analyze the following clinical data and provide a triage decision:

Symptoms: {symptoms}
Patient Age: {patient_age if patient_age else 'Not provided'}
Comorbidities: {', '.join(comorbidities) if comorbidities else 'None'}

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
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start == -1:
                raise ValueError("No JSON in response")
            json_str = response[json_start:json_end]
            decision = json.loads(json_str)
            if 'severity_level' not in decision:
                raise ValueError("Missing required field severity_level")
            return decision
        except (json.JSONDecodeError, ValueError):
            # Rule-based fallback using top disease probability
            primary = disease_probs[0][0] if disease_probs else 'Unknown'
            confidence = disease_probs[0][1] if disease_probs else 0.5
            severity_map = {'Pneumonia': 'High', 'Typhoid': 'Medium', 'Malaria': 'Medium'}
            severity = severity_map.get(primary, 'Medium')
            action_map = {
                'High': 'Seek emergency care immediately — call 911 or go to nearest ED',
                'Medium': 'Visit an urgent care clinic or physician today',
                'Low': 'Rest at home and monitor symptoms; consult pharmacist if needed',
            }
            warnings = []
            if severity == 'High':
                warnings = ['EMERGENCY: Seek immediate medical attention']
            return {
                'severity_level': severity,
                'primary_condition': primary,
                'confidence_score': round(confidence, 3),
                'reasoning': (
                    f"Based on symptom analysis, {primary} has the highest probability "
                    f"({confidence:.0%}). Severity classified as {severity} per clinical protocol."
                ),
                'recommended_action': action_map[severity],
                'safety_warnings': warnings,
            }
