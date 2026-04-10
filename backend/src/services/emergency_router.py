"""
Emergency routing service.
Uses Google Maps API when key is available; falls back to structured mock data.
"""

import os
import math
import requests
from typing import Dict, List, Optional

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY', '')
GOOGLE_PLACES_URL = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"

# Fallback facilities per severity
_MOCK_FACILITIES = {
    "High": [
        {
            "facility_name": "City General Hospital — Emergency Department",
            "address": "1 Emergency Drive, City Center",
            "phone": "+1-800-HOSPITAL",
            "distance_km": 2.3,
            "estimated_time_minutes": 8,
            "directions_url": "https://maps.google.com/?q=Emergency+Hospital",
        },
        {
            "facility_name": "Regional Medical Center",
            "address": "45 Medical Blvd, District 2",
            "phone": "+1-800-REGIONAL",
            "distance_km": 4.1,
            "estimated_time_minutes": 14,
            "directions_url": "https://maps.google.com/?q=Regional+Medical+Center",
        }
    ],
    "Medium": [
        {
            "facility_name": "QuickCare Urgent Center",
            "address": "22 Health Street, Midtown",
            "phone": "+1-800-URGENTCARE",
            "distance_km": 1.5,
            "estimated_time_minutes": 6,
            "directions_url": "https://maps.google.com/?q=Urgent+Care+Center",
        },
        {
            "facility_name": "MedExpress Urgent Care",
            "address": "78 Wellness Ave, Uptown",
            "phone": "+1-800-MEDEXPRESS",
            "distance_km": 3.2,
            "estimated_time_minutes": 11,
            "directions_url": "https://maps.google.com/?q=MedExpress+Urgent+Care",
        }
    ],
    "Low": [
        {
            "facility_name": "HealthPlus Pharmacy",
            "address": "5 Main Street, Downtown",
            "phone": "+1-800-PHARMACY",
            "distance_km": 0.8,
            "estimated_time_minutes": 3,
            "directions_url": "https://maps.google.com/?q=HealthPlus+Pharmacy",
        }
    ]
}

_CARE_PATHWAY = {"High": "Emergency", "Medium": "Urgent Care", "Low": "Self-Care"}
_FACILITY_TYPE = {"High": "Emergency Department", "Medium": "Urgent Care Center", "Low": "Pharmacy"}
_WAIT_TIME = {"High": "Immediate triage on arrival", "Medium": "15-45 minutes typical", "Low": "Walk-in, minimal wait"}

_PRE_ARRIVAL = {
    "High": [
        "Call 911 or emergency services immediately if condition worsens",
        "Do NOT drive yourself — call an ambulance or have someone drive you",
        "Bring a list of current medications and allergies",
        "Inform hospital of symptoms on arrival for immediate triage",
    ],
    "Medium": [
        "Proceed to urgent care as soon as possible (within the hour)",
        "Bring ID, insurance card, and medication list",
        "Monitor for worsening symptoms — if breathing difficulty develops, call 911",
    ],
    "Low": [
        "Visit pharmacy or clinic at your convenience (within 24-48 hours)",
        "Rest and stay hydrated",
        "Monitor symptoms — return for care if condition worsens",
    ]
}

_FOLLOW_UP = {
    "High": [
        "Follow all discharge instructions from the emergency physician",
        "Schedule follow-up with primary care provider within 3-5 days",
        "Return immediately to ED if symptoms return or worsen",
    ],
    "Medium": [
        "Follow prescribed treatment plan completely",
        "Schedule follow-up with GP in 3-5 days",
        "Return to urgent care if symptoms do not improve within 48 hours",
    ],
    "Low": [
        "Complete any OTC treatment course as directed",
        "See GP if symptoms persist beyond 7-10 days",
        "Maintain hydration and rest",
    ]
}

_EMERGENCY_CONTACTS = {
    "High": ["911 (Emergency Services)", "Hospital Emergency: +1-800-HOSPITAL"],
    "Medium": ["Urgent Care: +1-800-URGENTCARE", "GP After-Hours Line"],
    "Low": ["Local Pharmacy", "GP Office"]
}


class EmergencyRouter:
    """Routes patients to appropriate care facilities based on severity."""

    def __init__(self):
        self.api_key = GOOGLE_MAPS_API_KEY
        self.has_api = bool(self.api_key)

    def route(
        self,
        severity: str,
        condition: str,
        patient_location: Optional[str] = None,
        comorbidities: Optional[List[str]] = None,
        mobility_status: str = "Mobile"
    ) -> Dict:
        """Build complete routing recommendation."""
        severity = severity.capitalize()
        if severity not in ("High", "Medium", "Low"):
            severity = "Medium"

        facilities = self._get_facilities(severity, patient_location)
        special = self._build_special_considerations(
            severity, condition, comorbidities or [], mobility_status
        )

        return {
            "routing_pathway": _CARE_PATHWAY.get(severity, "Urgent Care"),
            "facility_type": _FACILITY_TYPE.get(severity, "Healthcare Facility"),
            "pre_arrival_instructions": _PRE_ARRIVAL.get(severity, []),
            "follow_up_guidance": _FOLLOW_UP.get(severity, []),
            "emergency_contacts": _EMERGENCY_CONTACTS.get(severity, ["911"]),
            "estimated_wait_time": _WAIT_TIME.get(severity, "Unknown"),
            "special_considerations": special,
            "nearby_facilities": facilities,
        }

    # Backwards-compat alias for existing code
    def find_nearest_facilities(self, location: str, facility_type: str = 'hospital') -> list:
        severity = "High" if "emergency" in facility_type.lower() else "Medium"
        return self._get_facilities(severity, location)

    def get_directions(self, origin: str, destination: str) -> dict:
        return {
            "directions_url": f"https://maps.google.com/?q={destination.replace(' ', '+')}",
            "estimated_time_minutes": 10,
            "distance_km": 3.0
        }

    def _get_facilities(self, severity: str, location: Optional[str]) -> List[Dict]:
        if self.has_api and location:
            try:
                return self._google_maps_search(severity, location)
            except Exception:
                pass
        return _MOCK_FACILITIES.get(severity, [])

    def _google_maps_search(self, severity: str, location: str) -> List[Dict]:
        keywords = {"High": "hospital emergency", "Medium": "urgent care", "Low": "pharmacy"}
        geo = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": location, "key": self.api_key}, timeout=5
        ).json()
        if geo.get("status") != "OK":
            return _MOCK_FACILITIES.get(severity, [])

        loc = geo["results"][0]["geometry"]["location"]
        lat, lng = loc["lat"], loc["lng"]

        data = requests.get(
            GOOGLE_PLACES_URL,
            params={"location": f"{lat},{lng}", "radius": 10000,
                    "keyword": keywords.get(severity, "hospital"), "key": self.api_key},
            timeout=5
        ).json()

        facilities = []
        for place in data.get("results", [])[:3]:
            p_lat = place["geometry"]["location"]["lat"]
            p_lng = place["geometry"]["location"]["lng"]
            dist = self._haversine(lat, lng, p_lat, p_lng)
            facilities.append({
                "facility_name": place.get("name", "Unknown"),
                "address": place.get("vicinity", "Address unavailable"),
                "phone": place.get("formatted_phone_number", "Call directory"),
                "distance_km": round(dist, 2),
                "estimated_time_minutes": max(3, int(dist * 3)),
                "directions_url": f"https://maps.google.com/?q={p_lat},{p_lng}",
            })
        return facilities or _MOCK_FACILITIES.get(severity, [])

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return R * 2 * math.asin(math.sqrt(a))

    def _build_special_considerations(
        self, severity: str, condition: str, comorbidities: List[str], mobility: str
    ) -> List[str]:
        considerations = []
        if mobility.lower() == "immobile":
            considerations.append("Patient is immobile — ambulance transport recommended")
        elif mobility.lower() == "assisted":
            considerations.append("Patient requires mobility assistance — wheelchair access needed")
        if comorbidities:
            considerations.append(
                f"Existing conditions: {', '.join(comorbidities)} — inform attending physician"
            )
        condition_notes = {
            "Pneumonia": "Oxygen therapy may be required on arrival",
            "Malaria": "Rapid malaria test (RDT) will be needed at facility",
            "Typhoid": "Blood culture may be required for diagnosis confirmation",
        }
        if condition in condition_notes:
            considerations.append(condition_notes[condition])
        if severity == "High":
            considerations.append("Call ahead to alert ED staff of arriving patient condition")
        return considerations
