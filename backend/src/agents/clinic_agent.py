"""Clinic Agent — non-emergency primary / urgent care guidance."""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from src.agents.base_agent import BaseAgent


class ClinicAgent(BaseAgent):
    """Recommends appropriate non-emergency clinic pathways."""

    def __init__(self) -> None:
        super().__init__(
            "ClinicAgent",
            system_prompt=(
                "You are a clinic navigation assistant. For non-emergency cases, recommend "
                "whether same-day primary care, urgent care, or telehealth is reasonable. "
                "Output strict JSON with keys: clinic_pathway (Primary Care|Urgent Care|Telehealth|Mixed), "
                "rationale (string), preparation_steps (array of strings), "
                "what_to_bring (array), timing_guidance (string)."
            ),
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        severity = input_data.get("severity_level", "Low")
        condition = input_data.get("primary_condition", "")
        symptoms = input_data.get("symptoms", "")
        location = input_data.get("patient_location", "")
        comorbidities = input_data.get("comorbidities", []) or []

        if os.getenv("OPENAI_API_KEY"):
            try:
                self.clear_history()
                prompt = (
                    f"Severity band: {severity}\n"
                    f"Working diagnosis/condition focus: {condition}\n"
                    f"Symptoms: {symptoms}\n"
                    f"Location (for context only): {location or 'unknown'}\n"
                    f"Comorbidities: {', '.join(comorbidities) if comorbidities else 'none'}\n"
                    "Return JSON only."
                )
                raw = self.get_response(prompt)
                start, end = raw.find("{"), raw.rfind("}") + 1
                return json.loads(raw[start:end])
            except Exception:
                pass

        return self._fallback(severity, condition)

    def _fallback(self, severity: str, condition: str) -> Dict[str, Any]:
        if severity == "Medium":
            pathway = "Urgent Care"
            timing = "Seek same-day evaluation, especially if symptoms are worsening or new since this morning."
            prep = [
                "Bring a list of medications and allergies.",
                "Note time of symptom onset and fever readings if applicable.",
            ]
        else:
            pathway = "Primary Care"
            timing = "Schedule a routine visit within a few days if symptoms persist or interfere with daily activities."
            prep = [
                "Bring insurance information and medication list.",
                "Write down questions for your clinician.",
            ]

        return {
            "clinic_pathway": pathway,
            "rationale": f"Non-emergency presentation aligned with {pathway.lower()} for suspected {condition or 'general complaint'}.",
            "preparation_steps": prep,
            "what_to_bring": ["ID", "Insurance card", "Medication list", "Allergy list"],
            "timing_guidance": timing,
        }
