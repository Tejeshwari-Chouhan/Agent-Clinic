"""Severity Scoring Agent — combines symptoms, ML confidence, and history into a triage severity score."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


class SeverityScoringAgent:
    """
    Deterministic severity scoring (0–100) and High/Medium/Low band.
    Designed to complement (not replace) clinical LLM triage when an API key is available.
    """

    RED_FLAG_KEYWORDS = [
        "chest pain",
        "crushing chest",
        "heart attack",
        "shortness of breath",
        "can't breathe",
        "cannot breathe",
        "trouble breathing",
        "difficulty breathing",
        "stroke",
        "slurred speech",
        "one sided weakness",
        "one-sided weakness",
        "unconscious",
        "unresponsive",
        "fainting",
        "passed out",
        "seizure",
        "severe bleeding",
        "vomiting blood",
        "blood in vomit",
        "suicidal",
        "severe allergic",
        "anaphylaxis",
    ]

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        symptoms_text = str(input_data.get("symptoms", "") or "").lower()
        disease_probs: List[Tuple[str, float]] = input_data.get("disease_probabilities") or []
        understood = input_data.get("symptom_understanding") or {}
        history = input_data.get("medical_history") or {}
        patient_age = input_data.get("patient_age")

        components: Dict[str, float] = {}
        score = 0.0

        matched_red = [k for k in self.RED_FLAG_KEYWORDS if k in symptoms_text]
        if matched_red:
            components["red_flag"] = 45.0
            score += 45.0

        top_prob = float(disease_probs[0][1]) if disease_probs else 0.0
        ml_component = min(35.0, top_prob * 38.0)
        components["ml_confidence"] = ml_component
        score += ml_component

        vec = understood.get("symptom_vector") or {}
        active = sum(1 for c, v in vec.items() if int(v or 0))
        burden = min(22.0, active * 2.8)
        components["symptom_burden"] = burden
        score += burden

        if history.get("risk_flags"):
            hist_boost = min(12.0, 4.0 * len(history["risk_flags"]))
            components["history_risk"] = hist_boost
            score += hist_boost

        try:
            age = int(patient_age) if patient_age is not None else None
        except (TypeError, ValueError):
            age = None
        if age is not None and (age < 5 or age >= 75):
            components["age_vulnerability"] = 8.0
            score += 8.0

        # Rapid breathing / dizziness in vector add urgency when ML is uncertain
        if int(vec.get("rapid_breathing", 0)):
            components["respiratory_distress_signal"] = 10.0
            score += 10.0
        if int(vec.get("vomiting", 0)) and int(vec.get("diarrhea", 0)):
            components["dehydration_pattern"] = 6.0
            score += 6.0

        score = max(0.0, min(100.0, score))

        if matched_red or score >= 72.0:
            level = "High"
        elif score >= 42.0:
            level = "Medium"
        else:
            level = "Low"

        return {
            "severity_level": level,
            "severity_score": round(score, 1),
            "score_components": components,
            "matched_red_flags": matched_red,
            "rationale": self._rationale(level, score, matched_red, disease_probs[:3]),
        }

    def _rationale(
        self,
        level: str,
        score: float,
        red: List[str],
        top_conditions: List[Tuple[str, float]],
    ) -> str:
        parts = [f"Composite score {score:.1f}/100 mapped to {level}."]
        if red:
            parts.append(f"Red-flag language: {', '.join(red[:4])}.")
        if top_conditions:
            top_fmt = ", ".join(f"{c} ({p:.0%})" for c, p in top_conditions)
            parts.append(f"Top ML hypotheses: {top_fmt}.")
        return " ".join(parts)
