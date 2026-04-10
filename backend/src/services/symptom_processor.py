"""Service for processing natural language symptom input into binary feature vectors"""

import re
from typing import Dict, List

# Keyword → feature mapping for the 15 binary symptom features
SYMPTOM_KEYWORD_MAP: Dict[str, List[str]] = {
    'fever': [
        'fever', 'febrile', 'high temperature', 'temperature', 'pyrexia',
        'hot', 'burning up', 'feverish'
    ],
    'cough': [
        'cough', 'coughing', 'coughs', 'dry cough', 'wet cough',
        'productive cough', 'persistent cough', 'hacking'
    ],
    'headache': [
        'headache', 'head pain', 'head ache', 'migraine', 'head hurts',
        'head is pounding', 'head pressure', 'skull pain'
    ],
    'nausea': [
        'nausea', 'nauseous', 'nauseated', 'feel like vomiting',
        'queasy', 'sick to my stomach', 'stomach turning'
    ],
    'vomiting': [
        'vomit', 'vomiting', 'throwing up', 'threw up', 'puking',
        'puke', 'vomited', 'emesis', 'retching'
    ],
    'fatigue': [
        'fatigue', 'tired', 'exhausted', 'weakness', 'weak', 'lethargy',
        'lethargic', 'no energy', 'low energy', 'run down', 'worn out',
        'sluggish', 'weary'
    ],
    'sore_throat': [
        'sore throat', 'throat pain', 'throat hurts', 'scratchy throat',
        'painful swallowing', 'difficulty swallowing', 'throat irritation',
        'pharyngitis', 'strep'
    ],
    'chills': [
        'chills', 'shivering', 'shiver', 'rigor', 'rigors', 'shaking',
        'feeling cold', 'cold sweats', 'goosebumps', 'teeth chattering'
    ],
    'body_pain': [
        'body pain', 'body ache', 'muscle pain', 'muscle ache', 'aching',
        'myalgia', 'joint pain', 'arthralgia', 'pain all over',
        'sore muscles', 'soreness'
    ],
    'loss_of_appetite': [
        'loss of appetite', 'no appetite', 'not hungry', 'anorexia',
        'not eating', 'cannot eat', 'food aversion', 'loss of hunger',
        'decreased appetite', 'not feeling like eating'
    ],
    'abdominal_pain': [
        'abdominal pain', 'stomach pain', 'belly pain', 'stomach ache',
        'stomachache', 'tummy pain', 'abdominal cramps', 'stomach cramps',
        'gut pain', 'stomach hurts', 'belly hurts'
    ],
    'diarrhea': [
        'diarrhea', 'diarrhoea', 'loose stool', 'watery stool',
        'loose motions', 'frequent bowel', 'runny stool', 'stomach running'
    ],
    'sweating': [
        'sweating', 'sweat', 'sweaty', 'night sweats', 'profuse sweating',
        'excessive sweating', 'perspiration', 'perspiring'
    ],
    'rapid_breathing': [
        'rapid breathing', 'shortness of breath', 'short of breath',
        'difficulty breathing', 'breathlessness', 'dyspnea', 'dyspnoea',
        'fast breathing', 'labored breathing', 'cannot breathe',
        'hard to breathe', 'breathing difficulty', 'chest tightness',
        'wheezing', 'breathing fast'
    ],
    'dizziness': [
        'dizziness', 'dizzy', 'lightheaded', 'light headed', 'vertigo',
        'spinning', 'room spinning', 'unsteady', 'faint', 'fainting',
        'blacking out'
    ],
}

# Build reverse lookup: normalized keyword → feature_name
_KEYWORD_TO_FEATURE: Dict[str, str] = {}
for feature, keywords in SYMPTOM_KEYWORD_MAP.items():
    for kw in keywords:
        _KEYWORD_TO_FEATURE[kw.lower()] = feature


class SymptomProcessor:
    """Processes natural language symptom descriptions into binary feature vectors."""

    def __init__(self):
        self.feature_cols = list(SYMPTOM_KEYWORD_MAP.keys())

    def parse_symptoms(self, symptom_text: str) -> Dict:
        """
        Parse symptom text → binary feature vector dict + metadata.

        Returns:
        {
            'raw_input': str,
            'extracted_symptoms': [str],   # feature names found
            'severity_indicators': [str],  # keywords like 'severe', 'mild'
            'feature_vector': {feature: 0/1, ...}  # 15 binary features
        }
        """
        normalized = self.normalize_terminology(symptom_text)
        feature_vector = {feat: 0 for feat in self.feature_cols}
        extracted = []

        # Try multi-word phrases first (longest match wins)
        for kw in sorted(_KEYWORD_TO_FEATURE.keys(), key=len, reverse=True):
            if kw in normalized:
                feat = _KEYWORD_TO_FEATURE[kw]
                if feature_vector[feat] == 0:
                    feature_vector[feat] = 1
                    extracted.append(feat)

        severity_indicators = self._extract_severity(normalized)

        return {
            'raw_input': symptom_text,
            'extracted_symptoms': extracted,
            'severity_indicators': severity_indicators,
            'feature_vector': feature_vector,
        }

    def validate_input(self, symptom_text: str) -> bool:
        """Return True only if at least one recognizable symptom is found."""
        if not symptom_text or not symptom_text.strip():
            return False
        parsed = self.parse_symptoms(symptom_text)
        return len(parsed['extracted_symptoms']) > 0 or len(symptom_text.strip()) >= 5

    def normalize_terminology(self, symptom_text: str) -> str:
        """Lowercase, strip punctuation, normalize whitespace."""
        text = symptom_text.lower()
        text = re.sub(r"[^\w\s]", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _extract_severity(self, normalized_text: str) -> List[str]:
        """Extract severity/urgency qualifiers from text."""
        severity_terms = {
            'severe': ['severe', 'severe pain', 'excruciating', 'unbearable', 'extreme'],
            'moderate': ['moderate', 'significant', 'considerable'],
            'mild': ['mild', 'slight', 'minor', 'a bit', 'little'],
            'sudden': ['sudden', 'suddenly', 'abrupt', 'acute'],
            'chronic': ['chronic', 'persistent', 'ongoing', 'weeks', 'months'],
        }
        found = []
        for level, terms in severity_terms.items():
            if any(term in normalized_text for term in terms):
                found.append(level)
        return found
