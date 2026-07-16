import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, AlertTriangle, Shield, BookOpen,
  CheckCircle, XCircle, Clock, ExternalLink,
} from 'lucide-react';

const DEMO_ALERT = {
  id: 1, user_identity: 'ravi.sharma@gov.in', asset_id: 1,
  risk_score: 0.94, severity: 'critical',
  threat_type: 'credential_compromise', mitre_technique: 'T1078', status: 'open',
  explanation_text: 'CRITICAL ALERT — Immediate action required. Flagged mainly due to: urgency and credential-harvest language detected in email text; access from unexpected geographic location; text and URL models disagree — common evasion pattern. Multiple independent detection signals on the same identity increase confidence in this alert.',
  explanation_json: {
    features: [
      { name: 'text_urgency_score', value: 0.82, description: 'Urgency and credential-harvest language detected in email text' },
      { name: 'geo_anomaly', value: 0.6, description: 'Access from unexpected geographic location (Ukraine)' },
      { name: 'model_disagreement_signal', value: 0.15, description: 'Text and URL models disagree — common evasion pattern' },
      { name: 'correlation_bonus', value: 0.2, description: 'Correlated phishing + anomaly signals on same identity' },
      { name: 'spf_fail', value: 0.15, description: 'SPF email authentication check failed' },
    ],
    threat_context: {
      mitre_id: 'T1078', mitre_name: 'Valid Accounts',
      tactic: 'Defense Evasion, Persistence, Privilege Escalation, Initial Access',
      description: 'Compromised credentials are being used to access systems.',
      recommended_actions: [
        'Force password reset', 'Terminate active sessions',
        'Require step-up authentication', 'Review recent activity on the account',
      ],
    },
  },
  source_event_ids: [101, 102],
  created_at: '2026-07-16T08:15:00Z', updated_at: '2026-07-16T08:15:00Z',
};

const DEMO_PLAYBOOK = {
  playbook_id: 2, name: 'Compromised Credential Response',
  threat_type: 'credential_compromise', severity: 'high',
  mitre_technique: 'T1078', mitre_technique_name: 'Valid Accounts',
  description: 'Response playbook for suspected credential compromise.',
  action_sequence: [
    { step_number: 1, action: 'force_password_reset', description: 'Immediately force a password reset on the compromised account', is_automated: true, requires_confirmation: true, estimated_minutes: 2 },
    { step_number: 2, action: 'terminate_sessions', description: 'Terminate all active sessions for the affected user across all services', is_automated: true, requires_confirmation: true, estimated_minutes: 2 },
    { step_number: 3, action: 'enable_mfa', description: 'Require step-up / multi-factor authentication for the next login', is_automated: true, requires_confirmation: true, estimated_minutes: 3 },
    { step_number: 4, action: 'review_activity', description: 'Review all recent activity on the account for signs of data access or lateral movement', is_automated: false, requires_confirmation: false, estimated_minutes: 10 },
    { step_number: 5, action: 'notify_user', description: 'Contact the user directly to confirm whether the access was legitimate', is_automated: false, requires_confirmation: false, estimated_minutes: 3 },
  ],
  requires_human_confirmation: true, estimated_time_minutes: 20,
};

export default function AlertDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [alert, setAlert] = useState(DEMO_ALERT);
  const [playbook] = useState(DEMO_PLAYBOOK);

  const ctx = alert.explanation_json?.threat_context || {};
  const features = alert.explanation_json?.features || [];

  return (
    <div>
      <div className="page-header">
        <button className="btn btn-secondary mb-4" onClick={() => navigate('/alerts')}>
          <ArrowLeft size={16} /> Back to Alert Queue
        </button>
        <div className="flex items-center gap-4">
          <h1>Alert #{alert.id}</h1>
          <span className={`severity-badge ${alert.severity}`}>{alert.severity}</span>
          <span className={`status-badge ${alert.status}`}>{alert.status}</span>
        </div>
        <p>{alert.threat_type.replace(/_/g, ' ')} — {alert.user_identity}</p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 'var(--space-6)' }}>
        {/* Left: Alert Details + SHAP */}
        <div>
          {/* Risk Score */}
          <div className="card mb-6">
            <div className="card-header">
              <span className="card-title">Risk Assessment</span>
              <span className="mitre-tag">{alert.mitre_technique}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-6)', marginBottom: 'var(--space-4)' }}>
              <div style={{
                width: 80, height: 80, borderRadius: '50%',
                background: `conic-gradient(${alert.severity === 'critical' ? '#ef4444' : '#f97316'} ${alert.risk_score * 360}deg, var(--bg-primary) 0)`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                <div style={{
                  width: 60, height: 60, borderRadius: '50%', background: 'var(--bg-card)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xl)', fontWeight: 800,
                  color: alert.severity === 'critical' ? '#ef4444' : '#f97316',
                }}>
                  {alert.risk_score.toFixed(2)}
                </div>
              </div>
              <div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 4 }}>
                  MITRE ATT&CK: <strong style={{ color: 'var(--text-primary)' }}>{ctx.mitre_name}</strong>
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
                  Tactic: {ctx.tactic}
                </div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', marginTop: 4 }}>
                  {ctx.description}
                </div>
              </div>
            </div>
          </div>

          {/* SHAP Explanation */}
          <div className="shap-explanation mb-6">
            <div className="shap-title">🔍 Feature Contributions (SHAP Analysis)</div>
            {features.map((f, i) => (
              <div className="shap-feature" key={i}>
                <span className="shap-feature-name">{f.description}</span>
                <div className="shap-feature-bar">
                  <div className="shap-feature-bar-fill" style={{ width: `${Math.min(f.value * 120, 100)}%` }} />
                </div>
                <span className="shap-feature-value">{f.value.toFixed(2)}</span>
              </div>
            ))}
            <div className="shap-summary">{alert.explanation_text}</div>
          </div>

          {/* Event Trail */}
          <div className="card">
            <div className="card-title mb-4">📋 Source Events</div>
            {alert.source_event_ids.map(eid => (
              <div key={eid} style={{
                padding: '8px 12px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)',
                marginBottom: 8, display: 'flex', alignItems: 'center', gap: 8,
                fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)',
              }}>
                <span style={{ color: 'var(--text-accent)' }}>Event #{eid}</span>
                <span style={{ color: 'var(--text-tertiary)' }}>— contributed to this alert's risk score</span>
              </div>
            ))}
          </div>
        </div>

        {/* Right: Playbook + Actions */}
        <div>
          {/* Recommended Playbook */}
          <div className="card mb-6">
            <div className="card-header">
              <span className="card-title">📖 Recommended Playbook</span>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
                <Clock size={12} style={{ display: 'inline', marginRight: 4 }} />
                Est. {playbook.estimated_time_minutes} min
              </span>
            </div>
            <h3 style={{ fontSize: 'var(--text-md)', fontWeight: 700, marginBottom: 'var(--space-2)' }}>
              {playbook.name}
            </h3>
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-4)' }}>
              {playbook.description}
            </p>
            <div className="mitre-tag mb-4">{playbook.mitre_technique} — {playbook.mitre_technique_name}</div>

            <div className="playbook-steps">
              {playbook.action_sequence.map(step => (
                <div className="playbook-step" key={step.step_number}>
                  <div className="step-number">{step.step_number}</div>
                  <div className="step-content">
                    <div className="step-action">{step.action.replace(/_/g, ' ')}</div>
                    <div className="step-description">{step.description}</div>
                    <div className="step-tags">
                      <span className={`step-tag ${step.is_automated ? 'automated' : 'manual'}`}>
                        {step.is_automated ? '⚡ Automated' : '👤 Manual'}
                      </span>
                      {step.requires_confirmation && (
                        <span className="step-tag confirmation">🔐 Needs Confirmation</span>
                      )}
                      <span className="step-tag manual">~{step.estimated_minutes}m</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="card">
            <div className="card-title mb-4">⚡ Actions</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', padding: '12px' }}>
                <BookOpen size={16} /> Open Incident with This Playbook
              </button>
              <button className="btn btn-danger" style={{ width: '100%', justifyContent: 'center', padding: '12px' }}>
                <AlertTriangle size={16} /> Confirm Threat
              </button>
              <button className="btn btn-success" style={{ width: '100%', justifyContent: 'center', padding: '12px' }}>
                <CheckCircle size={16} /> Dismiss — False Positive
              </button>
              <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'center', padding: '12px' }}>
                <Shield size={16} /> Escalate to SOC Lead
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
