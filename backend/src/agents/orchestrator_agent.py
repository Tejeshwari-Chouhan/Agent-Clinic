"""Orchestrator Agent - Coordinates all agents and manages the triage workflow"""

import time
import json
from typing import Dict, Any, List

from src.agents.base_agent import BaseAgent
from src.agents.triage_decision_agent import TriageDecisionAgent
from src.agents.pharmaceutical_agent import PharmaceuticalAgent
from src.agents.routing_agent import RoutingAgent
from src.services.rag_service import RAGService
from src.services.emergency_router import EmergencyRouter


class OrchestratorAgent(BaseAgent):
    """Master agent that orchestrates the Predict-then-Act triage workflow."""

    def __init__(self):
        system_prompt = """You are the master orchestrator for a clinical healthcare triage system.
Your role is to synthesize outputs from specialist agents into clear, actionable patient guidance.
Always prioritize patient safety. For high-severity cases, emphasize urgency.
Provide a concise, plain-language patient summary (2-3 sentences maximum)."""

        super().__init__('OrchestratorAgent', system_prompt)

        self.triage_agent = TriageDecisionAgent()
        self.pharma_agent = PharmaceuticalAgent()
        self.routing_agent = RoutingAgent()
        self.rag_service = RAGService()
        self.emergency_router = EmergencyRouter()

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the full Predict-then-Act pipeline.

        Input keys: symptoms, disease_probabilities, patient_age,
                    current_medications, allergies, comorbidities,
                    patient_location, mobility_status
        """
        start_time = time.time()

        symptoms = input_data.get('symptoms', '')
        disease_probs = input_data.get('disease_probabilities', [])
        patient_age = input_data.get('patient_age')
        current_medications = input_data.get('current_medications', [])
        allergies = input_data.get('allergies', [])
        comorbidities = input_data.get('comorbidities', [])
        patient_location = input_data.get('patient_location', '')
        mobility_status = input_data.get('mobility_status', 'Mobile')

        # ── Step 1: Triage Decision (LLM + disease probabilities) ─────────────
        triage_decision = self.triage_agent.process({
            'disease_probabilities': disease_probs,
            'symptoms': symptoms,
            'patient_age': patient_age,
            'comorbidities': comorbidities,
        })

        severity = triage_decision.get('severity_level', 'Medium')
        primary_condition = triage_decision.get('primary_condition', '')

        # ── Step 2: Pharmaceutical Guidance (RAG for non-emergency) ───────────
        pharma_recommendations = {}
        if severity in ('Medium', 'Low'):
            # Use RAG knowledge base first (fast, no LLM call needed)
            rag_result = self.rag_service.get_recommendations(
                condition=primary_condition,
                patient_age=patient_age,
                current_medications=current_medications,
                allergies=allergies,
            )

            # Supplement with LLM agent for extra context/interactions
            pharma_llm = self.pharma_agent.process({
                'condition': primary_condition,
                'severity': severity,
                'current_medications': current_medications,
                'allergies': allergies,
                'patient_age': patient_age,
            })

            # Merge: RAG data is primary, LLM supplements where RAG has gaps
            pharma_recommendations = {
                **rag_result,
                'llm_recommendations': pharma_llm.get('recommendations', []),
                'drug_interactions': (
                    rag_result.get('drug_interactions', []) +
                    pharma_llm.get('drug_interactions', [])
                ),
                'otc_alternatives': (
                    rag_result.get('otc_alternatives', []) or
                    pharma_llm.get('otc_alternatives', [])
                ),
                'warnings': list(set(
                    rag_result.get('warnings', []) + pharma_llm.get('warnings', [])
                )),
            }
        elif severity == 'High':
            # For emergencies, provide only OTC supportive care info — no prescription guidance
            pharma_recommendations = {
                'condition': primary_condition,
                'severity': 'High',
                'recommendations': [],
                'supportive_care': ['Proceed to emergency department immediately — do not self-medicate'],
                'warnings': ['HIGH SEVERITY: Emergency care required — no OTC treatment recommended'],
                'drug_interactions': [],
                'otc_alternatives': [],
            }

        # ── Step 3: Routing (structured service + LLM agent) ─────────────────
        # Structured router for facility data
        routing_data = self.emergency_router.route(
            severity=severity,
            condition=primary_condition,
            patient_location=patient_location,
            comorbidities=comorbidities,
            mobility_status=mobility_status,
        )

        # LLM routing agent for nuanced instructions
        routing_llm = self.routing_agent.process({
            'severity_level': severity,
            'condition': primary_condition,
            'patient_location': patient_location,
            'comorbidities': comorbidities,
            'mobility_status': mobility_status,
        })

        # Merge routing: structured data for facilities, LLM for instructions
        routing_guidance = {
            **routing_data,
            'routing_pathway': routing_data.get('routing_pathway'),
            'facility_type': routing_data.get('facility_type'),
            'pre_arrival_instructions': (
                routing_data.get('pre_arrival_instructions', []) or
                routing_llm.get('pre_arrival_instructions', [])
            ),
            'follow_up_guidance': (
                routing_data.get('follow_up_guidance', []) or
                routing_llm.get('follow_up_guidance', [])
            ),
            'special_considerations': list(set(
                routing_data.get('special_considerations', []) +
                routing_llm.get('special_considerations', [])
            )),
        }

        # ── Step 4: Patient Summary (LLM synthesis) ───────────────────────────
        patient_summary = self._synthesize_summary(
            severity, primary_condition, disease_probs, symptoms
        )

        # ── Step 5: Compile Next Steps & Warnings ─────────────────────────────
        next_steps = self._compile_next_steps(severity, routing_guidance, pharma_recommendations)
        warnings = self._compile_warnings(triage_decision, pharma_recommendations, severity)

        elapsed_ms = round((time.time() - start_time) * 1000, 1)

        return {
            'triage_decision': triage_decision,
            'pharmaceutical_recommendations': pharma_recommendations,
            'routing_guidance': routing_guidance,
            'patient_summary': patient_summary,
            'next_steps': next_steps,
            'warnings': warnings,
            'processing_time_ms': elapsed_ms,
        }

    def _synthesize_summary(
        self, severity: str, condition: str, disease_probs: list, symptoms: str
    ) -> str:
        """Generate concise plain-language patient summary."""
        prob_pct = f"{disease_probs[0][1]:.0%}" if disease_probs else "unknown"

        # Rule-based summary (always generated, works without LLM)
        rule_based = {
            'High': (
                f"Based on your symptoms, our AI analysis indicates a high probability of {condition} ({prob_pct}), "
                "a serious condition requiring immediate emergency care. "
                "Please call 911 or proceed to the nearest Emergency Department right away."
            ),
            'Medium': (
                f"Your symptoms are consistent with {condition} ({prob_pct} probability). "
                "This condition requires medical attention today — please visit an urgent care clinic or physician as soon as possible."
            ),
            'Low': (
                f"Your symptoms appear mild and are consistent with {condition} ({prob_pct} probability). "
                "You may manage this at home with rest and OTC medications, but monitor closely and see a doctor if symptoms worsen."
            ),
        }.get(severity, f"Please consult a healthcare provider for proper evaluation of your symptoms (possible {condition}).")

        # Attempt LLM enhancement if API available
        if not self._api_available:
            return rule_based

        top_probs = disease_probs[:3] if disease_probs else []
        prob_text = '; '.join([f"{c}: {p:.0%}" for c, p in top_probs])
        prompt = (
            f"Patient presents with: {symptoms}\n"
            f"Disease probabilities: {prob_text}\n"
            f"Triage decision: {severity} severity — {condition}\n\n"
            "Write a 2-sentence patient-friendly summary explaining the assessment "
            "and what the patient should do next. Use plain language, no medical jargon."
        )
        try:
            response = self.get_response(prompt)
            if response and 'error' not in response.lower()[:20]:
                return response
        except Exception:
            pass
        return rule_based

    def _compile_next_steps(
        self, severity: str, routing: dict, pharma: dict
    ) -> List[str]:
        steps = []
        pre_arrival = routing.get('pre_arrival_instructions', [])
        steps.extend(pre_arrival[:3])  # Top 3 routing instructions

        if severity in ('Medium', 'Low') and pharma.get('supportive_care'):
            steps.extend(pharma['supportive_care'][:2])

        follow_up = routing.get('follow_up_guidance', [])
        if follow_up:
            steps.append(follow_up[0])

        return steps

    def _compile_warnings(
        self, triage_decision: dict, pharma: dict, severity: str
    ) -> List[str]:
        warnings = []
        warnings.extend(triage_decision.get('safety_warnings', []))
        warnings.extend(pharma.get('warnings', []))

        if severity == 'High':
            warnings.insert(0, 'EMERGENCY: Seek immediate medical care — call 911 if unable to transport')

        return list(dict.fromkeys(warnings))  # deduplicate, preserve order
