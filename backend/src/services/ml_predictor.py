"""Service for ML-based disease probability prediction using trained model"""

import os
import pickle
import numpy as np
from typing import List, Tuple, Dict

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'models')

FEATURE_COLS = [
    'fever', 'cough', 'headache', 'nausea', 'vomiting', 'fatigue',
    'sore_throat', 'chills', 'body_pain', 'loss_of_appetite',
    'abdominal_pain', 'diarrhea', 'sweating', 'rapid_breathing', 'dizziness'
]

# Severity mapping for each disease
DISEASE_SEVERITY = {
    'Pneumonia': 'High',
    'Typhoid': 'Medium',
    'Malaria': 'Medium',
}


class MLPredictor:
    """Predicts disease probabilities from binary symptom features using trained GBM."""

    def __init__(self):
        self.model = None
        self.label_encoder = None
        self.feature_cols = FEATURE_COLS
        self._load_model()

    def _load_model(self):
        model_path = os.path.join(MODELS_DIR, 'disease_model.pkl')
        encoder_path = os.path.join(MODELS_DIR, 'label_encoder.pkl')

        if os.path.exists(model_path) and os.path.exists(encoder_path):
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            with open(encoder_path, 'rb') as f:
                self.label_encoder = pickle.load(f)
        else:
            # Model not yet trained — will use fallback heuristics
            self.model = None
            self.label_encoder = None

    def _features_to_vector(self, symptom_features: Dict) -> np.ndarray:
        """Convert symptom dict to ordered feature vector."""
        vector = np.array(
            [float(symptom_features.get(col, 0)) for col in self.feature_cols],
            dtype=np.float32
        ).reshape(1, -1)
        return vector

    def predict(self, symptom_features: Dict) -> List[Tuple[str, float]]:
        """
        Return disease probability vector P(D|S).
        symptom_features: dict with keys matching FEATURE_COLS, values 0 or 1.
        Returns: sorted list of (condition, probability) tuples.
        """
        if self.model is None or self.label_encoder is None:
            return self._heuristic_predict(symptom_features)

        X = self._features_to_vector(symptom_features)
        proba = self.model.predict_proba(X)[0]
        classes = self.label_encoder.classes_

        results = [(cls, float(prob)) for cls, prob in zip(classes, proba)]
        return self.rank_by_probability(results)

    def _heuristic_predict(self, symptom_features: Dict) -> List[Tuple[str, float]]:
        """Rule-based fallback when model is not trained yet."""
        f = symptom_features

        # Pneumonia signals: rapid_breathing, cough, fever, fatigue
        pneumonia_score = (
            2.0 * f.get('rapid_breathing', 0) +
            1.5 * f.get('cough', 0) +
            1.0 * f.get('fever', 0) +
            0.5 * f.get('fatigue', 0)
        )

        # Malaria signals: fever, chills, sweating, headache, body_pain
        malaria_score = (
            1.5 * f.get('fever', 0) +
            2.0 * f.get('chills', 0) +
            1.5 * f.get('sweating', 0) +
            0.5 * f.get('headache', 0) +
            0.5 * f.get('body_pain', 0)
        )

        # Typhoid signals: fever, abdominal_pain, loss_of_appetite, nausea
        typhoid_score = (
            1.0 * f.get('fever', 0) +
            2.0 * f.get('abdominal_pain', 0) +
            1.5 * f.get('loss_of_appetite', 0) +
            1.0 * f.get('nausea', 0) +
            0.5 * f.get('diarrhea', 0)
        )

        total = pneumonia_score + malaria_score + typhoid_score + 0.1
        return self.rank_by_probability([
            ('Pneumonia', round(pneumonia_score / total, 4)),
            ('Malaria', round(malaria_score / total, 4)),
            ('Typhoid', round(typhoid_score / total, 4)),
        ])

    def validate_probabilities(self, probabilities: List[Tuple[str, float]]) -> bool:
        total = sum(prob for _, prob in probabilities)
        return abs(total - 1.0) < 0.05

    def rank_by_probability(self, probabilities: List[Tuple[str, float]]) -> List[Tuple[str, float]]:
        return sorted(probabilities, key=lambda x: x[1], reverse=True)

    def get_severity(self, condition: str) -> str:
        return DISEASE_SEVERITY.get(condition, 'Medium')

    @property
    def is_model_loaded(self) -> bool:
        return self.model is not None
