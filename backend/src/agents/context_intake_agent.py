"""Context Intake Agent - Parses prompt text and extracts patient context."""

from typing import Any, Dict, List
import re

from src.agents.base_agent import BaseAgent


class ContextIntakeAgent(BaseAgent):
    """Agent responsible for turning free-text updates into storable context."""

    def __init__(self):
        system_prompt = (
            "You are a healthcare context intake agent that extracts test reports, "
            "medications, allergies, and known conditions from user prompts."
        )
        super().__init__('ContextIntakeAgent', system_prompt)

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = str(input_data.get('prompt', '') or '').strip()
        if not prompt:
            return {
                'action': 'no_action',
                'context': {},
                'message': 'Prompt is empty; no context update applied.',
            }

        extracted_context = {
            'test_reports': self._extract_list(
                prompt, ['test report data', 'test reports', 'test report', 'report']
            ),
            'medications': self._extract_list(prompt, ['medications', 'medication', 'meds', 'medicine']),
            'allergies': self._extract_list(prompt, ['allergies', 'allergy']),
            'known_conditions': self._extract_list(
                prompt, ['known conditions', 'conditions', 'diagnosed with', 'history of']
            ),
            # Always preserve full user text so random context is not lost.
            'context_notes': [prompt],
        }

        action = 'store_context'
        message = 'Stored prompt context and extracted structured fields when available.'

        return {
            'action': action,
            'context': extracted_context,
            'message': message,
        }

    def _extract_list(self, prompt: str, field_tokens: List[str]) -> List[str]:
        """Extract list values after field token markers."""
        for token in field_tokens:
            pattern = rf"{re.escape(token)}\s*[:\-]\s*([^\n\.]+)"
            match = re.search(pattern, prompt, flags=re.IGNORECASE)
            if not match:
                continue
            raw = match.group(1).strip()
            parts = re.split(r",| and ", raw)
            values = [part.strip(" .;:") for part in parts if part.strip(" .;:")]
            if values:
                return values
        return []
