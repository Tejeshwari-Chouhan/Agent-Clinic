import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Stethoscope, ArrowRight, Shield, Clock, BrainCircuit, HeartPulse } from 'lucide-react';
import './App.css'; // I will write this next

interface SymptomState {
  text: string;
  isSubmitting: boolean;
  result: any | null;
}

function App() {
  const [symptoms, setSymptoms] = useState<SymptomState>({
    text: '',
    isSubmitting: false,
    result: null
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symptoms.text.trim()) return;
    
    setSymptoms(prev => ({ ...prev, isSubmitting: true }));
    
    // Simulate backend call
    setTimeout(() => {
      setSymptoms(prev => ({ 
        ...prev, 
        isSubmitting: false,
        result: {
          triageLevel: 'Urgent',
          urgencyScore: 8,
          recommendation: 'Please seek evaluation at an urgent care facility or emergency department within the next 2-4 hours. Do not drive yourself if you are feeling dizzy or disoriented.',
          possibleConditions: [
            { name: 'Acute Bronchitis', probability: 0.75 },
            { name: 'Pneumonia', probability: 0.20 },
            { name: 'Upper Respiratory Infection', probability: 0.05 }
          ]
        }
      }));
    }, 2500);
  };

  return (
    <div className="app-layout">
      {/* Navbar */}
      <nav className="navbar glass-panel">
        <div className="container flex-between nav-content">
          <div className="logo flex-center">
            <Activity className="logo-icon" size={28} />
            <span className="logo-text">Agent<span className="text-gradient">Clinic</span></span>
          </div>
          <div className="nav-links">
            <a href="#about" className="nav-link">How it Works</a>
            <a href="#security" className="nav-link">Privacy</a>
            <button className="btn btn-primary btn-sm">Provider Login</button>
          </div>
        </div>
      </nav>

      <main className="main-content container">
        {/* Hero Section */}
        <section className="hero">
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="hero-text"
          >
            <h1>Intelligent AI-Powered <br/><span className="text-gradient">Healthcare Triage</span></h1>
            <p className="hero-subtitle">
              Describe your symptoms naturally. Our advanced medical AI will analyze your condition, provide instant preliminary assessment, and guide you to the right care pathway.
            </p>
          </motion.div>

          <div className="features grid-cols-3">
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="feature-card glass-panel"
            >
              <BrainCircuit className="feature-icon" />
              <h3>AI Assessment</h3>
              <p>State-of-the-art LLMs trained on medical literature analyze your symptoms.</p>
            </motion.div>
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="feature-card glass-panel"
            >
              <Clock className="feature-icon" />
              <h3>Instant Triage</h3>
              <p>Get immediate guidance on whether to visit ER, Urgent Care, or stay home.</p>
            </motion.div>
            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="feature-card glass-panel"
            >
              <Shield className="feature-icon" />
              <h3>HIPAA Compliant</h3>
              <p>Your health data is encrypted and handled with the highest security standards.</p>
            </motion.div>
          </div>
        </section>

        {/* Triage Section */}
        <section className="triage-section">
          <motion.div 
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="triage-container glass-panel"
          >
            <div className="triage-header">
              <Stethoscope size={24} className="triage-header-icon" />
              <h2>Describe Your Symptoms</h2>
            </div>
            
            <form onSubmit={handleSubmit} className="triage-form">
              <textarea 
                className="input-base textarea" 
                placeholder="E.g., I've had a severe headache and nausea for the past 6 hours. My vision also feels a bit blurry..."
                value={symptoms.text}
                onChange={(e) => setSymptoms(prev => ({ ...prev, text: e.target.value }))}
                rows={5}
                disabled={symptoms.isSubmitting || symptoms.result !== null}
              />
              
              {!symptoms.result && (
                <div className="form-actions">
                  <button 
                    type="submit" 
                    className="btn btn-primary submit-btn"
                    disabled={!symptoms.text.trim() || symptoms.isSubmitting}
                  >
                    {symptoms.isSubmitting ? (
                      <span className="flex-center gap-2">
                        <HeartPulse className="spinner" size={20} />
                        Analyzing...
                      </span>
                    ) : (
                      <span className="flex-center gap-2">
                        Assess Symptoms <ArrowRight size={20} />
                      </span>
                    )}
                  </button>
                </div>
              )}
            </form>

            {/* Results Display */}
            <AnimatePresence>
              {symptoms.result && (
                <motion.div 
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="triage-results"
                >
                  <div className="result-header">
                    <h3>Assessment Complete</h3>
                    <span className="badge badge-urgent">Priority: {symptoms.result.triageLevel}</span>
                  </div>
                  
                  <div className="result-body">
                    <p className="recommendation">
                      <strong>Recommendation:</strong> {symptoms.result.recommendation}
                    </p>
                    
                    <div className="conditions-list">
                      <h4>Possible Considerations</h4>
                      <ul>
                        {symptoms.result.possibleConditions.map((cond: any, idx: number) => (
                          <li key={idx} className="condition-item">
                            <span className="condition-name">{cond.name}</span>
                            <div className="probability-bar-bg">
                              <motion.div 
                                initial={{ width: 0 }}
                                animate={{ width: `${cond.probability * 100}%` }}
                                transition={{ duration: 1, delay: 0.5 + (idx * 0.2) }}
                                className="probability-bar-fill" 
                              />
                            </div>
                            <span className="probability-text">{Math.round(cond.probability * 100)}%</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="result-actions">
                    <button className="btn btn-primary" onClick={() => window.location.href='#'}>Find Nearby Care</button>
                    <button 
                      className="btn btn-secondary"
                      onClick={() => setSymptoms({ text: '', isSubmitting: false, result: null })}
                    >
                      Start Over
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </section>
      </main>
    </div>
  );
}

export default App;
