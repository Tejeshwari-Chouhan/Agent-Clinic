"""Symptom Understanding Agent — maps natural language to structured symptom features for ML."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

from src.agents.base_agent import BaseAgent
from src.dp_train_utils import SYMPTOMS

# Same columns as `data/ml/symptom_disease_training.csv` (via dp_train_utils)
FEATURE_COLUMNS: List[str] = list(SYMPTOMS)

# Keywords / phrases → feature name (first match wins per line via scan)
KEYWORD_MAP: Dict[str, List[str]] = {
    "fever": ["fever", "febrile", "temperature", "high temp", "burning up", "feeling hot"],
    "cough": ["cough", "coughing", "hacking"],
    "headache": ["headache", "head ache", "migraine", "head pain"],
    "nausea": ["nausea", "nauseous", "queasy", "sick to my stomach"],
    "vomiting": ["vomit", "vomiting", "throwing up", "threw up"],
    "fatigue": ["fatigue", "tired", "exhausted", "weakness", "lethargic", "no energy"],
    "sore_throat": ["sore throat", "throat pain", "painful swallow", "scratchy throat"],
    "chills": ["chills", "shivering", "rigors"],
    "body_pain": ["body ache", "body pain", "muscle pain", "myalgia", "aches", "joint pain"],
    "loss_of_appetite": ["loss of appetite", "no appetite", "not eating"],
    "abdominal_pain": ["abdominal", "stomach pain", "belly pain", "cramps", "stomach ache"],
    "diarrhea": ["diarrhea", "diarrhoea", "loose stools", "watery stool"],
    "sweating": ["sweating", "night sweats", "sweats"],
    "chest_pain": [
        "chest pain",
        "chest pressure",
        "chest tightness",
        "crushing chest",
        "pain in chest",
        "chest hurts",
        "hurts in my chest",
        "substernal",
        "retrosternal",
        "precordial",
        "angina",
        "heart pain",
    ],
    "rapid_breathing": [
        "rapid breathing",
        "fast breathing",
        "shortness of breath",
        "breathless",
        "difficulty breathing",
        "trouble breathing",
        "can't breathe",
        "labored breathing",
    ],
    "dizziness": ["dizzy", "dizziness", "vertigo", "lightheaded", "light-headed"],
    "skin_rash": [
        "skin rash",
        "rash on",
        "rashes",
        "hives",
        "urticaria",
        "welts",
        "eczema",
        "dermatitis",
        "peeling skin",
        "red spots",
        "spots on skin",
        "blisters on skin",
        "maculopapular",
        "petechiae",
        "purpura",
    ],
    "itching": [
        "itchy",
        "itching",
        "itch all over",
        "pruritus",
        "itchy skin",
        "itches",
    ],
}


class SymptomUnderstandingAgent(BaseAgent):
    """Extracts structured symptom vector from free text; optional LLM refinement when API key is set."""

    def __init__(self):
        super().__init__(
            "SymptomUnderstandingAgent",
            system_prompt=(
                "You extract clinical symptom features from patient text. "
                "Only use information stated or clearly implied. "
                "Output strict JSON with keys: "
                + json.dumps(FEATURE_COLUMNS + ["extracted_symptom_phrases", "clinical_notes"])
                + " where each of the first keys is 0 or 1."
            ),
        )

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        text = str(input_data.get("symptoms", "") or "").strip()
        keyword_vector, phrases = self._keyword_extraction(text)
        llm_vector: Dict[str, int] | None = None
        notes = ""

        if os.getenv("OPENAI_API_KEY") and text:
            try:
                llm_vector, notes = self._llm_extraction(text)
            except Exception:
                llm_vector = None

        merged = dict(keyword_vector)
        if llm_vector:
            for col in FEATURE_COLUMNS:
                merged[col] = max(int(merged.get(col, 0)), int(llm_vector.get(col, 0)))

        ordered = [int(merged.get(c, 0)) for c in FEATURE_COLUMNS]
        return {
            "raw_input": text,
            "symptom_vector": merged,
            "feature_order": FEATURE_COLUMNS,
            "feature_array": ordered,
            "extracted_symptoms": [c for c in FEATURE_COLUMNS if merged.get(c)],
            "extracted_symptom_phrases": phrases,
            "nlp_source": "llm+keywords" if llm_vector else "keywords",
            "clinical_notes": notes or None,
        }

    def _keyword_extraction(self, text: str) -> tuple[Dict[str, int], List[str]]:
        lower = text.lower()
        vector = {c: 0 for c in FEATURE_COLUMNS}
        phrases: List[str] = []

        for feature, needles in KEYWORD_MAP.items():
            for needle in needles:
                if needle in lower:
                    vector[feature] = 1
                    phrases.append(needle)
                    break

        # If nothing matched but user wrote something clinical-ish, avoid all-zero by soft signal
        if not any(vector.values()) and len(lower) >= 8:
            if re.search(r"chest|chest wall|sternum|precordial|substernal|retrosternal", lower) and re.search(
                r"pain|pressure|tight|ache|discomfort|heavy|hurts|hurting", lower
            ):
                vector["chest_pain"] = 1
                phrases.append("chest discomfort (pattern)")
            elif re.search(
                r"\b(rash|rashes|hives|urticaria|eczema|dermatitis|peeling|maculopapular|petechiae|purpura)\b",
                lower,
            ) or (re.search(r"\bskin\b", lower) and re.search(r"\b(rash|rashes|spots|bumps|red|lesions?)\b", lower)):
                vector["skin_rash"] = 1
                if re.search(r"\b(itch|itchy|itching|pruritus)\b", lower):
                    vector["itching"] = 1
                phrases.append("skin complaint (pattern)")
            elif re.search(r"\b(pain|hurt|sick|ill|unwell|symptom)\b", lower):
                vector["fatigue"] = max(vector["fatigue"], 1)
                phrases.append("non-specific complaint")

        return vector, phrases

    def _llm_extraction(self, text: str) -> tuple[Dict[str, int], str]:
        self.clear_history()
        prompt = (
            f'Patient says:\n"""{text}"""\n\n'
            "Return JSON only. Keys: "
            + ", ".join(FEATURE_COLUMNS)
            + ', "extracted_symptom_phrases" (array of short strings), '
            '"clinical_notes" (one short string). '
            "Each symptom key must be 0 or 1."
        )
        raw = self.get_response(prompt)
        start, end = raw.find("{"), raw.rfind("}") + 1
        payload = json.loads(raw[start:end])
        vec = {}
        for col in FEATURE_COLUMNS:
            vec[col] = 1 if int(payload.get(col, 0)) else 0
        notes = str(payload.get("clinical_notes", ""))
        return vec, notes
