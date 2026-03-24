# Healthcare Triage System - Design Document

## Overview

The Intelligent Healthcare Triage System is a multi-layered architecture that synthesizes natural language processing, machine learning, and large language models to provide rapid, accurate triage decisions. The system processes patient symptom descriptions through a symptom processor, generates disease probability predictions via an ML model, and orchestrates appropriate clinical actions through an LLM-based triage agent.

The design prioritizes:
- **Latency**: Sub-3-second end-to-end triage decisions (95th percentile)
- **Accuracy**: F1-score ≥ 0.75 for disease prediction, 0.95+ recall for emergency cases
- **Reliability**: Graceful degradation with fallback mechanisms for component failures
- **Privacy**: HIPAA-compliant data handling with end-to-end encryption
- **User Experience**: Closed-loop interactions from symptom assessment through follow-up guidance

## Architecture

### High-Level System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                     Patient Interface Layer                      │
│  (Web/Mobile UI - Symptom Input, Results Display, Follow-up)    │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                  Orchestration Layer                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Triage Orchestrator (Request Router & State Manager)    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼──────────┐
│ Processing   │  │ Prediction  │  │ Decision       │
│ Layer        │  │ Layer       │  │ Layer          │
├──────────────┤  ├─────────────┤  ├────────────────┤
│ Symptom      │  │ ML Model    │  │ Triage Agent   │
│ Processor    │  │ (Disease    │  │ (LLM-based)    │
│              │  │ Probability)│  │                │
│ NLP Engine   │  │             │  │ Severity       │
│ (Extraction, │  │ Validation  │  │ Classifier     │
│ Normalization)  │ & Ranking   │  │                │
└──────────────┘  └─────────────┘  └────────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼──────┐  ┌──────▼──────┐  ┌─────▼──────────┐
│ Routing      │  │ Pharma      │  │ Integration    │
│ Layer        │  │ Layer       │  │ Layer          │
├──────────────┤  ├─────────────┤  ├────────────────┤
│ Emergency    │  │ Pharma      │  │ Google Maps    │
│ Router       │  │ Advisor     │  │ API            │
│              │  │             │  │                │
│ Urgent Care  │  │ Drug        │  │ RAG Pipeline   │
│ Router       │  │ Interaction │  │                │
│              │  │ Checker     │  │ Monitoring &   │
│ Self-Care    │  │             │  │ Logging        │
│ Guidance     │  │ Warnings &  │  │                │
│              │  │ Contraind.  │  │ Error Handler  │
└──────────────┘  └─────────────┘  └────────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                  Data & Storage Layer                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Encrypted Patient Data Store (AES-256 at rest, TLS in   │   │
│  │ transit), Audit Logs, Metrics Database, Cache Layer     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

**Symptom Processor**
- Parses natural language symptom input
- Extracts clinical features using NLP
- Normalizes medical terminology
- Validates input completeness
- Filters non-clinical content
- Requests clarification when needed

**ML Model (Disease Probability)**
- Accepts extracted symptom features
- Generates disease probability vector
- Ensures probabilities sum to 1.0 (±0.01 tolerance)
- Ranks conditions by probability
- Completes predictions within 500ms
- Maintains F1-score ≥ 0.75

**Triage Agent (LLM-based)**
- Interprets disease probability vectors
- Classifies severity (High/Medium/Low)
- Generates confidence scores (0-1)
- Provides reasoning explanations
- Orchestrates downstream actions
- Handles edge cases and ambiguities

**Emergency Router**
- Queries Google Maps API for nearest facilities
- Provides address, phone, travel time
- Generates turn-by-turn directions
- Completes routing within 2 seconds
- Falls back to cached facility database on API failure

**Pharmaceutical Advisor**
- Queries RAG pipeline for medication recommendations
- Filters to OTC and commonly prescribed medications
- Includes dosage, frequency, duration
- Provides side effect warnings
- Coordinates with drug interaction checker

**Drug Interaction Checker**
- Validates recommended medications against patient's current medications
- Detects harmful interactions
- Alerts patient to conflicts
- Excludes conflicting medications
- Maintains interaction database

**Monitoring & Logging**
- Tracks F1-score, Task Success Rate, Triage Latency
- Monitors recall rate for High severity cases (target: ≥0.95)
- Logs interactions for outcome tracking
- Maintains HIPAA-compliant audit logs
- Excludes PII from logs

## Data Models and Information Flow

### Core Data Models

**SymptomInput**
```
{
  patient_id: UUID (encrypted)
  timestamp: ISO8601
  raw_text: String (encrypted)
  extracted_symptoms: [
    {
      symptom_name: String (normalized)
      severity: "mild" | "moderate" | "severe"
      duration: String (e.g., "3 days")
      onset: String (e.g., "sudden" | "gradual")
      associated_factors: [String]
    }
  ]
  clarification_needed: Boolean
  clarification_questions: [String]
}
```

**DiseaseProbabilityVector**
```
{
  prediction_id: UUID
  timestamp: ISO8601
  model_version: String
  conditions: [
    {
      condition_name: String
      probability: Float (0.0 - 1.0)
      confidence_interval: {
        lower: Float
        upper: Float
      }
      rank: Integer
    }
  ]
  sum_check: Float (should be ~1.0)
  processing_time_ms: Integer
  model_performance: {
    f1_score: Float
    precision: Float
    recall: Float
  }
}
```

**TriageDecision**
```
{
  decision_id: UUID
  timestamp: ISO8601
  severity_level: "High" | "Medium" | "Low"
  confidence_score: Float (0.0 - 1.0)
  reasoning: String
  recommended_actions: [
    {
      action_type: "emergency_routing" | "urgent_care" | "self_care" | "pharmacy"
      details: Object
      priority: Integer
    }
  ]
  pharmaceutical_recommendations: [PharmaceuticalRecommendation]
  follow_up_guidance: String
  patient_summary: String
}
```

**PharmaceuticalRecommendation**
```
{
  medication_id: UUID
  medication_name: String
  dosage: String
  frequency: String
  duration: String
  indication: String
  side_effects: [String]
  contraindications: [String]
  drug_interactions_checked: Boolean
  interaction_warnings: [String]
  rag_source: String (reference to knowledge base)
}
```

**EmergencyRoutingInfo**
```
{
  routing_id: UUID
  nearest_facility: {
    name: String
    address: String
    phone: String
    distance_km: Float
    estimated_travel_time_min: Integer
    directions_url: String
    turn_by_turn: [String]
  }
  alternative_facilities: [
    {
      name: String
      address: String
      distance_km: Float
      estimated_travel_time_min: Integer
    }
  ]
  pre_arrival_instructions: String
  emergency_contact_info: String
  api_response_time_ms: Integer
}
```

### Information Flow Diagram

```
Patient Input
    │
    ▼
┌─────────────────────────┐
│ Symptom Processor       │
│ - Parse NLP             │
│ - Extract Features      │
│ - Normalize Terms       │
│ - Validate Input        │
└────────────┬────────────┘
             │
             ▼
    ┌────────────────────┐
    │ Clarification      │
    │ Needed?            │
    └────┬───────────┬───┘
         │ Yes       │ No
         │           │
    ┌────▼──┐    ┌───▼──────────────────┐
    │ Ask    │    │ ML Model             │
    │ Patient│    │ - Generate Probs     │
    │        │    │ - Rank Conditions    │
    └────┬───┘    │ - Validate Sum       │
         │        └────────┬─────────────┘
         │                 │
         └─────────┬───────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Triage Agent (LLM)    │
        │ - Classify Severity  │
        │ - Generate Confidence│
        │ - Explain Reasoning  │
        └────────┬─────────────┘
                 │
        ┌────────┴────────┬──────────────┐
        │                 │              │
    ┌───▼────┐      ┌─────▼────┐   ┌────▼─────┐
    │ High   │      │ Medium   │   │ Low      │
    │ Severity       │ Severity │   │ Severity │
    └───┬────┘      └─────┬────┘   └────┬─────┘
        │                 │             │
    ┌───▼──────────┐  ┌───▼──────┐  ┌──▼──────────┐
    │ Emergency    │  │ Urgent   │  │ Self-Care  │
    │ Router       │  │ Care     │  │ Guidance   │
    │ - Maps API   │  │ Router   │  │ + Pharma   │
    │ - Directions │  │ - Nearby │  │ Advisor    │
    └───┬──────────┘  │ Facilities   │ - Drug    │
        │             └───┬──────┘   │ Interaction
        │                 │         │ Check     │
        │                 │         └──┬────────┘
        │                 │            │
        └─────────────────┼────────────┘
                          │
                          ▼
                ┌──────────────────────┐
                │ Triage Result        │
                │ - Decision Summary   │
                │ - Actions            │
                │ - Follow-up Guidance │
                │ - Educational Res.   │
                └──────────────────────┘
                          │
                          ▼
                    Patient Display
```

## Components and Interfaces

### Symptom Processor Interface

```
Input: SymptomInput (raw_text)
Output: SymptomInput (with extracted_symptoms, clarification_needed)

Methods:
- parse_symptoms(raw_text: String) -> [ExtractedSymptom]
- normalize_terminology(symptom: String) -> String
- validate_input(symptoms: [ExtractedSymptom]) -> ValidationResult
- request_clarification(symptoms: [ExtractedSymptom]) -> [String]
- filter_clinical_content(text: String) -> String
```

### ML Model Interface

```
Input: [ExtractedSymptom]
Output: DiseaseProbabilityVector

Methods:
- predict(symptoms: [ExtractedSymptom]) -> DiseaseProbabilityVector
- validate_probabilities(vector: DiseaseProbabilityVector) -> Boolean
- rank_conditions(vector: DiseaseProbabilityVector) -> [RankedCondition]
- get_model_performance() -> ModelPerformanceMetrics
```

### Triage Agent Interface

```
Input: DiseaseProbabilityVector, PatientContext
Output: TriageDecision

Methods:
- classify_severity(probabilities: DiseaseProbabilityVector) -> SeverityLevel
- generate_confidence_score(probabilities: DiseaseProbabilityVector) -> Float
- explain_reasoning(decision: TriageDecision) -> String
- orchestrate_actions(severity: SeverityLevel) -> [Action]
```

### Emergency Router Interface

```
Input: PatientLocation
Output: EmergencyRoutingInfo

Methods:
- find_nearest_facility(location: Coordinates) -> Facility
- get_directions(from: Coordinates, to: Facility) -> DirectionsInfo
- fallback_to_cache(location: Coordinates) -> [Facility]
```

### Pharmaceutical Advisor Interface

```
Input: TriageDecision, PatientMedications
Output: [PharmaceuticalRecommendation]

Methods:
- query_rag_pipeline(condition: String) -> [MedicationOption]
- filter_medications(options: [MedicationOption]) -> [PharmaceuticalRecommendation]
- check_interactions(recommendations: [PharmaceuticalRecommendation], 
                     current_meds: [Medication]) -> InteractionReport
```

## Integration Points

### Google Maps API Integration

**Purpose**: Locate nearest emergency facilities and provide routing information

**Integration Pattern**:
- Async HTTP requests with 2-second timeout
- Fallback to cached facility database on failure
- Caching layer for frequently accessed locations
- Rate limiting to prevent API quota exhaustion

**Error Handling**:
- Network timeout → use cached data
- API rate limit → queue request for retry
- Invalid location → request clarification from patient

### RAG Pipeline Integration

**Purpose**: Retrieve pharmaceutical knowledge and clinical guidelines

**Integration Pattern**:
- Vector similarity search for medication recommendations
- Retrieval of drug interaction data
- Access to clinical guidelines for condition-specific guidance
- Caching of frequently accessed knowledge

**Error Handling**:
- Pipeline unavailable → provide generic guidance based on condition
- No relevant results → escalate to human review
- Outdated knowledge → flag for knowledge base update

### ML Model Integration

**Purpose**: Generate disease probability predictions from symptom features

**Integration Pattern**:
- Batch prediction support for performance
- Model versioning for A/B testing
- Performance monitoring and drift detection
- Fallback to rule-based system on model failure

**Error Handling**:
- Model inference failure → use rule-based triage
- Prediction latency > 500ms → timeout and fallback
- Model performance degradation → alert operations team

## LLM-Based Agent Design

### Agent Architecture

The Triage Agent is an LLM-based system that interprets disease probabilities and makes clinical decisions. It operates in a structured decision-making framework:

**Agent Workflow**:
1. **Input Reception**: Receives disease probability vector and patient context
2. **Severity Classification**: Analyzes top-N conditions and their probabilities to classify severity
3. **Decision Generation**: Generates triage decision with confidence score and reasoning
4. **Action Orchestration**: Determines downstream actions (emergency routing, urgent care, self-care, pharmacy)
5. **Output Formatting**: Structures decision for patient communication

### Severity Classification Logic

```
High Severity (Emergency):
- Any condition with probability > 0.7 AND high-risk classification
- Multiple high-probability conditions indicating complex presentation
- Conditions requiring immediate intervention (e.g., stroke, MI, sepsis)
- Confidence threshold: ≥ 0.85

Medium Severity (Urgent Care):
- Conditions with probability 0.4-0.7 requiring professional evaluation
- Moderate-risk conditions with uncertain diagnosis
- Conditions requiring diagnostic confirmation
- Confidence threshold: ≥ 0.70

Low Severity (Self-Care):
- Conditions with probability < 0.4 or low-risk classification
- Self-limiting conditions with clear management pathways
- Conditions manageable with OTC medications
- Confidence threshold: ≥ 0.60
```

### Decision Logic

The agent uses a multi-factor decision framework:

1. **Probability Analysis**: Top-3 conditions and their probabilities
2. **Risk Stratification**: Clinical risk level of top conditions
3. **Confidence Assessment**: Certainty of prediction based on symptom clarity
4. **Patient Context**: Age, comorbidities, current medications
5. **Clinical Guidelines**: Evidence-based triage protocols

### Prompt Engineering Strategy

The agent uses structured prompts with:
- Clear role definition (clinical triage specialist)
- Explicit decision criteria
- Output format specification (JSON)
- Reasoning requirement
- Confidence score generation
- Fallback instructions for edge cases

## Error Handling and Fallback Mechanisms

### Component Failure Scenarios

**ML Model Failure**
- Trigger: Model inference error or timeout (>500ms)
- Fallback: Rule-based triage system using symptom severity and count
- Recovery: Retry with exponential backoff; alert operations team
- User Impact: Slightly longer latency; reduced accuracy

**Google Maps API Failure**
- Trigger: API unavailable, timeout, or rate limit exceeded
- Fallback: Cached facility database (updated daily)
- Recovery: Queue request for retry; use alternative API if available
- User Impact: May provide slightly outdated facility information

**RAG Pipeline Failure**
- Trigger: Pipeline unavailable or no relevant results
- Fallback: Generic pharmaceutical guidance based on condition
- Recovery: Retry with broader search parameters; escalate to human review
- User Impact: Less personalized medication recommendations

**LLM Agent Failure**
- Trigger: LLM API error, timeout, or invalid response
- Fallback: Deterministic decision tree based on probability vector
- Recovery: Retry with simplified prompt; escalate to human review
- User Impact: Less nuanced reasoning; may miss edge cases

### Graceful Degradation Strategy

The system implements a tiered fallback approach:

```
Tier 1 (Full Functionality):
- All components operational
- Full feature set available
- Optimal latency and accuracy

Tier 2 (Partial Degradation):
- One non-critical component unavailable
- Core triage functionality maintained
- Reduced feature set (e.g., no emergency routing)
- Acceptable latency and accuracy

Tier 3 (Critical Degradation):
- Multiple components unavailable
- Rule-based fallback active
- Basic triage only
- Increased latency; reduced accuracy
- Human escalation recommended

Tier 4 (System Unavailable):
- Critical components failed
- User directed to emergency services
- Offline guidance provided
```

### Error Logging and Monitoring

- All errors logged with context (component, timestamp, user_id hash, error details)
- No PII stored in logs (patient_id encrypted, symptom text excluded)
- Error metrics tracked for alerting (error rate, component health)
- Automatic escalation for critical errors (emergency routing failures)

## Performance Considerations and Latency Optimization

### Latency Budget (Target: <3 seconds for 95th percentile)

```
Component                    Target Latency    Optimization Strategy
─────────────────────────────────────────────────────────────────
Symptom Processing           200ms             - Parallel NLP processing
                                               - Cached terminology database
                                               - Streaming input parsing

ML Model Inference           500ms             - Model quantization
                                               - Batch prediction
                                               - GPU acceleration
                                               - Caching for common symptoms

Triage Agent Decision        400ms             - Prompt caching
                                               - Structured output
                                               - Parallel LLM calls
                                               - Token optimization

Emergency Routing            2000ms            - Parallel API calls
                                               - Location caching
                                               - Facility database indexing

Pharmaceutical Advisor       300ms             - RAG vector caching
                                               - Pre-computed interactions
                                               - Parallel queries

Total End-to-End             ~3400ms           - Async processing
                                               - Request pipelining
                                               - Early response for urgent cases
```

### Optimization Techniques

**Caching Strategy**:
- Symptom terminology cache (LRU, 10K entries)
- Facility location cache (geographic grid, 24-hour TTL)
- RAG vector embeddings cache (semantic similarity, 7-day TTL)
- LLM prompt cache (common decision patterns)

**Parallelization**:
- Symptom extraction and validation in parallel
- Concurrent ML model and rule-based predictions
- Parallel pharmaceutical advisor and interaction checker
- Async external API calls (Maps, RAG)

**Resource Optimization**:
- Model quantization (FP32 → INT8) for ML model
- Token optimization for LLM prompts
- Connection pooling for external APIs
- Memory-efficient data structures

**Early Response**:
- Return emergency routing immediately for High severity
- Stream results to UI as they become available
- Prioritize critical path (severity classification)

## Security and Privacy Implementation

### Data Encryption

**In Transit**:
- TLS 1.2+ for all network communication
- Certificate pinning for external APIs
- Encrypted WebSocket connections for real-time updates

**At Rest**:
- AES-256 encryption for patient data in database
- Encrypted backups with separate key management
- Encrypted cache layers
- Secure key storage (HSM or managed key service)

### HIPAA Compliance

**Protected Health Information (PHI) Handling**:
- Symptom text encrypted and access-controlled
- Patient identifiers encrypted with separate keys
- Audit logs for all PHI access
- Data retention policies (30-day deletion on request)
- Business Associate Agreements with third parties

**Logging and Monitoring**:
- No PHI in application logs
- Patient ID hashed in logs
- Symptom text excluded from logs
- Audit trail for data access
- Automated PII detection and redaction

### Access Control

- Role-based access control (RBAC) for staff
- Multi-factor authentication for admin access
- API key rotation and management
- Principle of least privilege for service accounts

### Data Minimization

- Collect only necessary symptom information
- Discard non-clinical content
- Anonymize data for analytics
- Retention policies for different data types

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection Summary

After analyzing 50 acceptance criteria, 40 were identified as testable properties and 10 as non-testable monitoring/compliance requirements. The following redundancies were identified and consolidated:

- **Symptom Processing Properties**: Consolidated extraction, normalization, and validation into unified properties
- **Severity Routing Properties**: Combined High/Medium/Low severity routing into a single comprehensive property
- **Pharmaceutical Properties**: Merged medication retrieval, filtering, and interaction checking into unified properties
- **Fallback Properties**: Consolidated component-specific fallbacks into a general fallback mechanism property
- **Encryption Properties**: Combined TLS and AES-256 encryption into unified data protection property

### Correctness Properties

### Property 1: Symptom Feature Extraction and Normalization

*For any* natural language symptom input containing recognizable clinical symptoms, the Symptom Processor SHALL extract relevant clinical features and normalize medical terminology consistently such that equivalent symptom descriptions produce equivalent extracted features.

**Validates: Requirements 1.1, 1.2, 1.5**

### Property 2: Symptom Input Validation

*For any* symptom input, the Symptom Processor SHALL validate that the input contains at least one recognizable symptom, and SHALL request clarification when input is ambiguous or incomplete.

**Validates: Requirements 1.3, 1.4**

### Property 3: Disease Probability Vector Completeness and Validity

*For any* set of extracted symptom features provided to the ML Model, the model SHALL generate a Disease_Probability_Vector containing probabilities for all known conditions, with probabilities summing to 1.0 (±0.01 tolerance) and ranked in descending order.

**Validates: Requirements 2.1, 2.2, 2.3**

### Property 4: ML Model Latency Performance

*For any* valid symptom feature set, the ML Model SHALL complete prediction within 500ms to meet latency requirements.

**Validates: Requirements 2.4**

### Property 5: Severity Classification Completeness

*For any* Disease_Probability_Vector, the Triage Agent SHALL classify the case into exactly one valid Severity_Level (High, Medium, or Low) and accompany the decision with a confidence score between 0 and 1 and a brief explanation of reasoning.

**Validates: Requirements 3.1, 3.5, 3.6**

### Property 6: Severity-Based Action Orchestration

*For any* triage decision, the recommended actions SHALL be consistent with the assigned Severity_Level: High severity SHALL trigger emergency routing, Medium severity SHALL recommend urgent care, and Low severity SHALL provide self-care guidance and pharmaceutical recommendations.

**Validates: Requirements 3.2, 3.3, 3.4, 6.1, 6.2, 6.3**

### Property 7: High Severity Routing Invariant

*For any* case classified as High severity, the system SHALL never route the patient to self-care or pharmacy-only pathways; emergency routing SHALL always be included in recommended actions.

**Validates: Requirements 6.5**

### Property 8: Emergency Routing Completeness and Latency

*For any* High severity case, the Emergency Router SHALL query the Google Maps API to identify the nearest emergency facility, return facilities sorted by distance with address, phone number, estimated travel time, and turn-by-turn directions or map link, all within 2 seconds.

**Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

### Property 9: Pharmaceutical Recommendation Completeness

*For any* Low or Medium severity case, the Pharmaceutical Advisor SHALL query the RAG Pipeline and return recommendations that include medication name, dosage, frequency, duration, side effects, and contraindications, filtered to only include over-the-counter or commonly prescribed medications.

**Validates: Requirements 5.1, 5.2, 5.3, 5.6**

### Property 10: Drug Interaction Detection and Exclusion

*For any* set of recommended medications and a patient's current medication list, the Drug Interaction Checker SHALL detect harmful interactions and exclude conflicting medications from final recommendations, alerting the patient to detected conflicts.

**Validates: Requirements 5.4, 5.5**

### Property 11: Closed-Loop Experience Completeness

*For any* completed triage process, the system SHALL provide a summary of the triage decision and recommended actions, offer follow-up scheduling options, and log the interaction for future reference and outcome tracking.

**Validates: Requirements 7.1, 7.2, 7.5**

### Property 12: Emergency Pre-Arrival Guidance

*For any* case routed to emergency services, the system SHALL provide pre-arrival instructions and emergency contact information to the patient.

**Validates: Requirements 7.3**

### Property 13: Self-Care Educational Resources

*For any* case classified as Low severity, the system SHALL provide educational resources about the patient's condition and recommend follow-up with a primary care physician if symptoms persist.

**Validates: Requirements 6.4, 7.4**

### Property 14: Data Encryption in Transit

*For any* patient data transmission, the system SHALL encrypt data in transit using TLS 1.2 or higher.

**Validates: Requirements 9.1**

### Property 15: Data Encryption at Rest

*For any* patient data stored in the system, the data SHALL be encrypted at rest using AES-256 encryption.

**Validates: Requirements 9.2**

### Property 16: Data Deletion Compliance

*For any* patient data deletion request, the system SHALL remove all personal health information within 30 days.

**Validates: Requirements 9.3**

### Property 17: PII Exclusion from Logs

*For any* system interaction logged, the logs SHALL not contain personally identifiable information such as patient names, unencrypted patient IDs, or raw symptom text.

**Validates: Requirements 9.5**

### Property 18: ML Model Fallback Mechanism

*When* the ML Model fails to generate predictions (error or timeout >500ms), the system SHALL fall back to a rule-based triage system that produces a valid Severity_Level classification.

**Validates: Requirements 10.1**

### Property 19: Google Maps API Fallback Mechanism

*When* the Google Maps API is unavailable or times out, the Emergency Router SHALL provide a list of nearby emergency facilities from a cached database with address and distance information.

**Validates: Requirements 10.2**

### Property 20: RAG Pipeline Fallback Mechanism

*When* the RAG Pipeline is unavailable or returns no relevant results, the Pharmaceutical Advisor SHALL provide generic pharmaceutical guidance based on the diagnosed condition.

**Validates: Requirements 10.3**

### Property 21: Error Logging and Notification

*When* an error occurs in any system component, the system SHALL log the error with sufficient detail for debugging (component, timestamp, error type, stack trace) and notify the patient of the issue with alternative guidance options.

**Validates: Requirements 10.4, 10.5**

## Testing Strategy

### Dual Testing Approach

The system requires both unit testing and property-based testing to achieve comprehensive correctness verification:

**Unit Testing** (Specific Examples and Edge Cases):
- Specific symptom inputs with known expected outputs
- Edge cases: empty input, single symptom, multiple symptoms
- Error conditions: malformed input, API failures, timeout scenarios
- Integration points: API mocking, database transactions
- Security: encryption verification, PII detection

**Property-Based Testing** (Universal Properties):
- Symptom processing: random symptom descriptions across symptom types
- Disease prediction: random symptom combinations with probability validation
- Severity classification: random probability vectors with routing verification
- Pharmaceutical recommendations: random conditions with medication validation
- Fallback mechanisms: simulated component failures with recovery verification
- Data protection: random patient data with encryption verification

### Property-Based Testing Configuration

**Testing Framework**: Hypothesis (Python) or fast-check (JavaScript/TypeScript)

**Test Configuration**:
- Minimum 100 iterations per property test
- Seed-based reproducibility for failed cases
- Timeout: 30 seconds per test
- Shrinking enabled for minimal failing examples

**Test Tagging Format**:
```
Feature: healthcare-triage-system, Property {number}: {property_text}
```

**Example Test Tags**:
- `Feature: healthcare-triage-system, Property 1: Symptom Feature Extraction and Normalization`
- `Feature: healthcare-triage-system, Property 3: Disease Probability Vector Completeness and Validity`
- `Feature: healthcare-triage-system, Property 8: Emergency Routing Completeness and Latency`

### Property Test Implementation Guidelines

**Generators** (Input Generation):
- Symptom descriptions: Random combinations of symptom names, severities, durations
- Probability vectors: Random probabilities summing to 1.0 with valid condition names
- Patient medications: Random medication lists with known interaction data
- Locations: Random geographic coordinates within valid ranges
- Error scenarios: Simulated API failures, timeouts, invalid responses

**Assertions** (Property Verification):
- Extracted features are non-empty and clinically relevant
- Probabilities sum to 1.0 (±0.01 tolerance)
- Severity levels are one of {High, Medium, Low}
- Confidence scores are between 0 and 1
- Routing decisions match severity classification
- Latency is within specified bounds
- Encryption is applied to sensitive data
- Fallback mechanisms produce valid outputs

**Shrinking** (Minimal Failing Examples):
- Reduce symptom descriptions to minimal failing case
- Simplify probability vectors to minimal failing configuration
- Reduce medication lists to minimal interaction case

### Unit Test Coverage

**Symptom Processing**:
- Valid symptom extraction
- Medical terminology normalization
- Ambiguous input clarification
- Empty input rejection
- Non-clinical content filtering

**Disease Prediction**:
- Probability vector generation
- Probability sum validation
- Condition ranking
- Latency measurement

**Triage Decision**:
- Severity classification
- Confidence score generation
- Reasoning explanation
- Action orchestration

**Emergency Routing**:
- API query execution
- Facility sorting by distance
- Information completeness
- Latency measurement
- Fallback to cache

**Pharmaceutical Guidance**:
- RAG pipeline query
- Medication filtering
- Drug interaction detection
- Warning inclusion

**Error Handling**:
- ML model failure fallback
- API failure fallback
- Error logging
- Patient notification

**Security**:
- TLS encryption verification
- AES-256 encryption verification
- PII exclusion from logs
- Data deletion compliance

### Performance Testing

**Latency Benchmarks**:
- Symptom processing: <200ms (p95)
- ML model inference: <500ms (p95)
- Triage decision: <400ms (p95)
- Emergency routing: <2000ms (p95)
- End-to-end: <3000ms (p95)

**Load Testing**:
- Concurrent requests: 100+ simultaneous triage requests
- Throughput: >50 triage decisions/second
- Resource utilization: CPU <80%, Memory <85%

**Reliability Testing**:
- Component failure recovery
- Fallback mechanism activation
- Error rate: <0.1% for non-recoverable errors
- Availability: >99.9% uptime

## Appendix: External Dependencies

- **Google Maps API**: Location services, facility routing
- **RAG Pipeline**: Pharmaceutical knowledge, clinical guidelines
- **ML Model**: Disease probability prediction
- **LLM Service**: Triage decision-making and reasoning
- **Database**: Patient data storage and audit logs
- **Cache Layer**: Performance optimization
