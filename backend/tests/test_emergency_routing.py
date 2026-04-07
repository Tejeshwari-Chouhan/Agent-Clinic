"""Tests for emergency routing MVP flow."""

import sys
from pathlib import Path
import unittest
from unittest.mock import patch


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.services.emergency_router import EmergencyRouter  # noqa: E402
from src.agents.routing_agent import RoutingAgent  # noqa: E402


class EmergencyRouterTests(unittest.TestCase):
    def test_fallback_facilities_when_google_key_missing(self):
        router = EmergencyRouter(
            api_key="",
            timeout_seconds=1.0,
            max_facilities=2,
            fallback_data_path=str(BACKEND_ROOT / "src/data/emergency_facilities_fallback.json"),
        )
        facilities = router.find_nearest_facilities("San Jose, CA")
        self.assertTrue(len(facilities) > 0)
        self.assertIn("name", facilities[0])
        self.assertIn("directions_url", facilities[0])

    @patch("src.services.emergency_router.requests.get")
    def test_live_facilities_sorted_by_eta_then_distance(self, mock_get):
        # Places API response
        places_payload = {
            "results": [
                {"place_id": "p1", "name": "Hospital One", "formatted_address": "Addr 1"},
                {"place_id": "p2", "name": "Hospital Two", "formatted_address": "Addr 2"},
            ]
        }
        # Details responses + distance matrix responses sequence
        detail_p1 = {"result": {"name": "Hospital One", "formatted_address": "Addr 1", "formatted_phone_number": "111"}}
        dist_p1 = {"rows": [{"elements": [{"duration": {"value": 900}, "distance": {"value": 5000}}]}]}
        detail_p2 = {"result": {"name": "Hospital Two", "formatted_address": "Addr 2", "formatted_phone_number": "222"}}
        dist_p2 = {"rows": [{"elements": [{"duration": {"value": 600}, "distance": {"value": 6000}}]}]}

        class _Resp:
            def __init__(self, payload):
                self._payload = payload

            def raise_for_status(self):
                return None

            def json(self):
                return self._payload

        mock_get.side_effect = [_Resp(places_payload), _Resp(detail_p1), _Resp(dist_p1), _Resp(detail_p2), _Resp(dist_p2)]

        router = EmergencyRouter(api_key="test-key", timeout_seconds=1.0, max_facilities=2)
        facilities = router.find_nearest_facilities("San Jose, CA")

        self.assertEqual(len(facilities), 2)
        # Hospital Two has lower ETA and should be first.
        self.assertEqual(facilities[0]["name"], "Hospital Two")
        self.assertEqual(facilities[1]["name"], "Hospital One")


class RoutingAgentEmergencyTests(unittest.TestCase):
    @patch("src.agents.base_agent.BaseAgent.__init__", return_value=None)
    @patch.object(RoutingAgent, "get_response")
    @patch("src.agents.routing_agent.EmergencyRouter.find_nearest_facilities")
    def test_high_severity_contains_emergency_payload(self, mock_find, mock_llm, _mock_base_init):
        mock_llm.return_value = """{
            "routing_pathway":"Emergency",
            "facility_type":"Emergency Department",
            "pre_arrival_instructions":["Do not drive if unstable"],
            "follow_up_guidance":["Bring ID and medications"],
            "emergency_contacts":["911"],
            "estimated_wait_time":"Unknown",
            "special_considerations":["Possible cardiac emergency"]
        }"""
        mock_find.return_value = [
            {
                "name": "City General Hospital",
                "address": "123 Main St",
                "phone": "911",
                "distance_km": 2.5,
                "estimated_time_minutes": 8,
                "directions_url": "https://www.google.com/maps/dir/?api=1",
            }
        ]

        agent = RoutingAgent()
        result = agent.process(
            {
                "severity_level": "High",
                "condition": "Myocardial infarction",
                "patient_location": "San Jose, CA",
            }
        )

        self.assertIn("emergency_routing", result)
        self.assertEqual(result["emergency_routing"]["routing_source"], "live")
        self.assertTrue(len(result["emergency_routing"]["facilities"]) > 0)


if __name__ == "__main__":
    unittest.main()
