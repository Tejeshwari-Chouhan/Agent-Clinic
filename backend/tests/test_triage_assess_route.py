"""Integration-style test: /api/triage/assess invokes orchestrator (mocked, no OpenAI)."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app import app  # noqa: E402


class TriageAssessRouteTests(unittest.TestCase):
    @patch("src.routes.triage.orchestrator.process")
    def test_assess_returns_orchestrator_payload(self, mock_process):
        mock_process.return_value = {
            "triage_decision": {"severity_level": "Low", "recommended_action": "Rest"},
            "patient_summary": "OK",
            "disease_probabilities": [{"condition": "Pneumonia", "probability": 0.5}],
            "emergency_routing": {},
        }

        client = TestClient(app)
        res = client.post(
            "/api/triage/assess",
            json={"symptoms": "mild cough", "patient_age": 30, "patient_location": "Bengaluru, Karnataka, India"},
        )
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertEqual(body["triage_decision"]["severity_level"], "Low")
        mock_process.assert_called_once()


if __name__ == "__main__":
    unittest.main()
