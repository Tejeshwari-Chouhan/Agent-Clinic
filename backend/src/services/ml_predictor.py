"""Service for ML-based disease probability prediction"""

class MLPredictor:
    """Predicts disease probabilities from symptoms"""
    
    def __init__(self):
        self.model = None
        self.conditions = []
    
    def predict(self, symptom_features: dict) -> list:
        """
        Calculate disease probability vector P(D|S)
        Returns list of (condition, probability) tuples
        """
        _ = symptom_features
        # Placeholder implementation
        return [
            ('Common Cold', 0.35),
            ('Flu', 0.25),
            ('Allergies', 0.20),
            ('Other', 0.20)
        ]
    
    def validate_probabilities(self, probabilities: list) -> bool:
        """Validate that probabilities sum to 1.0 (within tolerance)"""
        total = sum(prob for _, prob in probabilities)
        return abs(total - 1.0) < 0.01
    
    def rank_by_probability(self, probabilities: list) -> list:
        """Rank conditions by probability in descending order"""
        return sorted(probabilities, key=lambda x: x[1], reverse=True)

    def validate_with_patient_context(self, probabilities: list, patient_context: dict) -> list:
        """
        Reweight disease probabilities using historical patient context
        such as known conditions and test report markers, then renormalize.
        """
        if not probabilities:
            return []

        known_conditions = [str(item).lower() for item in patient_context.get('known_conditions', [])]
        report_markers = ' '.join(str(item).lower() for item in patient_context.get('test_reports', []))

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
