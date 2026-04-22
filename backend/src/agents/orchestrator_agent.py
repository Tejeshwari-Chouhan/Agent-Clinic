"""Decision Orchestrator — runs the full multi-agent triage flow."""

from __future__ import annotations

import json
from typing import Any, Dict, List

from src.agents.base_agent import BaseAgent
from src.agents.clinic_agent import ClinicAgent
from src.agents.emergency_routing_agent import EmergencyRoutingAgent
from src.agents.pharmaceutical_agent import PharmaceuticalAgent
from src.agents.routing_agent import RoutingAgent
from src.agents.severity_scoring_agent import SeverityScoringAgent
from src.agents.symptom_understanding_agent import SymptomUnderstandingAgent
from src.agents.triage_decision_agent import TriageDecisionAgent
from src.services.ml_predictor import MLPredictor


class OrchestratorAgent(BaseAgent):
    """Coordinates symptom understanding → ML → severity → triage → routing branches."""

    RED_FLAG_KEYWORDS = [
        "chest pain",
        "shortness of breath",
        "trouble breathing",
        "difficulty breathing",
        "stroke",
        "slurred speech",
        "one sided weakness",
        "unconscious",
        "fainting",
        "seizure",
        "severe bleeding",
        "vomiting blood",
        "blood in vomit",
        "suicidal",
        "severe allergic reaction",
        "anaphylaxis",
    ]
    PATHWAY_EMERGENCY = "Emergency"
    PATHWAY_URGENT_CARE = "Urgent Care"
    PATHWAY_SELF_CARE = "Self-Care"

    _SEVERITY_RANK = {"High": 3, "Medium": 2, "Low": 1}

    def __init__(self) -> None:
        system_prompt = """You are the decision orchestrator for a multi-agent triage assistant.
You receive structured outputs from specialized agents and must synthesize a concise,
patient-friendly summary and next steps. Never contradict emergency instructions."""
        super().__init__("OrchestratorAgent", system_prompt)

        self.symptom_agent = SymptomUnderstandingAgent()
        self.severity_agent = SeverityScoringAgent()
        self.ml_predictor = MLPredictor()
        self.triage_agent = TriageDecisionAgent()
        self.pharma_agent = PharmaceuticalAgent()
        self.routing_agent = RoutingAgent()
        self.emergency_routing_agent = EmergencyRoutingAgent()
        self.clinic_agent = ClinicAgent()

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = self._normalize_input(input_data)

        agent_flow: Dict[str, Any] = {}

        symptom_understanding = self.symptom_agent.process({"symptoms": normalized["symptoms"]})
        agent_flow["symptom_understanding"] = {
            "agent": "SymptomUnderstandingAgent",
            "extracted_symptoms": symptom_understanding.get("extracted_symptoms"),
            "nlp_source": symptom_understanding.get("nlp_source"),
        }

        disease_probs = self.ml_predictor.predict(symptom_understanding)
        disease_probs = self.ml_predictor.validate_with_patient_context(disease_probs, normalized["patient_context"])
        disease_probs = self.ml_predictor.rank_by_probability(disease_probs)
        agent_flow["disease_prediction"] = {
            "agent": "DiseasePredictionAgent_ML",
            "top_predictions": [{"condition": c, "probability": round(p, 4)} for c, p in disease_probs[:5]],
        }

        severity_result = self.severity_agent.process(
            {
                "symptoms": normalized["symptoms"],
                "disease_probabilities": disease_probs,
                "symptom_understanding": symptom_understanding,
                "medical_history": {},
                "patient_age": normalized["patient_age"],
            }
        )
        agent_flow["severity_scoring"] = {"agent": "SeverityScoringAgent", **severity_result}

        decision_trace = {
            "safety_override_triggered": False,
            "override_keywords": [],
            "triage_confidence": None,
            "fallback_used": False,
            "pharma_invoked": False,
        }

        override = self._safety_override(normalized["symptoms"])
        if override:
            triage_decision = override
            decision_trace["safety_override_triggered"] = True
            decision_trace["override_keywords"] = override.get("matched_keywords", [])
        else:
            triage_input = {
                "disease_probabilities": disease_probs,
                "symptoms": normalized["symptoms"],
                "patient_age": normalized["patient_age"],
                "comorbidities": normalized["comorbidities"],
                "test_reports": normalized["patient_context"].get("test_reports", []),
                "known_conditions": normalized["patient_context"].get("known_conditions", []),
                "severity_hint": severity_result,
            }
            try:
                raw_triage = self.triage_agent.process(triage_input)
            except Exception:
                raw_triage = {}
            triage_decision = self._validate_triage_output(raw_triage, disease_probs)
            decision_trace["fallback_used"] = triage_decision.get("_fallback_used", False)
            decision_trace["triage_confidence"] = triage_decision.get("confidence_score")

        triage_decision.pop("matched_keywords", None)
        triage_decision.pop("_fallback_used", None)

        merged_severity = self._merge_severity_levels(
            triage_decision.get("severity_level", "Medium"),
            severity_result.get("severity_level", "Medium"),
            override,
        )
        triage_decision["severity_level"] = merged_severity
        triage_decision["severity_score"] = severity_result.get("severity_score")
        triage_decision["severity_rationale"] = severity_result.get("rationale")

        emergency_routing: Dict[str, Any] = {}
        clinic_guidance: Dict[str, Any] = {}
        routing_guidance: Dict[str, Any] = {}
        nearby_hospitals: Dict[str, Any] = {
            "routing_source": "none",
            "facilities": [],
            "message": "",
        }

        if merged_severity == "High":
            emergency_routing = self.emergency_routing_agent.process(
                {
                    "patient_location": normalized["patient_location"],
                    "condition": triage_decision.get("primary_condition", ""),
                    "mobility_status": normalized["mobility_status"],
                }
            )
            agent_flow["emergency_routing"] = {"agent": "EmergencyRoutingAgent", "er_locator": emergency_routing.get("er_locator")}
            routing_guidance = {
                "routing_pathway": self.PATHWAY_EMERGENCY,
                "facility_type": "Emergency Department",
                "pre_arrival_instructions": [
                    emergency_routing.get("emergency_instruction", "Call emergency services immediately."),
                    "Do not drive yourself if you feel faint, confused, or short of breath.",
                ],
                "follow_up_guidance": ["After stabilization, follow ED discharge instructions closely."],
                "emergency_contacts": ["911", "112", "108 (ambulance India)"],
                "estimated_wait_time": "Unknown",
                "special_considerations": [],
                "emergency_routing": emergency_routing,
            }
            pharma_recommendations = {
                "recommendations": [],
                "drug_interactions": [],
                "otc_alternatives": [],
                "warnings": [
                    "Emergency severity — do not self-medicate before emergency evaluation unless directed by dispatch."
                ],
            }
        else:
            routing_input = {
                "severity_level": merged_severity,
                "condition": triage_decision.get("primary_condition", ""),
                "patient_location": normalized["patient_location"],
                "comorbidities": normalized["comorbidities"],
                "mobility_status": normalized["mobility_status"],
            }
            try:
                raw_routing = self.routing_agent.process(routing_input)
            except Exception:
                raw_routing = {}
            routing_guidance = self._validate_routing_output(raw_routing, merged_severity)

            clinic_guidance = self.clinic_agent.process(
                {
                    "severity_level": merged_severity,
                    "primary_condition": triage_decision.get("primary_condition", ""),
                    "symptoms": normalized["symptoms"],
                    "patient_location": normalized["patient_location"],
                    "comorbidities": normalized["comorbidities"],
                }
            )
            agent_flow["clinic"] = {"agent": "ClinicAgent", "pathway": clinic_guidance.get("clinic_pathway")}

            if merged_severity in ["Medium", "Low"]:
                pharma_input = {
                    "condition": triage_decision.get("primary_condition", ""),
                    "severity": merged_severity,
                    "current_medications": normalized["current_medications"],
                    "allergies": normalized["allergies"],
                    "patient_age": normalized["patient_age"],
                }
                try:
                    pharma_recommendations = self.pharma_agent.process(pharma_input)
                except Exception:
                    pharma_recommendations = {
                        "recommendations": [],
                        "drug_interactions": [],
                        "otc_alternatives": [],
                        "warnings": ["Unable to generate pharmaceutical guidance. Consult a clinician."],
                    }
                decision_trace["pharma_invoked"] = True
            else:
                pharma_recommendations = {
                    "recommendations": [],
                    "drug_interactions": [],
                    "otc_alternatives": [],
                    "warnings": [],
                }

            if normalized["patient_location"].strip():
                try:
                    nearby_hospitals = self.emergency_routing_agent.nearby_hospitals(normalized["patient_location"])
                except Exception:
                    nearby_hospitals = {
                        "routing_source": "error",
                        "facilities": [],
                        "message": "Unable to load nearby hospitals for this location.",
                    }

            base_cg = clinic_guidance if isinstance(clinic_guidance, dict) else {}
            clinic_guidance = {**base_cg, "nearby_hospitals": nearby_hospitals}

        agent_flow["pharmacy"] = {"agent": "PharmacyAgent", "invoked": decision_trace["pharma_invoked"]}
        if merged_severity == "High":
            er_fac = emergency_routing.get("er_locator", {}).get("facilities") or []
            if er_fac:
                agent_flow["emergency_routing"]["hospital_count"] = len(er_fac)
        elif isinstance(clinic_guidance, dict):
            nh = clinic_guidance.get("nearby_hospitals") or {}
            if nh.get("facilities"):
                agent_flow.setdefault("clinic", {})["nearby_hospital_count"] = len(nh["facilities"])

        hospital_context = ""
        if merged_severity == "High" and emergency_routing:
            hospital_context = json.dumps(emergency_routing.get("er_locator", {}))
        elif isinstance(clinic_guidance, dict):
            hospital_context = json.dumps(clinic_guidance.get("nearby_hospitals", {}))

        synthesis_prompt = f"""Synthesize this triage package for the patient in plain language:
Triage: {json.dumps(triage_decision)}
Routing: {json.dumps({k: v for k, v in routing_guidance.items() if k != 'emergency_routing'})}
Clinic: {json.dumps(clinic_guidance)}
Pharmacy: {json.dumps(pharma_recommendations)}
Hospital / facility hints (informational): {hospital_context}
"""
        try:
            synthesis = self.get_response(synthesis_prompt)
        except Exception:
            synthesis = self._build_fallback_summary(triage_decision, routing_guidance, clinic_guidance)

        return {
            "agent_flow": agent_flow,
            "symptom_understanding": symptom_understanding,
            "disease_probabilities": [{"condition": c, "probability": p} for c, p in disease_probs],
            "severity_scoring": severity_result,
            "triage_decision": triage_decision,
            "pharmaceutical_recommendations": pharma_recommendations,
            "clinic_guidance": clinic_guidance,
            "routing_guidance": routing_guidance,
            "emergency_routing": emergency_routing,
            "patient_summary": synthesis,
            "next_steps": routing_guidance.get("pre_arrival_instructions", []),
            "warnings": triage_decision.get("safety_warnings", []),
            "decision_trace": decision_trace,
        }

    def _merge_severity_levels(self, triage_level: str, scored_level: str, override: Dict[str, Any] | None) -> str:
        levels = [scored_level, triage_level]
        if override:
            levels.append("High")
        best = "Low"
        best_rank = 0
        for lvl in levels:
            rank = self._SEVERITY_RANK.get(lvl, 1)
            if rank > best_rank:
                best = lvl
                best_rank = rank
        return best

    def _build_fallback_summary(
        self,
        triage_decision: Dict[str, Any],
        routing_guidance: Dict[str, Any],
        clinic_guidance: Dict[str, Any],
    ) -> str:
        clinic_path = clinic_guidance.get("clinic_pathway", "")
        clinic_bits = f" Clinic guidance: {clinic_path}." if clinic_path else ""
        return (
            f"Severity: {triage_decision.get('severity_level', 'Unknown')} "
            f"(score {triage_decision.get('severity_score', 'n/a')}). "
            f"Likely focus: {triage_decision.get('primary_condition', 'Unknown')}. "
            f"Action: {triage_decision.get('recommended_action', 'Consult a healthcare provider')}. "
            f"Routing: {routing_guidance.get('routing_pathway', 'Unknown')}.{clinic_bits}"
        )

    def _normalize_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        patient_ctx = input_data.get("patient_context")
        if not isinstance(patient_ctx, dict):
            patient_ctx = {}

        return {
            "symptoms": str(input_data.get("symptoms", "")).strip(),
            "disease_probabilities": input_data.get("disease_probabilities", []) or [],
            "patient_age": input_data.get("patient_age"),
            "current_medications": input_data.get("current_medications", []) or [],
            "allergies": input_data.get("allergies", []) or [],
            "comorbidities": input_data.get("comorbidities", []) or [],
            "patient_location": str(input_data.get("patient_location", "") or ""),
            "mobility_status": str(input_data.get("mobility_status", "Mobile") or "Mobile"),
            "patient_context": patient_ctx,
        }

    def _safety_override(self, symptoms: str) -> Dict[str, Any]:
        symptoms_lower = symptoms.lower()
        matched = [k for k in self.RED_FLAG_KEYWORDS if k in symptoms_lower]
        if not matched:
            return {}

        return {
            "severity_level": "High",
            "primary_condition": "Potential emergency condition",
            "confidence_score": 1.0,
            "reasoning": "Emergency red-flag symptoms detected via deterministic safety policy.",
            "recommended_action": "Call emergency services or go to the nearest emergency department now.",
            "safety_warnings": ["Do not delay care. If symptoms worsen, call emergency services immediately."],
            "matched_keywords": matched,
            "_fallback_used": False,
        }

    def _validate_triage_output(
        self, triage_decision: Dict[str, Any], disease_probabilities: List[Any]
    ) -> Dict[str, Any]:
        if not isinstance(triage_decision, dict):
            triage_decision = {}

        severity = str(triage_decision.get("severity_level", "Medium")).strip().title()
        if severity not in ["High", "Medium", "Low"]:
            severity = "Medium"

        primary_condition = triage_decision.get("primary_condition")
        if not primary_condition:
            if disease_probabilities and isinstance(disease_probabilities[0], (list, tuple)):
                primary_condition = str(disease_probabilities[0][0])
            else:
                primary_condition = "Unknown"

        confidence = triage_decision.get("confidence_score", 0.5)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))

        warnings = triage_decision.get("safety_warnings", [])
        if not isinstance(warnings, list):
            warnings = [str(warnings)] if warnings else []

        fallback_used = bool(
            not triage_decision
            or "severity_level" not in triage_decision
            or "recommended_action" not in triage_decision
        )

        return {
            "severity_level": severity,
            "primary_condition": primary_condition,
            "confidence_score": confidence,
            "reasoning": triage_decision.get("reasoning", "Clinical triage reasoning unavailable."),
            "recommended_action": triage_decision.get(
                "recommended_action", "Consult a healthcare provider for further evaluation."
            ),
            "safety_warnings": warnings,
            "_fallback_used": fallback_used,
        }

    def _validate_routing_output(self, routing_guidance: Dict[str, Any], severity: str) -> Dict[str, Any]:
        if not isinstance(routing_guidance, dict):
            routing_guidance = {}

        pathway = routing_guidance.get("routing_pathway")
        if pathway not in [self.PATHWAY_EMERGENCY, self.PATHWAY_URGENT_CARE, self.PATHWAY_SELF_CARE]:
            if severity == "High":
                pathway = self.PATHWAY_EMERGENCY
            elif severity == "Low":
                pathway = self.PATHWAY_SELF_CARE
            else:
                pathway = self.PATHWAY_URGENT_CARE

        return {
            "routing_pathway": pathway,
            "facility_type": routing_guidance.get("facility_type", self._default_facility_type(pathway)),
            "pre_arrival_instructions": self._to_list(routing_guidance.get("pre_arrival_instructions")),
            "follow_up_guidance": self._to_list(routing_guidance.get("follow_up_guidance")),
            "emergency_contacts": self._to_list(routing_guidance.get("emergency_contacts")) or ["911"],
            "estimated_wait_time": routing_guidance.get("estimated_wait_time", "Unknown"),
            "special_considerations": self._to_list(routing_guidance.get("special_considerations")),
        }

    def _default_facility_type(self, pathway: str) -> str:
        facility_map = {
            self.PATHWAY_EMERGENCY: "Emergency Department",
            self.PATHWAY_URGENT_CARE: "Urgent Care Center",
            self.PATHWAY_SELF_CARE: "Pharmacy",
        }
        return facility_map.get(pathway, "Healthcare Facility")

    def _to_list(self, value: Any) -> List[str]:
        if isinstance(value, list):
            return [str(item) for item in value]
        if value:
            return [str(value)]
        return []
