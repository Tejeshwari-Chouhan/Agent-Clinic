"""Smoke tests for ML predictor and deterministic agents (no OpenAI calls)."""

import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.agents.severity_scoring_agent import SeverityScoringAgent  # noqa: E402
from src.agents.symptom_understanding_agent import SymptomUnderstandingAgent  # noqa: E402
from src.dp_train_utils import SYMPTOMS  # noqa: E402
from src.services.ml_predictor import MLPredictor  # noqa: E402


class MLPredictorDatasetTests(unittest.TestCase):
    def test_predict_returns_normalized_distribution(self):
        predictor = MLPredictor()
        probs = predictor.predict(
            {
                "fever": 1,
                "cough": 1,
                "headache": 1,
                "nausea": 1,
                "vomiting": 0,
                "fatigue": 0,
                "sore_throat": 0,
                "chills": 1,
                "body_pain": 1,
                "loss_of_appetite": 1,
                "abdominal_pain": 1,
                "diarrhea": 0,
                "sweating": 0,
                "rapid_breathing": 0,
                "chest_pain": 0,
                "dizziness": 0,
                "skin_rash": 0,
                "itching": 0,
            }
        )
        self.assertTrue(len(probs) > 0)
        total = sum(p for _, p in probs)
        self.assertAlmostEqual(total, 1.0, places=5)


class MLPredictorFeverSparseTests(unittest.TestCase):
    """Fever-only vectors need explicit training rows; otherwise the tree spreads mass oddly."""

    @classmethod
    def setUpClass(cls):
        script = BACKEND_ROOT / "scripts" / "build_symptom_ml_dataset.py"
        subprocess.run(
            [sys.executable, str(script)],
            cwd=str(BACKEND_ROOT),
            check=True,
        )

    def test_fever_only_prefers_acute_infectious_labels(self):
        predictor = MLPredictor()
        vec = {c: (1 if c == "fever" else 0) for c in SYMPTOMS}
        probs = predictor.predict(vec)
        self.assertGreater(len(probs), 0)
        top5 = [name for name, _ in probs[:5]]
        misleading = {"BPPV", "Appendicitis", "Drug Eruption"}
        self.assertFalse(
            misleading.intersection(set(top5)),
            msg=f"unexpected non-fever-parsimonious top5: {top5}",
        )
        self.assertIn("Influenza", top5)
        self.assertIn("Acute Viral Syndrome", top5)

    @patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False)
    def test_plain_text_fever_maps_to_sensible_ml_top(self):
        agent = SymptomUnderstandingAgent()
        su = agent.process({"symptoms": "fever"})
        self.assertEqual(su["symptom_vector"]["fever"], 1)
        predictor = MLPredictor()
        probs = predictor.predict(su)
        top5 = [name for name, _ in probs[:5]]
        self.assertTrue(
            any(n in top5 for n in ("Influenza", "Acute Viral Syndrome", "COVID-19", "Common Cold")),
            msg=f"top5 was {top5}",
        )


class SymptomUnderstandingTests(unittest.TestCase):
    @patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False)
    def test_keyword_extraction_maps_fever_and_cough(self):
        agent = SymptomUnderstandingAgent()
        result = agent.process({"symptoms": "I have fever, bad cough, and chills"})
        self.assertEqual(result["symptom_vector"]["fever"], 1)
        self.assertEqual(result["symptom_vector"]["cough"], 1)
        self.assertEqual(result["symptom_vector"]["chills"], 1)


class SeverityScoringTests(unittest.TestCase):
    def test_red_flags_force_high(self):
        agent = SeverityScoringAgent()
        result = agent.process(
            {
                "symptoms": "I have crushing chest pain and shortness of breath",
                "disease_probabilities": [("Pneumonia", 0.2)],
                "symptom_understanding": {"symptom_vector": {}},
                "medical_history": {},
                "patient_age": 40,
            }
        )
        self.assertEqual(result["severity_level"], "High")


if __name__ == "__main__":
    unittest.main()
