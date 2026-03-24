# Agent-Clinic

Background & Problem Statement:
 In modern healthcare, patients often oscillate between "Googling" symptoms—which leads to unnecessary anxiety—and waiting hours in emergency rooms for non-urgent issues. Current digital health tools are largely passive, relying on static information or simple decision trees that lack nuance and complexity. There is a critical gap for an intelligent intermediary capable of synthesizing natural language, predicting disease probability without human intervention, and taking proactive actions. The core problem is the lack of a system that moves beyond simple prediction to provide a "closed-loop" healthcare experience.
Motivation:
Healthcare providers are currently overwhelmed by administrative triage, leading to burnout and delayed care for high-risk patients. By automating the initial assessment and routing process, we can ensure that high-severity cases receive immediate attention while low-severity cases are handled with appropriate self-care or pharmacy guidance.
Proposed Solution Approach: 
The system follows a Predict-then-Act architecture where a robust machine learning model calculates a probability vector P(D|S) to identify potential conditions, which is then interpreted by an LLM-based agent. Depending on the predicted severity, the agent autonomously triggers specific tools—such as a Google Maps API for emergency routing or a RAG pipeline for pharmaceutical suggestions and drug interaction checks. 
Expected Outcomes 
The system aims to achieve a good F1-score and Task Success Rate(TSR)  in triage accuracy. The final product will focus on reducing triage latency and ensuring high recall for emergency cases, effectively routing patients to the correct care facility based on real-time clinical synthesis.
