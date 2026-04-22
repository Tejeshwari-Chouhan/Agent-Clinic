"""Emergency Routing Agent — ER locator, ambulance guidance, and hospital suggestions (Maps or LLM)."""

from __future__ import annotations

from typing import Any, Dict, List

from config import settings
from src.agents.hospital_knowledge_agent import HospitalKnowledgeAgent
from src.services.emergency_router import EmergencyRouter


def _dispatch_numbers_for_location(location: str) -> tuple[Dict[str, str], str]:
    """
    Infer region from free-text location and return only relevant emergency numbers.
    """
    low = (location or "").lower().strip()
    if not low:
        return (
            {"Emergency": "Use the number for where you are (911 US/Canada, 112 EU, 108 ambulance in India)"},
            "unknown",
        )

    india_hints = (
        "india",
        "bharat",
        "telangana",
        "andhra",
        "karnataka",
        "kerala",
        "tamil nadu",
        "maharashtra",
        "gujarat",
        "rajasthan",
        "punjab",
        "haryana",
        "delhi",
        "uttar pradesh",
        "madhya pradesh",
        "bihar",
        "odisha",
        "west bengal",
        "jharkhand",
        "assam",
        "goa",
        "chhattisgarh",
        "himachal",
        "uttarakhand",
        "hyderabad",
        "bengaluru",
        "bangalore",
        "mumbai",
        "chennai",
        "pune",
        "kolkata",
        "ahmedabad",
        "jaipur",
        "lucknow",
        "kanpur",
        "nagpur",
        "indore",
        "bhopal",
        "visakhapatnam",
        "vijayawada",
        "coimbatore",
        "warangal",
    )
    if any(h in low for h in india_hints):
        return {"Ambulance": "108", "All emergencies (single number)": "112"}, "India"

    uk_hints = (
        "united kingdom",
        " england",
        "scotland",
        "wales",
        "northern ireland",
        "london",
        "manchester",
        "birmingham",
        "liverpool",
        "glasgow",
        "edinburgh",
        "bristol",
        ", uk",
        " uk",
    )
    if any(h in low for h in uk_hints):
        return {"Emergency": "999"}, "United Kingdom"

    us_hints = (
        "united states",
        " u.s",
        " usa",
        "california",
        "texas",
        "florida",
        "new york",
        "illinois",
        "pennsylvania",
        "ohio",
        "georgia",
        "north carolina",
        "michigan",
        "new jersey",
        "virginia",
        "washington",
        "arizona",
        "massachusetts",
        "tennessee",
        "indiana",
        "missouri",
        "maryland",
        "colorado",
        "wisconsin",
        "minnesota",
        "south carolina",
        "alabama",
        "louisiana",
        "kentucky",
        "oregon",
        "oklahoma",
        "connecticut",
        "utah",
        "nevada",
    )
    if any(h in low for h in us_hints):
        return {"Emergency": "911"}, "United States"

    canada_hints = ("canada", "ontario", "toronto", "quebec", "montreal", "british columbia", "vancouver", "alberta", "calgary", "manitoba", "ottawa")
    if any(h in low for h in canada_hints):
        return {"Emergency": "911"}, "Canada"

    au_hints = ("australia", "sydney", "melbourne", "brisbane", "perth", "adelaide", "canberra", "hobart", "darwin")
    if any(h in low for h in au_hints):
        return {"Emergency": "000"}, "Australia"

    nz_hints = ("new zealand", "auckland", "wellington", "christchurch", "dunedin", "hamilton nz")
    if any(h in low for h in nz_hints):
        return {"Emergency": "111"}, "New Zealand"

    eu_hints = (
        "germany",
        "france",
        "spain",
        "italy",
        "netherlands",
        "belgium",
        "poland",
        "sweden",
        "norway",
        "denmark",
        "finland",
        "portugal",
        "greece",
        "austria",
        "ireland",
        "czech",
        "romania",
        "hungary",
        "slovakia",
        "croatia",
        "europe",
        "paris",
        "berlin",
        "madrid",
        "rome",
        "amsterdam",
        "brussels",
        "warsaw",
        "stockholm",
        "dublin",
    )
    if any(h in low for h in eu_hints):
        return {"Emergency": "112"}, "EU / many European countries"

    return {"Emergency": "112 (verify local number for your country)"}, "unmatched"


class EmergencyRoutingAgent:
    """Coordinates ER facilities via Google Maps when configured; otherwise uses LLM hospital knowledge."""

    def __init__(self) -> None:
        self._router = EmergencyRouter(
            api_key=settings.google_maps_api_key,
            timeout_seconds=settings.google_maps_timeout_seconds,
            max_facilities=settings.emergency_max_facilities,
            fallback_data_path=settings.emergency_fallback_data_path,
        )
        self._hospital_knowledge = HospitalKnowledgeAgent()

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        location = str(input_data.get("patient_location", "") or "").strip()
        condition = str(input_data.get("condition", "") or "")
        mobility = str(input_data.get("mobility_status", "Mobile") or "Mobile")

        facilities: List[Dict[str, Any]] = []
        routing_source = "fallback"
        instruction = (
            "Call your local emergency number immediately (e.g. 911 in the US, 112 in the EU, 108 for ambulance in India). "
            "Share your exact address or landmarks if known."
        )

        if location:
            instruction = (
                "Call emergency services first; do not delay critical care for travel. "
                "If advised to self-transport, use the nearest ER below."
            )
            if settings.google_maps_api_key:
                try:
                    facilities = self._router.find_nearest_facilities(location, "hospital")
                except Exception:
                    facilities = []
                routing_source = "maps_places" if facilities else "fallback"
            if not facilities:
                llm = self._hospital_knowledge.process({"patient_location": location})
                facilities = self._normalize_llm_facilities(llm.get("facilities") or [])
                if facilities:
                    routing_source = "llm"

        normalized_facilities = [
            {
                "facility_name": f.get("facility_name") or f.get("name", ""),
                "address": f.get("address", ""),
                "phone": f.get("phone", "911"),
                "distance_km": float(f.get("distance_km", 0.0) or 0.0),
                "estimated_time_minutes": int(f.get("estimated_time_minutes", 0) or 0),
                "directions_url": f.get("directions_url", ""),
                "notes": f.get("notes", ""),
            }
            for f in facilities
        ]

        dispatch_numbers, region_detected = _dispatch_numbers_for_location(location)
        ambulance = {
            "dispatch_numbers": dispatch_numbers,
            "region_detected": region_detected,
            "instructions": [
                "State clearly: location, chief complaint, consciousness/breathing, bleeding, allergies.",
                f"Patient mobility: {mobility}. Request ambulance if transport is unsafe or symptoms are worsening.",
            ],
            "if_caller_outside_home_region": (
                "If you are traveling outside the detected region, use that area's emergency number instead."
                if region_detected not in ("unknown", "unmatched")
                else "Add city and country to your location so we can show the right emergency number."
            ),
        }

        return {
            "routing_source": routing_source,
            "emergency_instruction": instruction,
            "er_locator": {"facilities": normalized_facilities},
            "ambulance": ambulance,
            "condition_context": condition,
        }

    def nearby_hospitals(self, patient_location: str) -> Dict[str, Any]:
        """Informational hospitals: Google Places when API key is set; otherwise LLM famous hospitals in that city."""
        location = str(patient_location or "").strip()
        if not location:
            return {
                "routing_source": "none",
                "message": "Provide city and state to see hospital suggestions.",
                "facilities": [],
            }

        if settings.google_maps_api_key:
            try:
                raw = self._router.find_hospitals_near_patient(location)
            except Exception:
                raw = []
            if raw:
                facilities = [
                    {
                        "facility_name": item.get("name", ""),
                        "address": item.get("address", ""),
                        "phone": item.get("phone", ""),
                        "distance_km": float(item.get("distance_km", 0.0) or 0.0),
                        "estimated_time_minutes": int(item.get("estimated_time_minutes", 0) or 0),
                        "directions_url": item.get("directions_url", ""),
                    }
                    for item in raw
                ]
                return {
                    "routing_source": "maps_places",
                    "message": "Based on Google Places near your location (verify before visiting).",
                    "facilities": facilities,
                }

        llm = self._hospital_knowledge.process({"patient_location": location})
        facilities = self._normalize_llm_facilities(llm.get("facilities") or [])
        return {
            "routing_source": llm.get("routing_source", "llm"),
            "message": llm.get("message", "Hospital suggestions from AI knowledge (verify phone and address)."),
            "facilities": facilities,
        }

    @staticmethod
    def _normalize_llm_facilities(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for item in rows:
            if not isinstance(item, dict):
                continue
            name = str(item.get("facility_name") or item.get("name", "")).strip()
            if not name:
                continue
            out.append(
                {
                    "facility_name": name,
                    "address": str(item.get("address", "")).strip(),
                    "phone": str(item.get("phone", "")).strip() or "Verify on hospital website",
                    "distance_km": float(item.get("distance_km", 0.0) or 0.0),
                    "estimated_time_minutes": int(item.get("estimated_time_minutes", 0) or 0),
                    "directions_url": str(item.get("directions_url", "")).strip(),
                    "notes": str(item.get("notes", "")).strip(),
                }
            )
        return out
