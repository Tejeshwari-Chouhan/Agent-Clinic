"""Service for emergency routing using Google Maps APIs."""

from __future__ import annotations

from typing import Any, Dict, List
from urllib.parse import quote_plus
from pathlib import Path
import json
import requests


class EmergencyRouter:
    """Routes high-severity cases to nearest emergency facilities."""

    PLACES_API_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    DETAILS_API_URL = "https://maps.googleapis.com/maps/api/place/details/json"
    DISTANCE_MATRIX_API_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

    def __init__(
        self,
        api_key: str = "",
        timeout_seconds: float = 2.0,
        max_facilities: int = 3,
        fallback_data_path: str = "src/data/emergency_facilities_fallback.json",
    ):
        self.api_key = api_key or ""
        self.timeout_seconds = timeout_seconds
        self.max_facilities = max(1, max_facilities)
        self.fallback_data_path = Path(fallback_data_path)

    def find_nearest_facilities(self, location: str, facility_type: str = "hospital") -> List[Dict[str, Any]]:
        """
        Query Google Maps APIs to find nearest emergency facilities.
        Returns normalized facilities sorted by ETA then distance.
        """
        if not location:
            raise ValueError("Patient location is required for emergency routing.")

        try:
            places = self._search_places(location, facility_type)
        except Exception:
            places = []
        facilities: List[Dict[str, Any]] = []

        for place in places[: self.max_facilities]:
            place_id = place.get("place_id", "")
            if not place_id:
                continue
            details = self._get_place_details(place_id)
            route = self.get_directions(location, details.get("address", ""))
            facilities.append(
                {
                    "name": details.get("name", place.get("name", "Emergency Facility")),
                    "address": details.get("address", place.get("formatted_address", "")),
                    "phone": details.get("phone", "911"),
                    "distance_km": route.get("distance_km", 9999.0),
                    "estimated_time_minutes": route.get("estimated_time_minutes", 9999),
                    "directions_url": route.get(
                        "directions_url", self._build_directions_url(location, details.get("address", ""))
                    ),
                }
            )

        facilities.sort(
            key=lambda x: (
                x.get("estimated_time_minutes", 9999),
                x.get("distance_km", 9999.0),
            )
        )
        if facilities:
            return facilities[: self.max_facilities]
        return self._load_fallback_facilities(location)

    def get_directions(self, origin: str, destination: str) -> Dict[str, Any]:
        """Get travel time and distance for origin/destination using Distance Matrix."""
        directions_url = self._build_directions_url(origin, destination)
        if not self.api_key:
            return {
                "directions_url": directions_url,
                "estimated_time_minutes": 9999,
                "distance_km": 9999.0,
            }

        try:
            response = requests.get(
                self.DISTANCE_MATRIX_API_URL,
                params={
                    "origins": origin,
                    "destinations": destination,
                    "key": self.api_key,
                },
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            payload = response.json()
            rows = payload.get("rows", [])
            elements = rows[0].get("elements", []) if rows else []
            element = elements[0] if elements else {}

            duration_value = element.get("duration", {}).get("value")
            distance_value = element.get("distance", {}).get("value")
            if duration_value is None or distance_value is None:
                raise ValueError("Distance matrix returned incomplete data.")

            return {
                "directions_url": directions_url,
                "estimated_time_minutes": max(1, round(float(duration_value) / 60)),
                "distance_km": round(float(distance_value) / 1000, 2),
            }
        except Exception:
            return {
                "directions_url": directions_url,
                "estimated_time_minutes": 9999,
                "distance_km": 9999.0,
            }

    def _search_places(self, location: str, facility_type: str) -> List[Dict[str, Any]]:
        if not self.api_key:
            return []

        query = f"nearest emergency {facility_type} near {location}"
        response = requests.get(
            self.PLACES_API_URL,
            params={"query": query, "key": self.api_key},
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return payload.get("results", [])

    def _get_place_details(self, place_id: str) -> Dict[str, str]:
        if not self.api_key:
            return {"name": "", "address": "", "phone": "911"}

        response = requests.get(
            self.DETAILS_API_URL,
            params={
                "place_id": place_id,
                "fields": "name,formatted_address,formatted_phone_number",
                "key": self.api_key,
            },
            timeout=self.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json().get("result", {})
        return {
            "name": payload.get("name", ""),
            "address": payload.get("formatted_address", ""),
            "phone": payload.get("formatted_phone_number", "911"),
        }

    def _build_directions_url(self, origin: str, destination: str) -> str:
        return (
            "https://www.google.com/maps/dir/?api=1"
            f"&origin={quote_plus(origin)}"
            f"&destination={quote_plus(destination)}"
            "&travelmode=driving"
        )

    def _load_fallback_facilities(self, origin: str) -> List[Dict[str, Any]]:
        default_facilities = [
            {
                "name": "Nearest Emergency Department",
                "address": "Local Emergency Department",
                "phone": "911",
                "distance_km": 5.0,
                "estimated_time_minutes": 15,
                "directions_url": self._build_directions_url(origin, "Local Emergency Department"),
            }
        ]
        if not self.fallback_data_path.exists():
            return default_facilities

        try:
            payload = json.loads(self.fallback_data_path.read_text(encoding="utf-8"))
            facility_rows = payload.get("facilities", [])
            normalized = [
                {
                    "name": item.get("name", "Emergency Facility"),
                    "address": item.get("address", ""),
                    "phone": item.get("phone", "911"),
                    "distance_km": float(item.get("distance_km", 0.0)),
                    "estimated_time_minutes": int(item.get("estimated_time_minutes", 0)),
                    "directions_url": self._build_directions_url(origin, item.get("address", "")),
                }
                for item in facility_rows
            ]
            return normalized[: self.max_facilities] if normalized else default_facilities
        except Exception:
            return default_facilities
