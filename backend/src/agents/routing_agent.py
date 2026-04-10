"""Routing Agent - Determines appropriate care pathway and coordinates routing"""

from typing import Dict, Any, List
from src.agents.base_agent import BaseAgent
import json

class RoutingAgent(BaseAgent):
    """Agent responsible for routing decisions and care pathway coordination"""
    
    def __init__(self):
        system_prompt = """You are an expert healthcare routing agent. Your role is to:
1. Determine appropriate care pathways based on severity
2. Coordinate emergency routing for high-severity cases
3. Recommend urgent care facilities for medium-severity cases
4. Provide self-care guidance for low-severity cases
5. Ensure patient safety throughout the routing process

Care Pathways:
- High Severity: Emergency Department (ED) routing
- Medium Severity: Urgent Care Center routing
- Low Severity: Self-care with pharmacy consultation

Always provide:
- Clear routing recommendation
- Facility information (if applicable)
- Pre-arrival instructions
- Follow-up guidance
- Emergency contact information"""
        
        super().__init__('RoutingAgent', system_prompt)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process severity and condition to determine routing
        
        Input:
        {
            'severity_level': str,
            'condition': str,
            'patient_location': str (optional),
            'comorbidities': [str] (optional),
            'mobility_status': str (optional)
        }
        
        Output:
        {
            'routing_pathway': str,
            'facility_type': str,
            'pre_arrival_instructions': [str],
            'follow_up_guidance': [str],
            'emergency_contacts': [str],
            'estimated_wait_time': str,
            'special_considerations': [str]
        }
        """
        severity = input_data.get('severity_level', 'Medium')
        condition = input_data.get('condition', '')
        location = input_data.get('patient_location', '')
        comorbidities = input_data.get('comorbidities', [])
        mobility = input_data.get('mobility_status', 'Mobile')
        
        comorbidities_text = ', '.join(comorbidities) if comorbidities else "None"
        
        prompt = f"""Determine the appropriate care routing for the following patient:

Severity Level: {severity}
Condition: {condition}
Patient Location: {location if location else 'Not provided'}
Comorbidities: {comorbidities_text}
Mobility Status: {mobility}

Please provide routing recommendations in the following JSON format:
{{
    "routing_pathway": "Emergency|Urgent Care|Self-Care",
    "facility_type": "Emergency Department|Urgent Care Center|Pharmacy|Home Care",
    "pre_arrival_instructions": ["instruction1", "instruction2"],
    "follow_up_guidance": ["guidance1", "guidance2"],
    "emergency_contacts": ["contact1", "contact2"],
    "estimated_wait_time": "estimated time",
    "special_considerations": ["consideration1"]
}}"""
        
        response = self.get_response(prompt)
        
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            json_str = response[json_start:json_end]
            routing = json.loads(json_str)
            if 'routing_pathway' not in routing:
                raise ValueError("Missing required field routing_pathway")
            return routing
        except (json.JSONDecodeError, ValueError):
            return {
                'routing_pathway': {'High': 'Emergency', 'Medium': 'Urgent Care', 'Low': 'Self-Care'}.get(severity, 'Urgent Care'),
                'facility_type': self._get_facility_type(severity),
                'pre_arrival_instructions': [],
                'follow_up_guidance': ['Follow up with your healthcare provider within 48 hours'],
                'emergency_contacts': ['911 (Emergency Services)'],
                'estimated_wait_time': 'Unknown',
                'special_considerations': []
            }
    
    def _get_facility_type(self, severity: str) -> str:
        """Get facility type based on severity"""
        facility_map = {
            'High': 'Emergency Department',
            'Medium': 'Urgent Care Center',
            'Low': 'Pharmacy'
        }
        return facility_map.get(severity, 'Healthcare Facility')
