import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Stethoscope, ArrowRight, Shield, Clock, BrainCircuit, HeartPulse, MapPin, Building2, Ambulance, Pill } from 'lucide-react';
import './App.css'; // I will write this next

interface SymptomState {
  age: string;
  state: string;
  city: string;
  text: string;
  isSubmitting: boolean;
  result: any | null;
}

const indianLocations = {
  "Andhra Pradesh": ["Visakhapatnam", "Vijayawada", "Guntur", "Nellore"],
  "Delhi": ["New Delhi", "North Delhi", "South Delhi"],
  "Gujarat": ["Ahmedabad", "Surat", "Vadodara", "Rajkot"],
  "Karnataka": ["Bengaluru", "Mysuru", "Hubballi", "Mangaluru"],
  "Maharashtra": ["Mumbai", "Pune", "Nagpur", "Nashik"],
  "Tamil Nadu": ["Chennai", "Coimbatore", "Madurai", "Tiruchirappalli"],
  "Telangana": ["Hyderabad", "Warangal", "Nizamabad"],
  "Uttar Pradesh": ["Lucknow", "Kanpur", "Ghaziabad", "Agra"],
  "West Bengal": ["Kolkata", "Howrah", "Asansol", "Siliguri"]
};

interface RoutingPath {
  type: 'emergency' | 'non-emergency';
  agents: {
    name: string;
    icon: any;
    description: string;
  }[];
}

function App() {
  const [symptoms, setSymptoms] = useState<SymptomState>({
    age: '',
    state: '',
    city: '',
    text: '',
    isSubmitting: false,
    result: null
  });

  const getRoutingPath = (severityLevel: string): RoutingPath => {
    if (severityLevel !== 'High') {
      return {
        type: 'non-emergency',
        agents: [
          {
            name: 'Clinic Agent',
            icon: Building2,
            description: 'Schedule appointment with primary care physician'
          },
          {
            name: 'Pharmacy Agent',
            icon: Pill,
            description: 'Get over-the-counter medication recommendations'
          }
        ]
      };
    } else {
      return {
        type: 'emergency',
        agents: [
          {
            name: 'Nearby Hospitals',
            icon: MapPin,
            description: 'Find nearest available hospitals'
          },
          {
            name: 'Ambulance',
            icon: Ambulance,
            description: 'Request emergency medical transport'
          }
        ]
      };
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!symptoms.text.trim()) return;

    setSymptoms(prev => ({ ...prev, isSubmitting: true }));

    // Simulate backend call
    setTimeout(() => {
      let severityScore = Math.floor(Math.random() * 10) + 1; // Random score 1-10 for demo
      
      // Look for emergency keywords in the text to guarantee a high severity
      const urgentKeywords = ['severe', 'chest', 'heart', 'bleeding', 'emergency', 'unconscious', 'fainted', 'breath'];
      if (urgentKeywords.some(keyword => symptoms.text.toLowerCase().includes(keyword))) {
        severityScore = Math.floor(Math.random() * 3) + 8; // Guarantee 8, 9, or 10
      }
            let severityLevel = 'Low';
      if (severityScore >= 8) severityLevel = 'High';
      else if (severityScore >= 5) severityLevel = 'Medium';
      
      const routingPath = getRoutingPath(severityLevel);

      setSymptoms(prev => ({
        ...prev,
        isSubmitting: false,
        result: {
          triageLevel: severityLevel === 'High' ? 'Emergency' : 'Non-Emergency',
          severityLevel,
          routingPath,
          recommendation: severityLevel === 'High'
            ? 'Immediate emergency care required. Please proceed to the nearest emergency room.'
            : 'Non-emergency care recommended. Schedule an appointment or visit a pharmacy.',
          patientSummary: `A ${symptoms.age || 'unknown'}-year-old patient from ${symptoms.city || 'unspecified city'}, ${symptoms.state || 'unspecified state'} presenting with the following symptoms: "${symptoms.text}". The AI evaluation indicates a ${severityLevel.toLowerCase()} severity.`
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
            <a href="#about" className="nav-link">About</a>
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
              <div className="patient-info-grid">
                <div className="input-group">
                  <label htmlFor="age">Patient Age</label>
                  <input
                    type="number"
                    id="age"
                    className="input-base"
                    placeholder="e.g. 35"
                    value={symptoms.age}
                    onChange={(e) => setSymptoms(prev => ({ ...prev, age: e.target.value }))}
                    disabled={symptoms.isSubmitting || symptoms.result !== null}
                    min="1"
                    max="120"
                    required
                  />
                </div>
                <div className="input-group">
                  <label htmlFor="state">State</label>
                  <select
                    id="state"
                    className="input-base select-base"
                    value={symptoms.state}
                    onChange={(e) => setSymptoms(prev => ({ ...prev, state: e.target.value, city: '' }))}
                    disabled={symptoms.isSubmitting || symptoms.result !== null}
                    required
                  >
                    <option value="" disabled>Select State</option>
                    {Object.keys(indianLocations).map((state) => (
                      <option key={state} value={state}>{state}</option>
                    ))}
                  </select>
                </div>
                <div className="input-group">
                  <label htmlFor="city">City</label>
                  <select
                    id="city"
                    className="input-base select-base"
                    value={symptoms.city}
                    onChange={(e) => setSymptoms(prev => ({ ...prev, city: e.target.value }))}
                    disabled={!symptoms.state || symptoms.isSubmitting || symptoms.result !== null}
                    required
                  >
                    <option value="" disabled>Select City</option>
                    {symptoms.state && indianLocations[symptoms.state as keyof typeof indianLocations].map((city) => (
                      <option key={city} value={city}>{city}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="input-group">
                <label htmlFor="symptoms-text" style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>Symptoms</label>
                <textarea
                  id="symptoms-text"
                  className="input-base textarea"
                  placeholder="E.g., I've had a severe headache and nausea for the past 6 hours. My vision also feels a bit blurry..."
                  value={symptoms.text}
                  onChange={(e) => setSymptoms(prev => ({ ...prev, text: e.target.value }))}
                  rows={5}
                  disabled={symptoms.isSubmitting || symptoms.result !== null}
                  required
                />
              </div>

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
                    <div className="result-badges">
                      <span className={`badge ${symptoms.result.routingPath.type === 'emergency' ? 'badge-emergency' : 'badge-non-emergency'}`}>
                        {symptoms.result.triageLevel}
                      </span>
                      <span className="badge badge-score">
                        Severity: {symptoms.result.severityLevel}
                      </span>
                    </div>
                  </div>

                  <div className="result-body">
                    <p className="recommendation">
                      <strong>Recommendation:</strong> {symptoms.result.recommendation}
                    </p>

                    {/* Routing Path Display */}
                    <div className="routing-path">
                      <h4 className="routing-title">
                        {symptoms.result.routingPath.type === 'emergency' ? '🚨 Emergency Routing Path' : '🏥 Non-Emergency Routing Path'}
                      </h4>
                      <div className="agents-grid">
                        {symptoms.result.routingPath.agents.map((agent: any, idx: number) => {
                          const IconComponent = agent.icon;
                          return (
                            <motion.div
                              key={agent.name}
                              initial={{ opacity: 0, y: 20 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.5, delay: 0.2 + (idx * 0.1) }}
                              className="agent-card"
                            >
                              <div className="agent-icon">
                                <IconComponent size={24} />
                              </div>
                              <h5 className="agent-name">{agent.name}</h5>
                              <p className="agent-description">{agent.description}</p>
                              <button className="btn btn-outline agent-action">
                                Access {agent.name}
                              </button>
                            </motion.div>
                          );
                        })}
                      </div>
                    </div>

                    <div className="conditions-list patient-summary-section">
                      <h4>Patient Summary</h4>
                      <div className="patient-summary-content glass-panel" style={{ padding: '1.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                        <p style={{ lineHeight: '1.6', color: 'var(--text-secondary)' }}>
                          {symptoms.result.patientSummary}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="result-actions">
                    <button
                      className="btn btn-secondary"
                      onClick={() => setSymptoms(prev => ({ ...prev, text: '', isSubmitting: false, result: null }))}
                    >
                      Start Over
                    </button>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </section>

        {/* About Section */}
        <section id="about" className="about-section">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="about-container glass-panel"
          >
            <h2>About Agent<span className="text-gradient">Clinic</span></h2>
            <p className="about-text">
              AgentClinic is an advanced healthcare triage application designed to provide instant, AI-powered preliminary assessments. Our system leverages state-of-the-art Large Language Models to analyze your symptoms and intelligently route you to the appropriate care pathway.
            </p>
            <div className="stats-container grid-cols-3">
              <div className="stat-card">
                <h3 className="text-gradient">24/7</h3>
                <p>Availability</p>
              </div>
              <div className="stat-card">
                <h3 className="text-gradient">Instant</h3>
                <p>Assessment</p>
              </div>
              <div className="stat-card">
                <h3 className="text-gradient">Smart</h3>
                <p>Routing</p>
              </div>
            </div>
          </motion.div>
        </section>
      </main>
    </div>
  );
}

export default App;
