"""
Training utilities for the symptom→disease dataset (DecisionTree, fixed symptom columns).

Aligned with `notebooks/disease_ml_pipeline.ipynb`. Default CSV:
`backend/data/ml/symptom_disease_training.csv` (configurable via ML_DATASET_PATH).
Regenerate that file with `python scripts/build_symptom_ml_dataset.py` from the backend root.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Tuple

import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.tree import DecisionTreeClassifier

# Column order matches the training CSV (all binary 0/1 except `label`).
SYMPTOMS: List[str] = [
    "fever",
    "cough",
    "headache",
    "nausea",
    "vomiting",
    "fatigue",
    "sore_throat",
    "chills",
    "body_pain",
    "loss_of_appetite",
    "abdominal_pain",
    "diarrhea",
    "sweating",
    "rapid_breathing",
    "chest_pain",
    "dizziness",
    "skin_rash",
    "itching",
]

DEFAULT_DATASET_REL = Path("data/ml/symptom_disease_training.csv")


def _backend_root() -> Path:
    """Directory containing `app.py` (the FastAPI backend root)."""
    return Path(__file__).resolve().parents[1]


def resolve_dp_csv_path(csv_path: Path | None = None) -> Path:
    """
    Resolve CSV path:
    1) Explicit `csv_path` if provided and exists
    2) ML_DATASET_PATH relative to backend root
    3) Default `data/ml/symptom_disease_training.csv` under backend root
    4) Legacy `src/dp.csv` if still present
    """
    if csv_path is not None:
        p = Path(csv_path)
        if not p.exists():
            raise FileNotFoundError(str(p))
        return p

    root = _backend_root()

    env_rel = os.getenv("ML_DATASET_PATH", "").strip()
    if env_rel:
        candidate = Path(env_rel)
        if not candidate.is_absolute():
            candidate = root / env_rel
        if candidate.exists():
            return candidate

    primary = root / DEFAULT_DATASET_REL
    if primary.exists():
        return primary

    legacy = root / "src" / "dp.csv"
    if legacy.exists():
        return legacy

    raise FileNotFoundError(
        f"Training CSV not found. Expected {primary} "
        "(or set ML_DATASET_PATH to a path under the backend root)."
    )


def load_dp_frame(csv_path: Path | None = None) -> pd.DataFrame:
    return pd.read_csv(resolve_dp_csv_path(csv_path))


def train_model_from_dp(
    df: pd.DataFrame | None = None,
    csv_path: Path | None = None,
) -> Tuple[DecisionTreeClassifier, LabelEncoder, List[str]]:
    """
    Train DecisionTree on the full dataset (max_depth=12, min_samples_leaf=2, random_state=42).
    """
    train_data = df if df is not None else load_dp_frame(csv_path)
    if "label" not in train_data.columns:
        raise ValueError("Training file must include a `label` column.")

    X = train_data.drop(columns=["label"])
    for col in SYMPTOMS:
        if col not in X.columns:
            raise ValueError(f"Training file is missing expected symptom column: {col}")

    y_raw = train_data["label"].astype(str)
    le = LabelEncoder()
    y = le.fit_transform(y_raw)

    clf = DecisionTreeClassifier(max_depth=12, random_state=42, min_samples_leaf=2)
    clf.fit(X, y)
    feature_columns = list(X.columns)
    return clf, le, feature_columns
