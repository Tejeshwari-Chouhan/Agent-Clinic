# Implementation Plan: Intelligent Healthcare Triage System

## Overview

This implementation plan breaks down the Healthcare Triage System into discrete, manageable coding tasks organized by architectural layer. The system will be built incrementally, starting with core data models and interfaces, then implementing each component layer, integrating external services, and finally adding comprehensive testing and monitoring. All tasks reference specific requirements and correctness properties from the design document.

## Tasks

- [ ] 1. Set up project structure, dependencies, and core infrastructure
  - Create Python project structure with src/, tests/, config/ directories
  - Set up virtual environment and install dependencies (FastAPI, Pydantic, pytest, hypothesis, etc.)
  - Create base configuration management for API keys, database connections, encryption keys
  - Set up logging infrastructure with PII redaction and HIPAA compliance
  - Create utility modules for encryption (AES-256), hashing, and data validation
  - _Requirements: 9.1, 9.2, 9.5_

- [ ] 2. Implement core data models and validation
  - [ ] 2.1 Create Pydantic models for SymptomInput, ExtractedSymptom, and related types
    - Define SymptomInput with patient_id (encrypted), timestamp, raw_text (encrypted), extracted_symptoms
    - Implement validation for symptom data structure and required fields
    - _Requirements: 1.1, 1.2_

  - [ ]* 2.2 Write property test for symptom input validation
    - **Property 2: Symptom Input Validation**
    - **Validates: Requirements 1.3, 1.4**

  - [ ] 2.3 Create Pydantic models for DiseaseProbabilityVector and related types
    - Define DiseaseProbabilityVector with conditions list, probabilities, confidence intervals, model metadata
    - Implement validation for probability sum (1.0 ± 0.01 tolerance)
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 2.4 Write property test for disease probability vector completeness
    - **Property 3: Disease Probability Vector Completeness and Validity**
    - **Validates: Requirements 2.1, 2.2, 2.3**

  - [ ] 2.5 Create Pydantic models for TriageDecision, PharmaceuticalRecommendation, EmergencyRoutingInfo
    - Define TriageDecision with severity_level, confidence_score, reasoning, recommended_actions
    - Define PharmaceuticalRecommendation with medication details, side effects, contraindications
    - Define EmergencyRoutingInfo with facility details, directions, travel time
    - _Requirements: 3.1, 4.1, 5.1_

  - [ ]* 2.6 Write unit tests for all data models
    - Test model instantiation, validation, serialization/deserialization
    - Test edge cases: empty lists, boundary values, invalid types
    - _Requirements: 2.1, 3.1, 4.1, 5.1_

- [ ] 3. Implement Symptom Processor component
  - [ ] 3.1 Create SymptomProcessor class with NLP-based feature extraction
    - Implement parse_symptoms() method to extract clinical features from raw text
    - Implement normalize_terminology() method for medical term standardization
    - Implement validate_input() method to ensure at least one recognizable symptom
    - _Requirements: 1.1, 1.2, 1.4_

  - [ ] 3.2 Implement clarification and filtering logic
    - Implement request_clarification() method to identify ambiguous/incomplete inputs
    - Implement filter_clinical_content() method to remove non-clinical text
    - _Requirements: 1.3, 1.5_

  - [ ]* 3.3 Write property test for symptom feature extraction and normalization
    - **Property 1: Symptom Feature Extraction and Normalization**
    - **Validates: Requirements 1.1, 1.2, 1.5**

  - [ ]* 3.4 Write unit tests for SymptomProcessor
    - Test extraction with various symptom descriptions
    - Test normalization with medical terminology variations
    - Test clarification request triggering
    - Test non-clinical content filtering
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 4. Implement ML Model integration and Disease Probability prediction
  - [ ] 4.1 Create MLModelInterface and mock implementation for disease probability prediction
    - Implement predict() method that accepts extracted symptoms and returns DiseaseProbabilityVector
    - Implement probability validation to ensure sum equals 1.0 (±0.01 tolerance)
    - Implement condition ranking by probability in descending order
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ] 4.2 Implement latency tracking and performance monitoring
    - Add processing_time_ms tracking to DiseaseProbabilityVector
    - Implement timeout mechanism (500ms max) with fallback trigger
    - Add model performance metrics (F1-score, precision, recall)
    - _Requirements: 2.4, 2.5_

  - [ ]* 4.3 Write property test for ML model latency performance
    - **Property 4: ML Model Latency Performance**
    - **Validates: Requirements 2.4**

  - [ ]* 4.4 Write unit tests for ML model integration
    - Test prediction with various symptom combinations
    - Test probability sum validation
    - Test condition ranking
    - Test latency measurement and timeout
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 5. Implement Triage Agent (LLM-based decision-making)
  - [ ] 5.1 Create TriageAgent class with severity classification logic
    - Implement classify_severity() method using LLM to classify High/Medium/Low severity
    - Implement severity thresholds: High (prob > 0.7 + high-risk), Medium (0.4-0.7), Low (< 0.4)
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

  - [ ] 5.2 Implement confidence scoring and reasoning generation
    - Implement generate_confidence_score() method (0-1 range)
    - Implement explain_reasoning() method to provide decision justification
    - _Requirements: 3.5, 3.6_

  - [ ] 5.3 Implement action orchestration based on severity
    - Implement orchestrate_actions() method to determine downstream actions
    - Ensure High severity triggers emergency routing, Medium triggers urgent care, Low triggers self-care
    - _Requirements: 3.2, 3.3, 3.4, 6.1, 6.2, 6.3_

  - [ ]* 5.4 Write property test for severity classification completeness
    - **Property 5: Severity Classification Completeness**
    - **Validates: Requirements 3.1, 3.5, 3.6**

  - [ ]* 5.5 Write property test for severity-based action orchestration
    - **Property 6: Severity-Based Action Orchestration**
    - **Validates: Requirements 3.2, 3.3, 3.4, 6.1, 6.2, 6.3**

  - [ ]* 5.6 Write property test for high severity routing invariant
    - **Property 7: High Severity Routing Invariant**
    - **Validates: Requirements 6.5**

  - [ ]* 5.7 Write unit tests for TriageAgent
    - Test severity classification with various probability vectors
    - Test confidence score generation
    - Test reasoning explanation
    - Test action orchestration for each severity level
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 6.1, 6.2, 6.3, 6.5_

- [ ] 6. Implement Emergency Router component
  - [ ] 6.1 Create EmergencyRouter class with Google Maps API integration
    - Implement find_nearest_facility() method to query Google Maps API
    - Implement get_directions() method to retrieve turn-by-turn directions
    - Implement facility sorting by distance
    - _Requirements: 4.1, 4.2, 4.3, 4.4_

  - [ ] 6.2 Implement latency tracking and timeout handling
    - Add 2-second timeout for API calls
    - Implement api_response_time_ms tracking
    - Trigger fallback mechanism on timeout or API failure
    - _Requirements: 4.5_

  - [ ] 6.3 Implement cached facility database fallback
    - Create facility cache with geographic indexing
    - Implement fallback_to_cache() method for API failures
    - Ensure cache is updated daily with fresh facility data
    - _Requirements: 10.2_

  - [ ]* 6.4 Write property test for emergency routing completeness and latency
    - **Property 8: Emergency Routing Completeness and Latency**
    - **Validates: Requirements 4.1, 4.2, 4.3, 4.4, 4.5**

  - [ ]* 6.5 Write property test for Google Maps API fallback mechanism
    - **Property 19: Google Maps API Fallback Mechanism**
    - **Validates: Requirements 10.2**

  - [ ]* 6.6 Write unit tests for EmergencyRouter
    - Test API query execution with mock responses
    - Test facility sorting by distance
    - Test information completeness (address, phone, travel time, directions)
    - Test latency measurement and timeout
    - Test fallback to cache on API failure
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 10.2_

- [ ] 7. Implement Pharmaceutical Advisor component
  - [ ] 7.1 Create PharmaceuticalAdvisor class with RAG pipeline integration
    - Implement query_rag_pipeline() method to retrieve medication recommendations
    - Implement filter_medications() method to include only OTC and commonly prescribed medications
    - Ensure recommendations include medication name, dosage, frequency, duration
    - _Requirements: 5.1, 5.2, 5.3, 5.6_

  - [ ] 7.2 Implement side effects and contraindications retrieval
    - Add side_effects and contraindications fields to recommendations
    - Retrieve from RAG pipeline or knowledge base
    - _Requirements: 5.6_

  - [ ]* 7.3 Write property test for pharmaceutical recommendation completeness
    - **Property 9: Pharmaceutical Recommendation Completeness**
    - **Validates: Requirements 5.1, 5.2, 5.3, 5.6**

  - [ ]* 7.4 Write property test for RAG pipeline fallback mechanism
    - **Property 20: RAG Pipeline Fallback Mechanism**
    - **Validates: Requirements 10.3**

  - [ ]* 7.5 Write unit tests for PharmaceuticalAdvisor
    - Test RAG pipeline query with various conditions
    - Test medication filtering (OTC vs prescription)
    - Test completeness of recommendations
    - Test fallback to generic guidance on pipeline failure
    - _Requirements: 5.1, 5.2, 5.3, 5.6, 10.3_

- [ ] 8. Implement Drug Interaction Checker component
  - [ ] 8.1 Create DrugInteractionChecker class with interaction database
    - Implement check_interactions() method to validate recommended medications against current medications
    - Implement interaction detection logic using interaction database
    - _Requirements: 5.4, 5.5_

  - [ ] 8.2 Implement conflict alerting and medication exclusion
    - Implement alert_patient() method to notify of detected conflicts
    - Implement exclude_conflicting_medications() method to remove conflicting drugs from recommendations
    - _Requirements: 5.4, 5.5_

  - [ ]* 8.3 Write property test for drug interaction detection and exclusion
    - **Property 10: Drug Interaction Detection and Exclusion**
    - **Validates: Requirements 5.4, 5.5**

  - [ ]* 8.4 Write unit tests for DrugInteractionChecker
    - Test interaction detection with known drug pairs
    - Test conflict alerting
    - Test medication exclusion from recommendations
    - Test edge cases: empty medication lists, unknown drugs
    - _Requirements: 5.4, 5.5_

- [ ] 9. Implement Triage Orchestrator (main orchestration layer)
  - [ ] 9.1 Create TriageOrchestrator class to coordinate all components
    - Implement process_triage_request() method to orchestrate end-to-end flow
    - Coordinate SymptomProcessor → MLModel → TriageAgent → Routing/Pharma
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1_

  - [ ] 9.2 Implement request routing and state management
    - Implement state machine for triage workflow (input → processing → decision → actions)
    - Implement request tracking and session management
    - _Requirements: 1.1, 3.1_

  - [ ] 9.3 Implement closed-loop experience features
    - Implement follow-up scheduling options
    - Implement interaction logging for outcome tracking
    - _Requirements: 7.1, 7.2, 7.5_

  - [ ]* 9.4 Write property test for closed-loop experience completeness
    - **Property 11: Closed-Loop Experience Completeness**
    - **Validates: Requirements 7.1, 7.2, 7.5**

  - [ ]* 9.5 Write unit tests for TriageOrchestrator
    - Test end-to-end triage workflow
    - Test state transitions
    - Test request tracking
    - Test follow-up scheduling
    - Test interaction logging
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 7.2, 7.5_

- [ ] 10. Implement guidance and follow-up components
  - [ ] 10.1 Create GuidanceGenerator class for emergency pre-arrival instructions
    - Implement generate_emergency_guidance() method for High severity cases
    - Include pre-arrival instructions and emergency contact information
    - _Requirements: 7.3_

  - [ ] 10.2 Create EducationalResourceProvider for self-care guidance
    - Implement get_educational_resources() method for Low severity cases
    - Implement recommend_follow_up() method for physician follow-up
    - _Requirements: 6.4, 7.4_

  - [ ]* 10.3 Write property test for emergency pre-arrival guidance
    - **Property 12: Emergency Pre-Arrival Guidance**
    - **Validates: Requirements 7.3**

  - [ ]* 10.4 Write property test for self-care educational resources
    - **Property 13: Self-Care Educational Resources**
    - **Validates: Requirements 6.4, 7.4**

  - [ ]* 10.5 Write unit tests for guidance components
    - Test emergency guidance generation
    - Test educational resource retrieval
    - Test follow-up recommendation generation
    - _Requirements: 6.4, 7.3, 7.4_

- [ ] 11. Implement error handling and fallback mechanisms
  - [ ] 11.1 Create ErrorHandler class with graceful degradation logic
    - Implement tier-based fallback strategy (Tier 1-4)
    - Implement component failure detection and recovery
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5_

  - [ ] 11.2 Implement ML model fallback to rule-based triage
    - Create RuleBasedTriageEngine for fallback decisions
    - Implement fallback triggering on model failure or timeout
    - _Requirements: 10.1_

  - [ ] 11.3 Implement error logging with PII redaction
    - Implement error logging with component, timestamp, error type, stack trace
    - Ensure no PII in logs (encrypt patient_id, exclude symptom text)
    - _Requirements: 10.4, 10.5, 9.5_

  - [ ] 11.4 Implement patient notification on errors
    - Implement notify_patient_of_error() method
    - Provide alternative guidance options on error
    - _Requirements: 10.5_

  - [ ]* 11.5 Write property test for ML model fallback mechanism
    - **Property 18: ML Model Fallback Mechanism**
    - **Validates: Requirements 10.1**

  - [ ]* 11.6 Write property test for error logging and notification
    - **Property 21: Error Logging and Notification**
    - **Validates: Requirements 10.4, 10.5**

  - [ ]* 11.7 Write unit tests for error handling
    - Test component failure detection
    - Test fallback mechanism activation
    - Test error logging with PII redaction
    - Test patient notification
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 9.5_

- [ ] 12. Implement security and encryption layer
  - [ ] 12.1 Create EncryptionManager for data protection
    - Implement AES-256 encryption for data at rest
    - Implement TLS 1.2+ for data in transit
    - _Requirements: 9.1, 9.2_

  - [ ] 12.2 Implement HIPAA compliance features
    - Implement data deletion on request (30-day compliance)
    - Implement audit logging for PHI access
    - Implement access control and authentication
    - _Requirements: 9.3, 9.4_

  - [ ] 12.3 Implement PII detection and redaction
    - Create PII detector for logs and outputs
    - Implement automatic redaction of sensitive data
    - _Requirements: 9.5_

  - [ ]* 12.4 Write property test for data encryption in transit
    - **Property 14: Data Encryption in Transit**
    - **Validates: Requirements 9.1**

  - [ ]* 12.5 Write property test for data encryption at rest
    - **Property 15: Data Encryption at Rest**
    - **Validates: Requirements 9.2**

  - [ ]* 12.6 Write property test for PII exclusion from logs
    - **Property 17: PII Exclusion from Logs**
    - **Validates: Requirements 9.5**

  - [ ]* 12.7 Write unit tests for security and encryption
    - Test AES-256 encryption/decryption
    - Test TLS configuration
    - Test data deletion compliance
    - Test audit logging
    - Test PII detection and redaction
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 13. Implement monitoring and performance tracking
  - [ ] 13.1 Create MetricsCollector for performance monitoring
    - Implement F1-score tracking for disease predictions
    - Implement Task Success Rate tracking
    - Implement Triage Latency tracking (target: <3 seconds for 95th percentile)
    - _Requirements: 8.1, 8.2, 8.3, 8.6_

  - [ ] 13.2 Implement recall rate monitoring for High severity cases
    - Track recall rate for emergency cases (target: ≥0.95)
    - Implement alerting for recall rate degradation
    - _Requirements: 8.4, 8.5_

  - [ ] 13.3 Create PerformanceMonitor for component-level metrics
    - Monitor latency for each component (symptom processing, ML model, routing, etc.)
    - Implement latency budget tracking
    - _Requirements: 8.3, 8.6_

  - [ ] 13.4 Implement metrics persistence and reporting
    - Store metrics in metrics database
    - Create reporting endpoints for performance dashboards
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 13.5 Write unit tests for monitoring and metrics
    - Test metric collection and calculation
    - Test latency measurement
    - Test recall rate tracking
    - Test metrics persistence
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 14. Implement data persistence layer
  - [ ] 14.1 Create database models and ORM setup
    - Define database schema for patient data, triage decisions, audit logs
    - Set up SQLAlchemy ORM with encrypted fields
    - _Requirements: 9.2, 9.3, 9.4_

  - [ ] 14.2 Implement patient data storage with encryption
    - Create PatientDataRepository for encrypted data persistence
    - Implement encryption/decryption on read/write
    - _Requirements: 9.2_

  - [ ] 14.3 Implement audit logging for HIPAA compliance
    - Create AuditLogRepository for access tracking
    - Log all PHI access with timestamp, user, action
    - _Requirements: 9.4_

  - [ ] 14.4 Implement data deletion and retention policies
    - Implement delete_patient_data() method with 30-day compliance
    - Implement retention policies for different data types
    - _Requirements: 9.3_

  - [ ]* 14.5 Write property test for data deletion compliance
    - **Property 16: Data Deletion Compliance**
    - **Validates: Requirements 9.3**

  - [ ]* 14.6 Write unit tests for data persistence
    - Test data storage and retrieval
    - Test encryption/decryption
    - Test audit logging
    - Test data deletion
    - _Requirements: 9.2, 9.3, 9.4_

- [ ] 15. Implement caching layer for performance optimization
  - [ ] 15.1 Create CacheManager with multi-level caching strategy
    - Implement symptom terminology cache (LRU, 10K entries)
    - Implement facility location cache (geographic grid, 24-hour TTL)
    - Implement RAG vector embeddings cache (7-day TTL)
    - _Requirements: 8.3, 8.6_

  - [ ] 15.2 Implement cache invalidation and refresh
    - Implement TTL-based cache expiration
    - Implement manual cache refresh for critical data
    - _Requirements: 8.3_

  - [ ]* 15.3 Write unit tests for caching layer
    - Test cache hit/miss scenarios
    - Test TTL expiration
    - Test cache refresh
    - _Requirements: 8.3, 8.6_

- [ ] 16. Implement API endpoints and request handling
  - [ ] 16.1 Create FastAPI application with core endpoints
    - Implement POST /triage endpoint for symptom submission
    - Implement GET /triage/{decision_id} endpoint for decision retrieval
    - Implement POST /clarification endpoint for clarification responses
    - _Requirements: 1.1, 3.1, 7.1_

  - [ ] 16.2 Implement request validation and error handling
    - Add request validation middleware
    - Add error handling middleware with graceful error responses
    - _Requirements: 1.3, 10.4, 10.5_

  - [ ] 16.3 Implement authentication and authorization
    - Add API key authentication
    - Add role-based access control
    - _Requirements: 9.4_

  - [ ]* 16.4 Write unit tests for API endpoints
    - Test triage endpoint with valid/invalid inputs
    - Test decision retrieval
    - Test clarification handling
    - Test error responses
    - _Requirements: 1.1, 3.1, 7.1, 10.4, 10.5_

- [ ] 17. Checkpoint - Ensure all core components and tests pass
  - Run all unit tests and verify passing
  - Run all property-based tests and verify passing
  - Verify no PII in logs
  - Verify encryption is applied correctly
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 18. Implement integration tests for end-to-end workflows
  - [ ] 18.1 Create integration test suite for complete triage workflows
    - Test High severity case: symptom input → emergency routing
    - Test Medium severity case: symptom input → urgent care recommendation
    - Test Low severity case: symptom input → self-care guidance
    - _Requirements: 3.2, 3.3, 3.4, 6.1, 6.2, 6.3_

  - [ ] 18.2 Create integration tests for component interactions
    - Test SymptomProcessor → MLModel → TriageAgent flow
    - Test TriageAgent → EmergencyRouter flow
    - Test TriageAgent → PharmaceuticalAdvisor → DrugInteractionChecker flow
    - _Requirements: 1.1, 2.1, 3.1, 4.1, 5.1_

  - [ ] 18.3 Create integration tests for fallback mechanisms
    - Test ML model failure fallback
    - Test Google Maps API failure fallback
    - Test RAG pipeline failure fallback
    - _Requirements: 10.1, 10.2, 10.3_

  - [ ]* 18.4 Write integration tests for security and privacy
    - Test end-to-end encryption
    - Test HIPAA compliance
    - Test audit logging
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 19. Implement performance optimization and latency tuning
  - [ ] 19.1 Implement parallelization for concurrent processing
    - Parallelize symptom extraction and validation
    - Parallelize ML model and rule-based predictions
    - Parallelize pharmaceutical advisor and interaction checker
    - _Requirements: 8.3, 8.6_

  - [ ] 19.2 Implement async/await for external API calls
    - Convert Google Maps API calls to async
    - Convert RAG pipeline calls to async
    - Implement request pipelining
    - _Requirements: 8.3, 8.6_

  - [ ] 19.3 Implement early response for urgent cases
    - Return emergency routing immediately for High severity
    - Stream results to UI as they become available
    - _Requirements: 8.3, 8.6_

  - [ ] 19.4 Implement model quantization and optimization
    - Quantize ML model (FP32 → INT8) if applicable
    - Optimize token usage for LLM prompts
    - _Requirements: 8.3, 8.6_

  - [ ]* 19.5 Write performance benchmarking tests
    - Benchmark component latencies against targets
    - Benchmark end-to-end latency (target: <3 seconds for 95th percentile)
    - Benchmark throughput (target: >50 decisions/second)
    - _Requirements: 8.3, 8.6_

- [ ] 20. Implement monitoring and alerting system
  - [ ] 20.1 Create AlertingSystem for critical errors and performance degradation
    - Implement alerting for component failures
    - Implement alerting for performance degradation
    - Implement alerting for recall rate degradation
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ] 20.2 Create HealthCheckEndpoint for system status monitoring
    - Implement /health endpoint for component status
    - Implement /metrics endpoint for performance metrics
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ] 20.3 Implement logging aggregation and analysis
    - Set up centralized logging with PII redaction
    - Create log analysis for error patterns
    - _Requirements: 9.5, 10.4_

  - [ ]* 20.4 Write unit tests for monitoring and alerting
    - Test alert triggering on component failure
    - Test alert triggering on performance degradation
    - Test health check endpoint
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

- [ ] 21. Final checkpoint - Ensure all tests pass and system is production-ready
  - Run all unit tests, property-based tests, and integration tests
  - Verify all performance benchmarks are met
  - Verify all security and privacy requirements are met
  - Verify all monitoring and alerting is functional
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP, but are strongly recommended for production quality
- Each task references specific requirements and correctness properties for traceability
- Property-based tests validate universal correctness properties across all valid inputs
- Unit tests validate specific examples and edge cases
- Integration tests validate end-to-end workflows and component interactions
- Checkpoints (tasks 17 and 21) ensure incremental validation and early error detection
- All code must follow Python best practices and include comprehensive docstrings
- All external API calls must include timeout handling and fallback mechanisms
- All patient data must be encrypted at rest and in transit
- All logs must exclude PII and be HIPAA-compliant
