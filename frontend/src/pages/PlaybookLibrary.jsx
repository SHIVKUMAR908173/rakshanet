import React, { useState, useEffect } from 'react';
import { BookOpen, Shield, AlertTriangle, ShieldAlert, Zap, Filter, Search } from 'lucide-react';
import { fetchPlaybooks } from '../api/client';

const DEMO_PLAYBOOKS = [
  {
    id: 1, name: 'Compromised Credential Response', threat_type: 'credential_compromise',
    severity: 'high', mitre_technique: 'T1078', mitre_technique_name: 'Valid Accounts',
    description: 'Response playbook for suspected credential compromise — triggered when anomalous login follows a phishing click.',
    action_sequence: [
      { step_number: 1, action: 'force_password_reset', is_automated: true, requires_confirmation: true, estimated_minutes: 2 },
      { step_number: 2, action: 'terminate_sessions', is_automated: true, requires_confirmation: true, estimated_minutes: 2 },
      { step_number: 3, action: 'enable_mfa', is_automated: true, requires_confirmation: true, estimated_minutes: 3 },
    ],
    estimated_time_minutes: 20,
  },
  {
    id: 2, name: 'Anomalous OT/SCADA Access Response', threat_type: 'ot_anomaly',
    severity: 'critical', mitre_technique: 'T1021', mitre_technique_name: 'Remote Services',
    description: 'CRITICAL: Response playbook for anomalous access to OT/SCADA control endpoints.',
    action_sequence: [
      { step_number: 1, action: 'isolate_segment', is_automated: true, requires_confirmation: true, estimated_minutes: 3 },
      { step_number: 2, action: 'page_ot_engineer', is_automated: true, requires_confirmation: false, estimated_minutes: 1 },
      { step_number: 3, action: 'escalate_soc', is_automated: true, requires_confirmation: false, estimated_minutes: 1 },
    ],
    estimated_time_minutes: 30,
  },
  {
    id: 3, name: 'Data Exfiltration Response', threat_type: 'data_exfil',
    severity: 'critical', mitre_technique: 'T1041', mitre_technique_name: 'Exfiltration Over C2 Channel',
    description: 'CRITICAL: Response playbook for detected data exfiltration — abnormal outbound volume.',
    action_sequence: [
      { step_number: 1, action: 'block_egress', is_automated: true, requires_confirmation: true, estimated_minutes: 2 },
      { step_number: 2, action: 'isolate_host', is_automated: true, requires_confirmation: true, estimated_minutes: 3 },
    ],
    estimated_time_minutes: 25,
  },
  {
    id: 4, name: 'Phishing Email Response', threat_type: 'phishing',
    severity: 'medium', mitre_technique: 'T1566', mitre_technique_name: 'Phishing',
    description: 'Response playbook for confirmed phishing emails targeting organisation users.',
    action_sequence: [
      { step_number: 1, action: 'quarantine_email', is_automated: true, requires_confirmation: false, estimated_minutes: 2 },
      { step_number: 2, action: 'block_sender_domain', is_automated: true, requires_confirmation: true, estimated_minutes: 2 },
    ],
    estimated_time_minutes: 15,
  },
];

export default function PlaybookLibrary() {
  const [playbooks, setPlaybooks] = useState(DEMO_PLAYBOOKS);
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    setLoading(true);
    fetchPlaybooks()
      .then((d) => {
        const fetched = d?.playbooks || (Array.isArray(d) ? d : []);
        if (fetched.length > 0) {
          setPlaybooks(fetched);
        } else {
          setPlaybooks(DEMO_PLAYBOOKS);
        }
      })
      .catch(() => setPlaybooks(DEMO_PLAYBOOKS))
      .finally(() => setLoading(false));
  }, []);

  const filteredPlaybooks = playbooks.filter(pb => 
    pb.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pb.threat_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
    pb.mitre_technique.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div>
      <div className="page-header">
        <h1>📖 Playbook Library</h1>
        <p>MITRE ATT&CK-aligned response sequences mapped to threat types</p>
      </div>

      <div className="flex items-center justify-between mb-6">
        <div style={{ position: 'relative', width: 300 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: 10, color: 'var(--text-tertiary)' }} />
          <input
            type="text"
            placeholder="Search playbooks..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{
              width: '100%', background: 'var(--bg-input)', border: '1px solid var(--border-primary)',
              borderRadius: 'var(--radius-md)', padding: '8px 12px 8px 36px',
              color: 'var(--text-primary)', fontSize: 'var(--text-sm)',
              fontFamily: 'var(--font-sans)',
            }}
          />
        </div>
        <button className="btn btn-primary" onClick={() => alert('Create Playbook editor would open here.')}>
          <BookOpen size={16} /> Create Playbook
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: 'var(--space-6)' }}>
        {filteredPlaybooks.map(pb => (
          <div className="card" key={pb.id} style={{ display: 'flex', flexDirection: 'column' }}>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 style={{ fontSize: 'var(--text-lg)', fontWeight: 700, marginBottom: 4 }}>{pb.name}</h3>
                <span className="mitre-tag">{pb.mitre_technique} — {pb.mitre_technique_name}</span>
              </div>
              <span className={`severity-badge ${pb.severity}`}>{pb.severity}</span>
            </div>
            
            <p style={{ fontSize: 'var(--text-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-5)', flex: 1 }}>
              {pb.description}
            </p>

            <div style={{ background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', padding: 'var(--space-4)', marginBottom: 'var(--space-5)' }}>
              <div style={{ fontSize: 'var(--text-xs)', textTransform: 'uppercase', color: 'var(--text-tertiary)', fontWeight: 700, marginBottom: 8, letterSpacing: '0.05em' }}>
                Action Sequence Snippet
              </div>
              {pb.action_sequence.slice(0, 3).map((step, idx) => (
                <div key={idx} style={{ display: 'flex', gap: 8, marginBottom: 6, fontSize: 'var(--text-sm)' }}>
                  <span style={{ color: 'var(--accent-light)', fontWeight: 600 }}>{step.step_number}.</span>
                  <span style={{ color: 'var(--text-secondary)' }}>{step.action.replace(/_/g, ' ')}</span>
                  {step.is_automated && <Zap size={14} style={{ color: 'var(--status-info)', marginLeft: 'auto' }} />}
                </div>
              ))}
              {pb.action_sequence.length > 3 && (
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', marginTop: 4, fontStyle: 'italic' }}>
                  + {pb.action_sequence.length - 3} more steps
                </div>
              )}
            </div>

            <div className="flex justify-between items-center" style={{ borderTop: '1px solid var(--border-secondary)', paddingTop: 'var(--space-4)' }}>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)' }}>
                Est. resolution time: <span style={{ color: 'var(--text-primary)', fontWeight: 600 }}>{pb.estimated_time_minutes}m</span>
              </div>
              <button className="btn btn-secondary" onClick={() => alert(`View details for playbook: ${pb.name}`)}>View Full Playbook →</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
