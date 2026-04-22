"""ML disease prediction using `dp_train_utils` + `data/ml/symptom_disease_training.csv` (see notebooks/disease_ml_pipeline.ipynb)."""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

from config import settings
from src.dp_train_utils import load_dp_frame, train_model_from_dp


class MLPredictor:
    """Trains (or loads) the DecisionTree model from the symptom/disease CSV (notebook-aligned)."""

    def __init__(self) -> None:
        self._model: DecisionTreeClassifier | None = None
        self._label_encoder: LabelEncoder | None = None
        self._feature_columns: List[str] = []
        self._classes: List[str] = []
        self._is_fitted = False

    def _backend_root(self) -> Path:
        return Path(__file__).resolve().parents[2]

    def _dataset_path(self) -> Path:
        return self._backend_root() / settings.ml_dataset_path

    def _model_cache_path(self) -> Path:
        return self._backend_root() / settings.ml_model_cache_path

    def _ensure_model(self) -> None:
        if self._is_fitted:
            return

        path = self._dataset_path()
        dataset_mtime = path.stat().st_mtime if path.exists() else None
        dataset_key = str(path.resolve())

        cache = self._model_cache_path()
        if cache.exists() and dataset_mtime is not None:
            try:
                payload = pickle.loads(cache.read_bytes())
                cached_mtime = payload.get("dataset_mtime")
                cached_key = payload.get("dataset_path")
                if cached_mtime == dataset_mtime and cached_key == dataset_key:
                    self._model = payload["model"]
                    self._label_encoder = payload["label_encoder"]
                    self._feature_columns = payload["feature_columns"]
                    self._classes = list(self._label_encoder.classes_)
                    self._is_fitted = True
                    return
            except Exception:
                pass

        if not path.exists():
            self._model = None
            self._label_encoder = None
            self._feature_columns = []
            self._classes = []
            self._is_fitted = True
            return

        df = load_dp_frame(path)
        model, label_encoder, feature_columns = train_model_from_dp(df)

        self._model = model
        self._label_encoder = label_encoder
        self._feature_columns = feature_columns
        self._classes = list(label_encoder.classes_)
        self._is_fitted = True

        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_bytes(
                pickle.dumps(
                    {
                        "model": self._model,
                        "label_encoder": self._label_encoder,
                        "feature_columns": self._feature_columns,
                        "dataset_mtime": path.stat().st_mtime,
                        "dataset_path": str(path.resolve()),
                    }
                )
            )
        except OSError:
            pass

    def predict(self, symptom_features: dict) -> list:
        """
        symptom_features: mapping feature_name -> 0/1, or contains 'feature_array' aligned to training columns.
        Returns list of (condition, probability) tuples summing to ~1.
        """
        self._ensure_model()
        if not self._model or not self._label_encoder or not self._feature_columns:
            return self._heuristic_fallback(symptom_features)

        vector = self._vectorize(symptom_features)
        if vector is None:
            return self._heuristic_fallback(symptom_features)

        x_row = pd.DataFrame([vector.tolist()], columns=self._feature_columns)
        probs = self._model.predict_proba(x_row)[0]
        pairs = [(str(self._classes[i]), float(probs[i])) for i in range(len(probs))]
        total = sum(p for _, p in pairs)
        if total <= 0:
            return self._heuristic_fallback(symptom_features)
        normalized = [(c, p / total) for c, p in pairs]
        return sorted(normalized, key=lambda x: x[1], reverse=True)

    def _vectorize(self, symptom_features: dict) -> np.ndarray | None:
        if "feature_array" in symptom_features and "feature_order" in symptom_features:
            order = list(symptom_features["feature_order"])
            values = list(symptom_features["feature_array"])
            if len(order) != len(values):
                return None
            mapping = dict(zip(order, values))
            try:
                return np.array([int(mapping.get(col, 0)) for col in self._feature_columns], dtype=np.int32)
            except (TypeError, ValueError):
                return None

        try:
            return np.array([int(symptom_features.get(col, 0)) for col in self._feature_columns], dtype=np.int32)
        except (TypeError, ValueError):
            return None

    def _heuristic_fallback(self, symptom_features: dict) -> List[Tuple[str, float]]:
        _ = symptom_features
        return [
            ("Common Cold", 0.35),
            ("Flu", 0.25),
            ("Allergies", 0.20),
            ("Other", 0.20),
        ]

    def validate_probabilities(self, probabilities: list) -> bool:
        total = sum(prob for _, prob in probabilities)
        return abs(total - 1.0) < 0.01

    def rank_by_probability(self, probabilities: list) -> list:
        return sorted(probabilities, key=lambda x: x[1], reverse=True)

    def validate_with_patient_context(self, probabilities: list, patient_context: dict) -> list:
        if not probabilities:
            return []

        known_conditions = [str(item).lower() for item in patient_context.get("known_conditions", [])]
        report_markers = " ".join(str(item).lower() for item in patient_context.get("test_reports", []))

        adjusted = []
        for condition, probability in probabilities:
            weight = 1.0
            condition_lower = str(condition).lower()
            if any(condition_lower in known for known in known_conditions):
                weight += 0.20
            if condition_lower and condition_lower in report_markers:
                weight += 0.10
            adjusted.append((condition, max(0.0, float(probability) * weight)))

        total = sum(prob for _, prob in adjusted)
        if total <= 0:
            return probabilities

        normalized = [(condition, prob / total) for condition, prob in adjusted]
        return self.rank_by_probability(normalized)
