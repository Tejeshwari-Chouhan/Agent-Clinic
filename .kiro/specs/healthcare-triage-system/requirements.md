# Healthcare Triage System - Requirements Document

## Introduction

The Intelligent Healthcare Triage System is a digital health intermediary designed to address the gap between patient self-diagnosis and emergency room wait times. The system synthesizes natural language symptom input, predicts disease probability using machine learning, and orchestrates appropriate clinical actions through an LLM-based agent. By combining predictive analytics with intelligent decision-making, the system aims to reduce triage latency, improve diagnostic accuracy (measured by F1-score and Task Success Rate), and ensure high recall for emergency cases while providing appropriate guidance for non-urgent conditions.

## Glossary

- **Symptom_Input**: Natural language description of patient symptoms provided by the user
- **Disease_Probability_Vector**: A vector of probabilities P(D|S) representing the likelihood of each potential condition given observed symptoms
- **Triage_Agent**: An LLM-based agent that interprets disease probabilities and orchestrates appropriate clinical actions
- **Emergency_Routing**: The process of directing high-severity cases to the nearest emergency facility
- **Pharmaceutical_Guidance**: Recommendations for over-the-counter or prescription medications appropriate for the patient's condition
- **Drug_Interaction_Check**: Verification that recommended medications do not have harmful interactions with the patient's current medications
- **Severity_Level**: A classification of the patient's condition as High (emergency), Medium (urgent care), or Low (self-care/pharmacy)
- **Task_Success_Rate**: The percentage of triage decisions that result in appropriate clinical outcomes
- **F1_Score**: The harmonic mean of precision and recall, measuring diagnostic accuracy
- **Triage_Latency**: The time elapsed from symptom input submission to triage decision delivery
- **RAG_Pipeline**: Retrieval-Augmented Generation pipeline for accessing pharmaceutical and clinical knowledge
- **ML_Model**: Machine learning model that calculates disease probability vectors from symptom inputs
- **Closed_Loop_Experience**: A healthcare interaction that includes symptom assessment, triage decision, and follow-up guidance

## Requirements

### Requirement 1: Natural Language Symptom Input Processing

**User Story:** As a patient, I want to describe my symptoms in natural language, so that I can communicate my health concerns without requiring medical terminology.

#### Acceptance Criteria

1. WHEN a patient submits symptom text, THE Symptom_Processor SHALL parse the input and extract relevant clinical features
2. WHEN symptom input contains medical terminology, THE Symptom_Processor SHALL recognize and normalize the terms
3. WHEN symptom input is ambiguous or incomplete, THE Symptom_Processor SHALL request clarification from the patient
4. WHEN a patient submits symptom text, THE Symptom_Processor SHALL validate that the input contains at least one recognizable symptom
5. WHEN symptom input contains irrelevant information, THE Symptom_Processor SHALL filter out non-clinical content while preserving symptom descriptions

### Requirement 2: Disease Probability Prediction

**User Story:** As a clinician, I want the system to predict disease probabilities from symptoms, so that I can understand the likelihood of various conditions and make informed triage decisions.

#### Acceptance Criteria

1. WHEN symptom features are provided to the ML_Model, THE ML_Model SHALL calculate a Disease_Probability_Vector with probabilities for all known conditions
2. WHEN the ML_Model generates predictions, THE Disease_Probability_Vector SHALL contain probabilities that sum to 1.0 (or within 0.01 tolerance for numerical stability)
3. WHEN the ML_Model generates predictions, THE Disease_Probability_Vector SHALL rank conditions by probability in descending order
4. WHEN the ML_Model receives symptom input, THE ML_Model SHALL complete prediction within 500ms to meet latency requirements
5. WHEN the ML_Model generates predictions, THE predictions SHALL achieve an F1_Score of at least 0.75 on the validation dataset

### Requirement 3: LLM-Based Triage Agent Decision-Making

**User Story:** As a healthcare system, I want an intelligent agent to interpret disease probabilities and make triage decisions, so that appropriate clinical actions are triggered automatically.

#### Acceptance Criteria

1. WHEN the Triage_Agent receives a Disease_Probability_Vector, THE Triage_Agent SHALL classify the case into a Severity_Level (High, Medium, or Low)
2. WHEN the Triage_Agent classifies a case as High severity, THE Triage_Agent SHALL trigger Emergency_Routing immediately
3. WHEN the Triage_Agent classifies a case as Medium severity, THE Triage_Agent SHALL recommend urgent care consultation
4. WHEN the Triage_Agent classifies a case as Low severity, THE Triage_Agent SHALL provide self-care guidance and pharmaceutical recommendations
5. WHEN the Triage_Agent makes a triage decision, THE decision SHALL be accompanied by a confidence score between 0 and 1
6. WHEN the Triage_Agent makes a triage decision, THE decision SHALL include a brief explanation of the reasoning

### Requirement 4: Emergency Routing Capability

**User Story:** As a patient with a high-severity condition, I want the system to route me to the nearest emergency facility, so that I receive immediate medical attention.

#### Acceptance Criteria

1. WHEN a case is classified as High severity, THE Emergency_Router SHALL query the Google_Maps_API to identify the nearest emergency facility
2. WHEN the Emergency_Router queries for emergency facilities, THE Google_Maps_API SHALL return a list of facilities sorted by distance
3. WHEN emergency facilities are identified, THE Emergency_Router SHALL provide the patient with the facility address, phone number, and estimated travel time
4. WHEN the Emergency_Router provides routing information, THE information SHALL include turn-by-turn directions or a map link
5. WHEN the Emergency_Router completes routing, THE routing information SHALL be delivered within 2 seconds

### Requirement 5: Pharmaceutical Guidance with Drug Interaction Checking

**User Story:** As a patient with a low-severity condition, I want the system to recommend appropriate medications, so that I can manage my condition with confidence.

#### Acceptance Criteria

1. WHEN the Triage_Agent recommends medications for a Low or Medium severity case, THE Pharmaceutical_Advisor SHALL query the RAG_Pipeline for appropriate medications
2. WHEN the Pharmaceutical_Advisor retrieves medication recommendations, THE recommendations SHALL include medication name, dosage, frequency, and duration
3. WHEN the Pharmaceutical_Advisor retrieves medication recommendations, THE recommendations SHALL be filtered to include only over-the-counter or commonly prescribed medications
4. WHEN a patient provides their current medication list, THE Drug_Interaction_Checker SHALL verify that recommended medications do not have harmful interactions
5. WHEN a harmful drug interaction is detected, THE Drug_Interaction_Checker SHALL alert the patient and exclude the conflicting medication from recommendations
6. WHEN the Pharmaceutical_Advisor provides recommendations, THE recommendations SHALL include warnings about side effects and contraindications

### Requirement 6: Severity-Based Routing and Guidance

**User Story:** As a healthcare system, I want to route patients based on severity, so that high-risk cases receive immediate attention while low-risk cases receive appropriate self-care guidance.

#### Acceptance Criteria

1. WHEN a case is classified as High severity, THE System SHALL route the patient to emergency services immediately
2. WHEN a case is classified as Medium severity, THE System SHALL recommend urgent care consultation and provide a list of nearby urgent care facilities
3. WHEN a case is classified as Low severity, THE System SHALL provide self-care instructions and pharmaceutical recommendations
4. WHEN a case is classified as Low severity, THE System SHALL recommend follow-up with a primary care physician if symptoms persist
5. WHEN routing decisions are made, THE System SHALL ensure that High severity cases are never routed to self-care or pharmacy-only pathways

### Requirement 7: Closed-Loop Healthcare Experience

**User Story:** As a patient, I want a complete healthcare experience from symptom assessment to follow-up guidance, so that I feel supported throughout my health concern.

#### Acceptance Criteria

1. WHEN a patient completes the triage process, THE System SHALL provide a summary of the triage decision and recommended actions
2. WHEN a patient receives triage guidance, THE System SHALL offer the option to schedule a follow-up consultation with a healthcare provider
3. WHEN a patient is routed to emergency services, THE System SHALL provide pre-arrival instructions and emergency contact information
4. WHEN a patient receives self-care guidance, THE System SHALL provide educational resources about their condition
5. WHEN a patient completes the triage process, THE System SHALL log the interaction for future reference and outcome tracking

### Requirement 8: Performance Metrics and Monitoring

**User Story:** As a healthcare administrator, I want to monitor system performance, so that I can ensure the triage system maintains high accuracy and responsiveness.

#### Acceptance Criteria

1. WHEN the System processes triage cases, THE System SHALL track the F1_Score of disease predictions against clinical validation data
2. WHEN the System processes triage cases, THE System SHALL track the Task_Success_Rate of triage decisions against clinical outcomes
3. WHEN the System processes triage cases, THE System SHALL track the Triage_Latency from symptom input to triage decision
4. WHEN the System processes triage cases, THE System SHALL track the recall rate for High severity cases to ensure no emergency cases are missed
5. WHEN performance metrics are tracked, THE System SHALL maintain a minimum recall rate of 0.95 for High severity cases
6. WHEN performance metrics are tracked, THE System SHALL maintain a Triage_Latency of less than 3 seconds for 95% of cases

### Requirement 9: Patient Data Privacy and Security

**User Story:** As a patient, I want my health information to be protected, so that my privacy is maintained throughout the triage process.

#### Acceptance Criteria

1. WHEN a patient submits symptom information, THE System SHALL encrypt the data in transit using TLS 1.2 or higher
2. WHEN patient data is stored, THE System SHALL encrypt the data at rest using AES-256 encryption
3. WHEN a patient requests data deletion, THE System SHALL remove all personal health information within 30 days
4. WHEN the System processes patient data, THE System SHALL comply with HIPAA regulations for protected health information
5. WHEN the System logs interactions, THE System SHALL not store personally identifiable information in logs

### Requirement 10: Error Handling and Fallback Mechanisms

**User Story:** As a system operator, I want the system to handle errors gracefully, so that patients receive appropriate guidance even when components fail.

#### Acceptance Criteria

1. IF the ML_Model fails to generate predictions, THEN THE System SHALL fall back to a rule-based triage system
2. IF the Google_Maps_API is unavailable, THEN THE System SHALL provide a list of nearby emergency facilities from a cached database
3. IF the RAG_Pipeline is unavailable, THEN THE System SHALL provide generic pharmaceutical guidance based on the diagnosed condition
4. WHEN an error occurs, THE System SHALL log the error with sufficient detail for debugging
5. WHEN an error occurs, THE System SHALL notify the patient of the issue and provide alternative guidance options
