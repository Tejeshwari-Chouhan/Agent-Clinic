#!/usr/bin/env python3
"""
Regenerate `data/ml/symptom_disease_training.csv` from `src.dp_train_utils.SYMPTOMS`.

Uses many disease templates + random symptom combinations + isolated single-feature
rows so common phrases (e.g. skin rashes, chest pain) map to plausible labels.

Run from backend root:
  python scripts/build_symptom_ml_dataset.py
"""

from __future__ import annotations

import csv
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dp_train_utils import SYMPTOMS as COLS  # noqa: E402


def _zeros() -> dict[str, int]:
    return {c: 0 for c in COLS}


def _row(partial: dict[str, int]) -> list[int]:
    d = _zeros()
    for k, v in partial.items():
        if k in d:
            d[k] = int(v)
    return [d[c] for c in COLS]


def jitter(vec: list[int], rng: random.Random, rate: float = 0.04) -> list[int]:
    out = list(vec)
    for i in range(len(out)):
        if rng.random() < rate:
            out[i] = 1 - out[i]
    return out


def merge(a: dict[str, int], b: dict[str, int]) -> dict[str, int]:
    out = {**a, **b}
    return {k: int(v) for k, v in out.items() if k in COLS}


# (label, base partial dict) — bases are sparse; augmentation adds noise.
TEMPLATES: list[tuple[str, dict[str, int]]] = [
    # Respiratory / general
    ("Common Cold", {"sore_throat": 1, "cough": 1, "fatigue": 1, "headache": 1}),
    ("Influenza", {"fever": 1, "cough": 1, "headache": 1, "chills": 1, "body_pain": 1, "fatigue": 1}),
    ("Bronchitis", {"cough": 1, "fatigue": 1, "sore_throat": 1, "chest_pain": 0}),
    ("Pneumonia", {"fever": 1, "cough": 1, "chills": 1, "rapid_breathing": 1, "chest_pain": 1, "fatigue": 1}),
    ("COVID-19", {"fever": 1, "cough": 1, "fatigue": 1, "headache": 1, "loss_of_appetite": 1}),
    ("Sinusitis", {"headache": 1, "fatigue": 1, "cough": 1, "sore_throat": 1}),
    ("Allergic Rhinitis", {"sore_throat": 1, "fatigue": 1, "headache": 1, "cough": 0}),
    # GI
    ("Acute Gastroenteritis", {"nausea": 1, "vomiting": 1, "diarrhea": 1, "abdominal_pain": 1, "fatigue": 1}),
    ("Food Poisoning", {"nausea": 1, "vomiting": 1, "diarrhea": 1, "abdominal_pain": 1}),
    ("GERD with Chest Symptoms", {"chest_pain": 1, "nausea": 1, "abdominal_pain": 1}),
    # Neuro / systemic
    ("Migraine", {"headache": 1, "nausea": 1, "vomiting": 0, "dizziness": 1}),
    ("Tension Headache", {"headache": 1, "fatigue": 1}),
    ("Dehydration", {"dizziness": 1, "fatigue": 1, "rapid_breathing": 1, "nausea": 1}),
    ("Hyperventilation Syndrome", {"rapid_breathing": 1, "dizziness": 1, "nausea": 1, "chest_pain": 0}),
    # Infectious (non-skin specific patterns)
    ("Malaria", {"fever": 1, "chills": 1, "sweating": 1, "headache": 1, "nausea": 1}),
    ("Typhoid Fever", {"fever": 1, "headache": 1, "abdominal_pain": 1, "loss_of_appetite": 1}),
    ("Dengue Fever", {"fever": 1, "headache": 1, "body_pain": 1, "nausea": 1, "chills": 1}),
    ("Urinary Tract Infection", {"fever": 1, "fatigue": 1, "abdominal_pain": 1, "nausea": 0}),
    # Cardiac / chest
    ("Acute Coronary Syndrome", {"chest_pain": 1, "sweating": 1, "nausea": 1, "rapid_breathing": 1, "dizziness": 1}),
    ("Stable Angina", {"chest_pain": 1, "fatigue": 1, "rapid_breathing": 1}),
    ("Pulmonary Embolism", {"chest_pain": 1, "rapid_breathing": 1, "cough": 1, "dizziness": 1}),
    ("Costochondritis", {"chest_pain": 1, "body_pain": 1}),
    # Airway / pharynx (18-feature space)
    ("Asthma Exacerbation", {"cough": 1, "rapid_breathing": 1, "chest_pain": 1, "fatigue": 1}),
    ("Acute Bronchospasm", {"cough": 1, "rapid_breathing": 1, "dizziness": 1, "chest_pain": 0}),
    ("Viral Pharyngitis", {"sore_throat": 1, "fatigue": 1, "headache": 1, "cough": 0}),
    ("Streptococcal Pharyngitis", {"sore_throat": 1, "fever": 1, "headache": 1, "chills": 1, "nausea": 0}),
    # Abdominal surgical / renal colic (distinct from gastroenteritis: diarrhea off)
    ("Acute Cholecystitis", {"abdominal_pain": 1, "nausea": 1, "vomiting": 1, "fever": 1, "diarrhea": 0, "sweating": 1}),
    ("Appendicitis", {"abdominal_pain": 1, "nausea": 1, "vomiting": 1, "fever": 1, "loss_of_appetite": 1, "diarrhea": 0}),
    ("Nephrolithiasis", {"abdominal_pain": 1, "nausea": 1, "vomiting": 1, "body_pain": 1, "sweating": 1, "fever": 0}),
    ("Nephrolithiasis with Fever", {"abdominal_pain": 1, "nausea": 1, "vomiting": 1, "body_pain": 1, "fever": 1, "chills": 0}),
    # Vestibular
    ("BPPV", {"dizziness": 1, "nausea": 1, "vomiting": 0, "headache": 0}),
    ("Vestibular Neuritis", {"dizziness": 1, "nausea": 1, "vomiting": 1, "headache": 1}),
    ("Labyrinthitis", {"dizziness": 1, "nausea": 1, "vomiting": 1, "fever": 1, "headache": 1}),
    # Heat / systemic viral / panic
    ("Heat Exhaustion", {"fatigue": 1, "dizziness": 1, "sweating": 1, "nausea": 1, "rapid_breathing": 1, "fever": 0}),
    ("Heat Stroke", {"fever": 1, "dizziness": 1, "rapid_breathing": 1, "nausea": 1, "sweating": 0, "fatigue": 1}),
    ("Acute Viral Syndrome", {"fatigue": 1, "body_pain": 1, "headache": 1, "fever": 1, "chills": 1, "cough": 0}),
    ("Panic Attack", {"rapid_breathing": 1, "chest_pain": 1, "dizziness": 1, "nausea": 1, "sweating": 1}),
    # Urinary (no dysuria column — systemic vs local proxy)
    ("Pyelonephritis", {"fever": 1, "chills": 1, "abdominal_pain": 1, "body_pain": 1, "nausea": 1, "headache": 1}),
    ("Cystitis", {"abdominal_pain": 1, "fatigue": 1, "fever": 0, "nausea": 0, "vomiting": 0}),
    # Dermatology — strong skin_rash / itching signal
    ("Urticaria", {"skin_rash": 1, "itching": 1}),
    ("Acute Urticaria", {"skin_rash": 1, "itching": 1, "fatigue": 1}),
    ("Contact Dermatitis", {"skin_rash": 1, "itching": 1}),
    ("Atopic Dermatitis", {"skin_rash": 1, "itching": 1, "fatigue": 1}),
    ("Seborrheic Dermatitis", {"skin_rash": 1, "itching": 1}),
    ("Viral Exanthem", {"skin_rash": 1, "fever": 1, "fatigue": 1, "headache": 1}),
    ("Drug Eruption", {"skin_rash": 1, "itching": 1, "fever": 1, "nausea": 1}),
    ("Psoriasis", {"skin_rash": 1, "itching": 0, "body_pain": 1, "fatigue": 1}),
    ("Tinea Infection", {"skin_rash": 1, "itching": 1, "sweating": 1}),
    ("Cellulitis", {"skin_rash": 1, "fever": 1, "chills": 1, "body_pain": 1}),
    ("Herpes Zoster", {"skin_rash": 1, "body_pain": 1, "fatigue": 1, "headache": 1}),
    ("Impetigo", {"skin_rash": 1, "fever": 0, "itching": 0}),
    ("Pityriasis Rosea", {"skin_rash": 1, "itching": 1, "fatigue": 1}),
    ("Scabies", {"skin_rash": 1, "itching": 1, "body_pain": 0}),
    ("Heat Rash", {"skin_rash": 1, "itching": 1, "sweating": 1, "fever": 0}),
    ("Sunburn", {"skin_rash": 1, "fatigue": 1, "headache": 1}),
    ("Erythema Multiforme", {"skin_rash": 1, "itching": 1, "fever": 1}),
    ("Lichen Planus", {"skin_rash": 1, "itching": 1}),
    ("Nummular Eczema", {"skin_rash": 1, "itching": 1}),
    ("Stasis Dermatitis", {"skin_rash": 1, "itching": 1, "fatigue": 1}),
    ("Keratosis Pilaris", {"skin_rash": 1, "itching": 0}),
    ("Molluscum Contagiosum", {"skin_rash": 1, "itching": 0}),
    ("Hand Foot Mouth Disease", {"skin_rash": 1, "fever": 1, "sore_throat": 1, "fatigue": 1}),
    ("Chickenpox", {"skin_rash": 1, "fever": 1, "fatigue": 1, "headache": 1}),
    ("Measles-like Illness", {"skin_rash": 1, "fever": 1, "cough": 1}),
]

# Strip unknown keys from templates (e.g. "neck", "burning", "dry", "conjunctivitis")
_CLEAN: list[tuple[str, dict[str, int]]] = []
for lab, d in TEMPLATES:
    _CLEAN.append((lab, {k: v for k, v in d.items() if k in COLS}))
TEMPLATES = _CLEAN

OPTIONAL = ["fever", "cough", "fatigue", "sore_throat", "headache", "chills", "nausea", "body_pain", "vomiting"]


def augment(base: dict[str, int], rng: random.Random) -> dict[str, int]:
    out = dict(base)
    for k in OPTIONAL:
        if k not in out and rng.random() < 0.22:
            out[k] = 1
    return out


def main() -> None:
    out = ROOT / "data" / "ml" / "symptom_disease_training.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    rows: list[list[int | str]] = []

    for label, base in TEMPLATES:
        for _ in range(95):
            rows.append(jitter(_row(augment(base, rng)), rng) + [label])

    # Isolated high-signal features (match sparse NLP vectors)
    zi = {c: 0 for c in COLS}
    zi["chest_pain"] = 1
    chest_only = [zi[c] for c in COLS]
    for lab, n in [
        ("Stable Angina", 120),
        ("Costochondritis", 100),
        ("Acute Coronary Syndrome", 90),
        ("GERD with Chest Symptoms", 80),
    ]:
        for _ in range(n):
            rows.append(list(chest_only) + [lab])

    zi = {c: 0 for c in COLS}
    zi["cough"] = 1
    zi["rapid_breathing"] = 1
    cough_rapid = [zi[c] for c in COLS]
    for lab, n in [
        ("Asthma Exacerbation", 95),
        ("Acute Bronchospasm", 85),
        ("Pneumonia", 35),
    ]:
        for _ in range(n):
            rows.append(list(cough_rapid) + [lab])

    zi = {c: 0 for c in COLS}
    zi["dizziness"] = 1
    zi["nausea"] = 1
    dizz_nausea = [zi[c] for c in COLS]
    for lab, n in [
        ("BPPV", 75),
        ("Vestibular Neuritis", 65),
        ("Labyrinthitis", 55),
        ("Migraine", 30),
    ]:
        for _ in range(n):
            rows.append(list(dizz_nausea) + [lab])

    zi = {c: 0 for c in COLS}
    zi["abdominal_pain"] = 1
    zi["nausea"] = 1
    zi["vomiting"] = 1
    zi["body_pain"] = 1
    colic_like = [zi[c] for c in COLS]
    for lab, n in [
        ("Nephrolithiasis", 90),
        ("Nephrolithiasis with Fever", 55),
    ]:
        for _ in range(n):
            rows.append(list(colic_like) + [lab])

    # Fever-only / near-only — NLP often yields a single 1 on `fever`; without these rows
    # the tree lands in impure leaves and spreads mass to unrelated labels (e.g. BPPV).
    zi = {c: 0 for c in COLS}
    zi["fever"] = 1
    fever_only = [zi[c] for c in COLS]
    for lab, n in [
        ("Acute Viral Syndrome", 220),
        ("Influenza", 220),
        ("COVID-19", 140),
        ("Common Cold", 110),
        ("Dengue Fever", 85),
        ("Malaria", 85),
        ("Typhoid Fever", 75),
        ("Viral Pharyngitis", 70),
        ("Pyelonephritis", 65),
        ("Urinary Tract Infection", 65),
        ("Streptococcal Pharyngitis", 60),
        ("Heat Stroke", 55),
        ("Viral Exanthem", 50),
        ("Cellulitis", 45),
        ("Chickenpox", 40),
    ]:
        for _ in range(n):
            rows.append(list(fever_only) + [lab])

    zi = {c: 0 for c in COLS}
    zi["fever"] = 1
    zi["fatigue"] = 1
    fever_fatigue = [zi[c] for c in COLS]
    for lab, n in [
        ("Influenza", 90),
        ("Acute Viral Syndrome", 90),
        ("COVID-19", 60),
        ("Common Cold", 55),
        ("Malaria", 40),
    ]:
        for _ in range(n):
            rows.append(list(fever_fatigue) + [lab])

    zi = {c: 0 for c in COLS}
    zi["skin_rash"] = 1
    skin_only = [zi[c] for c in COLS]
    for lab, n in [
        ("Urticaria", 140),
        ("Contact Dermatitis", 120),
        ("Viral Exanthem", 100),
        ("Atopic Dermatitis", 90),
        ("Drug Eruption", 70),
    ]:
        for _ in range(n):
            rows.append(list(skin_only) + [lab])

    zi = {c: 0 for c in COLS}
    zi["skin_rash"] = 1
    zi["itching"] = 1
    rash_itch = [zi[c] for c in COLS]
    for lab, n in [
        ("Urticaria", 100),
        ("Acute Urticaria", 90),
        ("Contact Dermatitis", 80),
        ("Atopic Dermatitis", 70),
        ("Scabies", 60),
    ]:
        for _ in range(n):
            rows.append(list(rash_itch) + [lab])

    zi = {c: 0 for c in COLS}
    zi["itching"] = 1
    itch_only = [zi[c] for c in COLS]
    for lab, n in [("Urticaria", 80), ("Atopic Dermatitis", 70), ("Contact Dermatitis", 60)]:
        for _ in range(n):
            rows.append(list(itch_only) + [lab])

    # Extra random combination coverage (same label family stability)
    for _ in range(2500):
        label, base = rng.choice(TEMPLATES)
        noise = {c: (1 if rng.random() < 0.08 else 0) for c in COLS}
        merged = merge(base, noise)
        rows.append(jitter(_row(merged), rng, rate=0.055) + [label])

    rng.shuffle(rows)

    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(list(COLS) + ["label"])
        w.writerows(rows)

    print(f"Wrote {len(rows)} rows × {len(COLS)} features to {out}")


if __name__ == "__main__":
    main()
