"""Pharmaceutical Agent - Provides medication recommendations and drug interaction analysis"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
import json

class PharmaceuticalAgent(BaseAgent):
    """Agent responsible for pharmaceutical recommendations"""
    
    def __init__(self):
        system_prompt = """You are an expert pharmaceutical advisor agent. Your role is to:
1. Recommend appropriate medications based on diagnosed conditions
2. Check for drug interactions with current medications
3. Provide dosage and administration guidance
4. Identify contraindications and side effects
5. Suggest OTC alternatives when appropriate

Always prioritize patient safety and provide:
- Clear medication recommendations
- Dosage and frequency information
- Potential side effects
- Drug interaction warnings
- Contraindications
- When to seek medical attention"""
        
        super().__init__('PharmaceuticalAgent', system_prompt)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process condition and provide pharmaceutical recommendations
        
        Input:
        {
            'condition': str,
            'severity': str,
            'current_medications': [str],
            'allergies': [str] (optional),
            'patient_age': int (optional)
        }
        
        Output:
        {
            'recommendations': [
                {
                    'medication_name': str,
                    'dosage': str,
                    'frequency': str,
                    'duration': str,
                    'side_effects': [str],
                    'contraindications': [str],
                    'interaction_warnings': [str]
                }
            ],
            'drug_interactions': [str],
            'otc_alternatives': [str],
            'warnings': [str]
        }
        """
        condition = input_data.get('condition', '')
        severity = input_data.get('severity', 'Medium')
        current_meds = input_data.get('current_medications', [])
        allergies = input_data.get('allergies', [])
        patient_age = input_data.get('patient_age')
        
        meds_text = '\n'.join([f"- {med}" for med in current_meds]) if current_meds else "None"
        allergies_text = ', '.join(allergies) if allergies else "None"
        
        prompt = f"""Provide pharmaceutical recommendations for the following:

Condition: {condition}
Severity: {severity}
Current Medications:
{meds_text}
Known Allergies: {allergies_text}
Patient Age: {patient_age if patient_age else 'Not provided'}

Please provide recommendations in the following JSON format:
{{
    "recommendations": [
        {{
            "medication_name": "name",
            "dosage": "dosage",
            "frequency": "frequency",
            "duration": "duration",
            "side_effects": ["effect1", "effect2"],
            "contraindications": ["contraindication1"],
            "interaction_warnings": ["warning1"]
        }}
    ],
    "drug_interactions": ["interaction1", "interaction2"],
    "otc_alternatives": ["alternative1"],
    "warnings": ["warning1", "warning2"]
}}"""
        
        response = self.get_response(prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            recommendations = json.loads(json_str)
            if 'recommendations' not in recommendations:
                raise ValueError("Missing recommendations field")
            return recommendations
        except (json.JSONDecodeError, ValueError):
            return {
                'recommendations': [],
                'drug_interactions': [],
                'otc_alternatives': [],
                'warnings': ['Pharmaceutical recommendations require a physician consultation.']
            }
