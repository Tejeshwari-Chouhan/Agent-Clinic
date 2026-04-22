"""Hospital Knowledge Agent — lists well-known hospitals in a city using the LLM (no Maps API required)."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List
from urllib.parse import quote_plus

from src.agents.base_agent import BaseAgent


class HospitalKnowledgeAgent(BaseAgent):
    """
    Returns reputable / famous hospitals for a patient-reported city or region.
    Uses general knowledge; patients must verify phone numbers and departments before visiting.
    """

    def __init__(self) -> None:
        super().__init__(
            "HospitalKnowledgeAgent",
            system_prompt=(
                "You help triage software suggest where to seek in-person care. "
                "Given a city or region (often India), list 3 to 5 well-known major hospitals "
                "that locals would recognize: large public/teaching hospitals, major multi-specialty centers, "
                "or reputed tertiary-care names. Prefer facilities that typically have 24/7 emergency departments "
                "when the user may need urgent care.\n\n"
                "Rules:\n"
                "- Output ONLY a single JSON object, no markdown fences.\n"
                "- Schema: {\"hospitals\": [{\"name\": str, \"address\": str, \"phone\": str, \"notes\": str}], "
                "\"disclaimer\": str}\n"
                "- `address`: approximate street/area + city as commonly published (not GPS).\n"
                "- `phone`: main board / OPD number if you are confident; otherwise use "
                "\"Verify on official website\" or a well-known published line.\n"
                "- `notes`: one short line (e.g. \"Government\", \"Private chain\").\n"
                "- If the location is ambiguous, pick the most likely city and say so in disclaimer.\n"
                "- Never add hospitals outside the stated region."
            ),
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        location = str(input_data.get("patient_location", "") or "").strip()
        if not location:
            return {"routing_source": "llm", "facilities": [], "message": "No location provided for hospital lookup."}

        if not os.getenv("OPENAI_API_KEY"):
            return {
                "routing_source": "llm_unavailable",
                "facilities": [],
                "message": "Set OPENAI_API_KEY for AI-suggested hospitals, or add GOOGLE_MAPS_API_KEY for map-based search.",
            }

        prompt = (
            f"Patient-reported location (city / state / country):\n{location}\n\n"
            "Return the JSON object only."
        )

        try:
            self.clear_history()
            raw = self.get_response(prompt)
        except Exception as exc:
            return {
                "routing_source": "llm_error",
                "facilities": [],
                "message": f"Could not query hospital knowledge: {exc}",
            }

        hospitals, disclaimer = self._parse_response(raw)
        facilities = [_to_facility_row(h) for h in hospitals[:6]]
        return {
            "routing_source": "llm",
            "facilities": facilities,
            "message": disclaimer
            or "Well-known hospitals in your area (AI-generated; verify address and phone before visiting).",
        }

    def _parse_response(self, raw: str) -> tuple[List[Dict[str, str]], str]:
        try:
            start, end = raw.find("{"), raw.rfind("}") + 1
            payload = json.loads(raw[start:end])
        except (json.JSONDecodeError, ValueError):
            return [], "Could not parse hospital list from model response."

        rows = payload.get("hospitals") or []
        if not isinstance(rows, list):
            return [], str(payload.get("disclaimer") or "")

        cleaned: List[Dict[str, str]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name", "")).strip()
            if not name:
                continue
            cleaned.append(
                {
                    "name": name,
                    "address": str(row.get("address", "")).strip(),
                    "phone": str(row.get("phone", "")).strip() or "Verify on hospital website",
                    "notes": str(row.get("notes", "")).strip(),
                }
            )

        disclaimer = str(payload.get("disclaimer", "")).strip()
        return cleaned, disclaimer


def _to_facility_row(h: Dict[str, str]) -> Dict[str, Any]:
    name = h["name"]
    address = h.get("address", "")
    q = quote_plus(f"{name} {address}".strip())
    return {
        "facility_name": name,
        "address": address,
        "phone": h.get("phone", "Verify on hospital website"),
        "distance_km": 0.0,
        "estimated_time_minutes": 0,
        "directions_url": f"https://www.google.com/maps/search/?api=1&query={q}",
        "notes": h.get("notes", ""),
    }
