import { useState, useEffect, useRef, useCallback, type ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Stethoscope, ArrowRight, Shield, Clock, BrainCircuit, HeartPulse, MapPin, Building2, Ambulance, Pill, LocateFixed } from 'lucide-react';
import { reverseGeocodeClient } from './lib/reverseGeocode';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { Components } from 'react-markdown';
import './App.css'; // I will write this next

const patientSummaryMarkdownComponents: Partial<Components> = {
  a: ({ href, children, ...props }) => (
    <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
      {children}
    </a>
  ),
};

/**
 * Dev: leave unset so requests use `/api/...` on the Vite origin (see vite.config proxy → FastAPI).
 * Production: set VITE_API_BASE_URL to your API origin, e.g. https://api.example.com
 */
const API_BASE = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') ?? '';

type LocationDetectStatus =
  | 'idle'
  | 'detecting'
  | 'ok'
  | 'denied'
  | 'unavailable'
  | 'error'
  | 'skipped';

interface SymptomState {
  age: string;
  state: string;
  city: string;
  text: string;
  isSubmitting: boolean;
  error: string | null;
  result: any | null;
  /** Full line sent to API when browser location + reverse geocode succeed */
  autoLocation: string | null;
  locationStatus: LocationDetectStatus;
  locationDetail: string | null;
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
    panel: 'clinic' | 'pharmacy' | 'hospitals' | 'ambulance';
  }[];
}

function DetailBlock({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="glass-panel" style={{ marginTop: '0.75rem', padding: '1rem', textAlign: 'left', borderRadius: 'var(--radius-md)' }}>
      <h5 style={{ margin: '0 0 0.5rem', color: 'var(--text-primary)' }}>{title}</h5>
      <div style={{ color: 'var(--text-paragraph)', fontSize: '0.95rem', lineHeight: 1.55 }}>{children}</div>
    </div>
  );
}

function App() {
  const [openAgentPanel, setOpenAgentPanel] = useState<RoutingPath['agents'][number]['panel'] | null>(null);

  const [symptoms, setSymptoms] = useState<SymptomState>({
    age: '',
    state: '',
    city: '',
    text: '',
    isSubmitting: false,
    error: null,
    result: null,
    autoLocation: null,
    locationStatus: 'idle',
    locationDetail: null,
  });

  const [locationNonce, setLocationNonce] = useState(0);
  /** Bumps when user skips detection or effect re-runs; stale geolocation callbacks must not update state. */
  const locationDetectGenerationRef = useRef(0);
  const symptomsTextareaRef = useRef<HTMLTextAreaElement>(null);
  const triageSectionRef = useRef<HTMLElement>(null);

  /** After native #triage navigation (or programmatic scroll), move focus to the symptoms field. */
  const scheduleSymptomsFocus = useCallback(() => {
    window.setTimeout(() => {
      const el = symptomsTextareaRef.current;
      if (el && !el.disabled) el.focus({ preventScroll: true });
    }, 500);
  }, []);

  /** Programmatic scroll when a real `<button>` is used (no default hash jump). */
  const scrollTriageIntoView = useCallback(() => {
    const target = triageSectionRef.current ?? document.getElementById('triage');
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    scheduleSymptomsFocus();
  }, [scheduleSymptomsFocus]);

  useEffect(() => {
    const gen = ++locationDetectGenerationRef.current;
    setSymptoms((prev) => ({ ...prev, locationStatus: 'detecting', locationDetail: null }));

    if (!('geolocation' in navigator)) {
      if (gen !== locationDetectGenerationRef.current) return;
      setSymptoms((prev) => ({
        ...prev,
        locationStatus: 'unavailable',
        locationDetail: 'This browser does not support location. Choose state and city below.',
        autoLocation: null,
      }));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        if (gen !== locationDetectGenerationRef.current) return;
        try {
          const line = await reverseGeocodeClient(pos.coords.latitude, pos.coords.longitude);
          if (gen !== locationDetectGenerationRef.current) return;
          setSymptoms((prev) => ({
            ...prev,
            autoLocation: line,
            locationStatus: 'ok',
            locationDetail: null,
          }));
        } catch (e) {
          if (gen !== locationDetectGenerationRef.current) return;
          const msg = e instanceof Error ? e.message : 'Location lookup failed.';
          setSymptoms((prev) => ({
            ...prev,
            autoLocation: null,
            locationStatus: 'error',
            locationDetail: msg,
          }));
        }
      },
      (err) => {
        if (gen !== locationDetectGenerationRef.current) return;
        const denied = err.code === 1;
        setSymptoms((prev) => ({
          ...prev,
          autoLocation: null,
          locationStatus: denied ? 'denied' : 'unavailable',
          locationDetail: denied
            ? 'Location permission denied. You can enter state and city below.'
            : 'Could not read device location. Enter state and city below.',
        }));
      },
      { enableHighAccuracy: false, maximumAge: 300_000, timeout: 15_000 }
    );

    return () => {
      locationDetectGenerationRef.current += 1;
    };
  }, [locationNonce]);

  const hasManualLocation = Boolean(symptoms.state && symptoms.city);
  const locationStillLoading =
    symptoms.locationStatus === 'idle' || symptoms.locationStatus === 'detecting';
  const showManualLocationFields =
    symptoms.locationStatus === 'skipped' ||
    symptoms.locationStatus === 'denied' ||
    symptoms.locationStatus === 'unavailable' ||
    symptoms.locationStatus === 'error';
  /** Manual India fields are required only when that block is shown. Do not block submit while GPS is still resolving. */
  const mustCompleteManualLocation = showManualLocationFields && !hasManualLocation;
  const showLocationStatusRow =
    locationStillLoading || Boolean(symptoms.autoLocation) || Boolean(symptoms.locationDetail);

  const getRoutingPath = (severityLevel: string): RoutingPath => {
    if (severityLevel !== 'High') {
      return {
        type: 'non-emergency',
        agents: [
          {
            name: 'Clinic Agent',
            icon: Building2,
            description: 'Schedule appointment with primary care physician',
            panel: 'clinic',
          },
          {
            name: 'Pharmacy Agent',
            icon: Pill,
            description: 'Get over-the-counter medication recommendations',
            panel: 'pharmacy',
          },
        ]
      };
    } else {
      return {
        type: 'emergency',
        agents: [
          {
            name: 'Nearby Hospitals',
            icon: MapPin,
            description: 'Find nearest available hospitals',
            panel: 'hospitals',
          },
          {
            name: 'Ambulance',
            icon: Ambulance,
            description: 'Request emergency medical transport',
            panel: 'ambulance',
          },
        ]
      };
    }
  };

  const skipAutoLocation = () => {
    locationDetectGenerationRef.current += 1;
    setSymptoms((prev) => ({
      ...prev,
      autoLocation: null,
      locationStatus: 'skipped',
      locationDetail: null,
    }));
  };

  const retryAutoLocation = () => {
    setSymptoms((prev) => ({
      ...prev,
      autoLocation: null,
      locationStatus: 'idle',
      locationDetail: null,
      state: '',
      city: '',
    }));
    setLocationNonce((n) => n + 1);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symptoms.text.trim()) return;
    if (mustCompleteManualLocation) {
      setSymptoms((prev) => ({
        ...prev,
        error: 'Select Indian state and city, or tap “Detect again” / “Enter manually” as needed.',
      }));
      return;
    }

    setSymptoms(prev => ({ ...prev, isSubmitting: true, error: null }));

    const ageNum = parseInt(symptoms.age, 10);
    const patientLocation =
      symptoms.autoLocation?.trim() ||
      (symptoms.state && symptoms.city
        ? [symptoms.city, symptoms.state, 'India'].filter(Boolean).join(', ')
        : undefined);

    try {
      const res = await fetch(`${API_BASE}/api/triage/assess`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          symptoms: symptoms.text,
          patient_age: Number.isFinite(ageNum) ? ageNum : undefined,
          patient_location: patientLocation || undefined,
          mobility_status: 'Mobile',
        }),
      });

      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        const detail = (data as { detail?: string }).detail;
        throw new Error(typeof detail === 'string' ? detail : res.statusText || 'Assessment failed');
      }

      const sev: string = data?.triage_decision?.severity_level ?? 'Medium';
      const routingPath = getRoutingPath(sev);
      const recommendation: string =
        data?.triage_decision?.recommended_action ??
        (sev === 'High'
          ? 'Immediate emergency care required. Use ER locator and ambulance guidance from your clinician or dispatch.'
          : 'Non-emergency care recommended. Use clinic and pharmacy guidance below.');

      const topList = (data?.disease_probabilities ?? [])
        .slice(0, 3)
        .map((x: { condition: string; probability: number }) => `${x.condition} (${(Number(x.probability) * 100).toFixed(1)}%)`)
        .join(', ');

      const facilities =
        sev === 'High' ? (data?.emergency_routing?.er_locator?.facilities ?? []) : [];

      setOpenAgentPanel(null);
      setSymptoms(prev => ({
        ...prev,
        isSubmitting: false,
        result: {
          triageLevel: sev === 'High' ? 'Emergency' : 'Non-Emergency',
          severityLevel: sev,
          severityScore: data?.triage_decision?.severity_score,
          routingPath,
          recommendation,
          patientSummary: data?.patient_summary ?? recommendation,
          topConditions: topList,
          emergencyFacilities: facilities,
          emergencyRouting: data?.emergency_routing ?? null,
          routingGuidance: data?.routing_guidance ?? null,
          clinicGuidance: data?.clinic_guidance ?? null,
          pharmacyGuidance: data?.pharmaceutical_recommendations ?? null,
        },
      }));
    } catch (err: unknown) {
      let message = err instanceof Error ? err.message : 'Could not reach the triage service.';
      if (message === 'Failed to fetch' || message === 'Load failed') {
        message =
          'Could not reach the API. Start the FastAPI backend on port 3000 (from backend/: `python app.py` or `uvicorn app:app --reload --port 3000`), then try again. If it uses another port, set VITE_PROXY_API in frontend/.env (e.g. VITE_PROXY_API=http://127.0.0.1:8000).';
      }
      setSymptoms(prev => ({
        ...prev,
        isSubmitting: false,
        error: message,
        result: null,
      }));
    }
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
            <a href="#triage" className="nav-link" onClick={scheduleSymptomsFocus}>
              Access symptoms
            </a>
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
            <button type="button" className="btn btn-primary" style={{ marginTop: '1.25rem' }} onClick={scrollTriageIntoView}>
              Access symptoms
            </button>
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
        <section id="triage" ref={triageSectionRef} className="triage-section">
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

                {showLocationStatusRow && (
                  <div className="input-group" style={{ gridColumn: '2 / 4' }}>
                    <label>Location</label>
                    {locationStillLoading ? (
                      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem' }}>
                        <span style={{ color: 'var(--text-secondary)' }}>Detecting your approximate area from this device…</span>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={skipAutoLocation}
                          disabled={symptoms.isSubmitting || symptoms.result !== null}
                        >
                          Enter manually
                        </button>
                      </div>
                    ) : symptoms.autoLocation ? (
                      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'flex-start', gap: '0.75rem' }}>
                        <p style={{ margin: 0, flex: '1 1 12rem', color: 'var(--text-paragraph)' }}>
                          <MapPin size={16} style={{ display: 'inline', verticalAlign: 'text-top', marginRight: '0.35rem' }} />
                          <strong style={{ color: 'var(--text-primary)' }}>{symptoms.autoLocation}</strong>
                          <span style={{ display: 'block', fontSize: '0.85rem', marginTop: '0.35rem' }}>
                            Used for nearby care and emergency routing. You can switch to manual state/city if this is wrong.
                          </span>
                        </p>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={skipAutoLocation}
                            disabled={symptoms.isSubmitting || symptoms.result !== null}
                          >
                            Enter manually
                          </button>
                          <button
                            type="button"
                            className="btn btn-secondary btn-sm"
                            onClick={retryAutoLocation}
                            disabled={symptoms.isSubmitting || symptoms.result !== null}
                          >
                            <span className="flex-center gap-1" style={{ justifyContent: 'center' }}>
                              <LocateFixed size={14} /> Detect again
                            </span>
                          </button>
                        </div>
                      </div>
                    ) : symptoms.locationDetail ? (
                      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: '0.75rem' }}>
                        <p style={{ margin: 0, fontSize: '0.9rem', color: 'var(--danger, #f87171)' }}>{symptoms.locationDetail}</p>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={retryAutoLocation}
                          disabled={symptoms.isSubmitting || symptoms.result !== null}
                        >
                          <span className="flex-center gap-1" style={{ justifyContent: 'center' }}>
                            <LocateFixed size={14} /> Try again
                          </span>
                        </button>
                      </div>
                    ) : null}
                  </div>
                )}

                {showManualLocationFields && (
                  <>
                    <div className="input-group">
                      <label htmlFor="state">State (India)</label>
                      <select
                        id="state"
                        className="input-base select-base"
                        value={symptoms.state}
                        onChange={(e) => setSymptoms(prev => ({ ...prev, state: e.target.value, city: '' }))}
                        disabled={symptoms.isSubmitting || symptoms.result !== null}
                        required={!symptoms.autoLocation}
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
                        required={!symptoms.autoLocation}
                      >
                        <option value="" disabled>Select City</option>
                        {symptoms.state && indianLocations[symptoms.state as keyof typeof indianLocations].map((city) => (
                          <option key={city} value={city}>{city}</option>
                        ))}
                      </select>
                    </div>
                  </>
                )}
              </div>

              <div className="input-group">
                <label htmlFor="symptoms-text" style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)' }}>Symptoms</label>
                <textarea
                  ref={symptomsTextareaRef}
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

              {symptoms.error && (
                <p className="recommendation" style={{ color: 'var(--danger, #f87171)', marginBottom: '1rem' }}>
                  <strong>Could not assess:</strong> {symptoms.error}
                </p>
              )}

              {!symptoms.result && (
                <div className="form-actions">
                  <button
                    type="submit"
                    className="btn btn-primary submit-btn"
                    disabled={
                      !symptoms.text.trim() ||
                      symptoms.isSubmitting ||
                      !symptoms.age.trim() ||
                      mustCompleteManualLocation
                    }
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
                        {symptoms.result.severityScore != null ? ` (${symptoms.result.severityScore})` : ''}
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
                        {symptoms.result.routingPath.agents.map((agent: RoutingPath['agents'][number], idx: number) => {
                          const IconComponent = agent.icon;
                          const panel = agent.panel;
                          const isOpen = openAgentPanel === panel;
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
                              <button
                                type="button"
                                className="btn btn-outline agent-action"
                                onClick={() => setOpenAgentPanel(isOpen ? null : panel)}
                              >
                                {isOpen ? 'Hide details' : 'View details'}
                              </button>
                            </motion.div>
                          );
                        })}
                      </div>
                    </div>

                    {openAgentPanel === 'clinic' && (
                      <DetailBlock title="Clinic Agent — care navigation">
                        {!symptoms.result.clinicGuidance ? (
                          <p>No clinic details were returned for this assessment.</p>
                        ) : (
                          <>
                        <p><strong>Pathway:</strong> {String(symptoms.result.clinicGuidance.clinic_pathway ?? '—')}</p>
                        {symptoms.result.clinicGuidance.rationale && (
                          <p style={{ marginTop: '0.5rem' }}>{String(symptoms.result.clinicGuidance.rationale)}</p>
                        )}
                        {symptoms.result.clinicGuidance.timing_guidance && (
                          <p style={{ marginTop: '0.5rem' }}><strong>Timing:</strong> {String(symptoms.result.clinicGuidance.timing_guidance)}</p>
                        )}
                        {Array.isArray(symptoms.result.clinicGuidance.preparation_steps) && symptoms.result.clinicGuidance.preparation_steps.length > 0 && (
                          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.25rem' }}>
                            {symptoms.result.clinicGuidance.preparation_steps.map((s: string) => (
                              <li key={s}>{s}</li>
                            ))}
                          </ul>
                        )}
                        {Array.isArray(symptoms.result.clinicGuidance.what_to_bring) && symptoms.result.clinicGuidance.what_to_bring.length > 0 && (
                          <p style={{ marginTop: '0.5rem' }}><strong>Bring:</strong> {symptoms.result.clinicGuidance.what_to_bring.join(', ')}</p>
                        )}
                        {symptoms.result.clinicGuidance.nearby_hospitals?.facilities?.length > 0 && (
                          <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
                            <p style={{ margin: '0 0 0.35rem' }}>
                              <strong>Nearby hospitals</strong> (for your city — verify before visiting)
                            </p>
                            <p style={{ fontSize: '0.85rem', color: 'var(--text-paragraph)', marginBottom: '0.5rem' }}>
                              {symptoms.result.clinicGuidance.nearby_hospitals.message}
                              {symptoms.result.clinicGuidance.nearby_hospitals.routing_source === 'llm' && (
                                <span> · Source: AI</span>
                              )}
                              {(symptoms.result.clinicGuidance.nearby_hospitals.routing_source === 'live' ||
                                symptoms.result.clinicGuidance.nearby_hospitals.routing_source === 'maps_places') && (
                                <span> · Source: Google Places</span>
                              )}
                            </p>
                            <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'var(--text-paragraph)', lineHeight: 1.6 }}>
                              {symptoms.result.clinicGuidance.nearby_hospitals.facilities.map(
                                (f: {
                                  facility_name: string;
                                  address?: string;
                                  phone?: string;
                                  directions_url?: string;
                                  notes?: string;
                                }) => (
                                  <li key={f.facility_name + (f.address ?? '')}>
                                    <strong>{f.facility_name}</strong>
                                    {f.address ? ` — ${f.address}` : ''}
                                    {f.phone ? ` — ${f.phone}` : ''}
                                    {f.notes ? (
                                      <span style={{ display: 'block', fontSize: '0.85rem', marginTop: '0.2rem' }}>{f.notes}</span>
                                    ) : null}
                                    {f.directions_url ? (
                                      <>
                                        {' '}
                                        <a href={f.directions_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>
                                          Directions
                                        </a>
                                      </>
                                    ) : null}
                                  </li>
                                )
                              )}
                            </ul>
                          </div>
                        )}
                          </>
                        )}
                      </DetailBlock>
                    )}

                    {openAgentPanel === 'pharmacy' && (
                      <DetailBlock title="Pharmacy Agent — medication guidance (informational only)">
                        {!symptoms.result.pharmacyGuidance ? (
                          <p>No pharmacy details were returned.</p>
                        ) : (
                          <>
                        {Array.isArray(symptoms.result.pharmacyGuidance.warnings) && symptoms.result.pharmacyGuidance.warnings.length > 0 && (
                          <ul style={{ margin: '0 0 0.5rem', paddingLeft: '1.25rem' }}>
                            {symptoms.result.pharmacyGuidance.warnings.map((w: string) => (
                              <li key={w}>{w}</li>
                            ))}
                          </ul>
                        )}
                        {Array.isArray(symptoms.result.pharmacyGuidance.recommendations) &&
                          symptoms.result.pharmacyGuidance.recommendations.map(
                            (r: { medication_name?: string; dosage?: string; frequency?: string; duration?: string; side_effects?: string[] }, i: number) => (
                              <div key={i} style={{ marginTop: '0.75rem', borderTop: '1px solid var(--border-color)', paddingTop: '0.75rem' }}>
                                <strong>{r.medication_name ?? 'Medication'}</strong>
                                {r.dosage && <span> — {r.dosage}</span>}
                                {r.frequency && <span>, {r.frequency}</span>}
                                {r.duration && <span>, {r.duration}</span>}
                                {Array.isArray(r.side_effects) && r.side_effects.length > 0 && (
                                  <p style={{ margin: '0.35rem 0 0', fontSize: '0.9rem' }}>Side effects: {r.side_effects.join(', ')}</p>
                                )}
                              </div>
                            )
                          )}
                        {Array.isArray(symptoms.result.pharmacyGuidance.otc_alternatives) && symptoms.result.pharmacyGuidance.otc_alternatives.length > 0 && (
                          <p style={{ marginTop: '0.75rem' }}><strong>OTC alternatives:</strong> {symptoms.result.pharmacyGuidance.otc_alternatives.join(', ')}</p>
                        )}
                          </>
                        )}
                      </DetailBlock>
                    )}

                    {openAgentPanel === 'hospitals' && (
                      <DetailBlock title="Nearby Hospitals — emergency facilities">
                        {symptoms.result.emergencyRouting?.emergency_instruction && (
                          <p>{String(symptoms.result.emergencyRouting.emergency_instruction)}</p>
                        )}
                        {symptoms.result.emergencyRouting?.routing_source === 'llm' && (
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-paragraph)', marginTop: '0.35rem' }}>
                            Source: AI-suggested major hospitals — verify phone and address before calling or traveling.
                          </p>
                        )}
                        {(symptoms.result.emergencyRouting?.routing_source === 'maps_places' ||
                          symptoms.result.emergencyRouting?.routing_source === 'live') && (
                          <p style={{ fontSize: '0.85rem', color: 'var(--text-paragraph)', marginTop: '0.35rem' }}>
                            Source: Google Places
                          </p>
                        )}
                        {symptoms.result.emergencyFacilities?.length > 0 ? (
                          <ul style={{ margin: '0.5rem 0 0', paddingLeft: '1.25rem' }}>
                            {symptoms.result.emergencyFacilities.map(
                              (f: {
                                facility_name: string;
                                address?: string;
                                phone?: string;
                                directions_url?: string;
                                notes?: string;
                              }) => (
                                <li key={f.facility_name + (f.address ?? '')}>
                                  <strong>{f.facility_name}</strong>
                                  {f.address ? ` — ${f.address}` : ''}
                                  {f.phone ? ` — ${f.phone}` : ''}
                                  {f.notes ? (
                                    <span style={{ display: 'block', fontSize: '0.85rem', marginTop: '0.2rem' }}>{f.notes}</span>
                                  ) : null}
                                  {f.directions_url ? (
                                    <>
                                      {' '}
                                      <a href={f.directions_url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent)' }}>
                                        Directions
                                      </a>
                                    </>
                                  ) : null}
                                </li>
                              )
                            )}
                          </ul>
                        ) : (
                          <p style={{ marginTop: '0.5rem' }}>
                            Enable device location or add state and city on the form for hospital suggestions, or call emergency services for the nearest ER.
                          </p>
                        )}
                      </DetailBlock>
                    )}

                    {openAgentPanel === 'ambulance' && (
                      <DetailBlock title="Ambulance / emergency dispatch">
                        {!symptoms.result.emergencyRouting?.ambulance ? (
                          <p>No ambulance dispatch payload was returned. In a real emergency, call your local emergency number (e.g. 911, 112, 108).</p>
                        ) : (
                          <>
                            {symptoms.result.emergencyRouting.ambulance.region_detected &&
                              symptoms.result.emergencyRouting.ambulance.region_detected !== 'unknown' &&
                              symptoms.result.emergencyRouting.ambulance.region_detected !== 'unmatched' && (
                                <p style={{ fontSize: '0.9rem', color: 'var(--text-paragraph)', marginBottom: '0.5rem' }}>
                                  Based on your location: <strong>{symptoms.result.emergencyRouting.ambulance.region_detected}</strong>
                                </p>
                              )}
                            <p><strong>Emergency numbers for this area:</strong></p>
                            <ul style={{ margin: '0.25rem 0', paddingLeft: '1.25rem' }}>
                              {Object.entries(symptoms.result.emergencyRouting.ambulance.dispatch_numbers ?? {}).map(([k, v]) => (
                                <li key={k}>
                                  <strong>{k}:</strong> {String(v)}
                                </li>
                              ))}
                            </ul>
                            {Array.isArray(symptoms.result.emergencyRouting.ambulance.instructions) && (
                              <ul style={{ marginTop: '0.5rem', paddingLeft: '1.25rem' }}>
                                {symptoms.result.emergencyRouting.ambulance.instructions.map((line: string) => (
                                  <li key={line}>{line}</li>
                                ))}
                              </ul>
                            )}
                            {symptoms.result.emergencyRouting.ambulance.if_caller_outside_home_region && (
                              <p style={{ marginTop: '0.5rem', fontSize: '0.9rem' }}>
                                {String(symptoms.result.emergencyRouting.ambulance.if_caller_outside_home_region)}
                              </p>
                            )}
                          </>
                        )}
                      </DetailBlock>
                    )}

                    {symptoms.result.topConditions && (
                      <p className="recommendation" style={{ marginTop: '0.75rem' }}>
                        <strong>ML top conditions:</strong> {symptoms.result.topConditions}
                      </p>
                    )}

                    <div className="conditions-list patient-summary-section">
                      <h4>Patient Summary</h4>
                      <div className="patient-summary-content glass-panel" style={{ padding: '1.5rem', background: 'rgba(0,0,0,0.3)', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)' }}>
                        <div className="patient-summary-markdown">
                          <ReactMarkdown remarkPlugins={[remarkGfm]} components={patientSummaryMarkdownComponents}>
                            {String(symptoms.result.patientSummary ?? '')}
                          </ReactMarkdown>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="result-actions">
                    <button
                      className="btn btn-secondary"
                      onClick={() => {
                        setOpenAgentPanel(null);
                        setSymptoms((prev) => ({
                          ...prev,
                          age: '',
                          state: '',
                          city: '',
                          text: '',
                          isSubmitting: false,
                          result: null,
                          error: null,
                        }));
                      }}
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
