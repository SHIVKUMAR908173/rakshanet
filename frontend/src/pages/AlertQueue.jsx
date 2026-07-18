import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, Search, Filter, ChevronDown, ChevronUp } from 'lucide-react';
import { fetchAlerts, updateAlertStatus } from '../api/client';

const DEMO_ALERTS = {
  total: 38,
  page: 1,
  page_size: 20,
  alerts: [
    {
      id: 1, user_identity: 'ravi.sharma@gov.in', risk_score: 0.94, severity: 'critical',
      threat_type: 'credential_compromise', mitre_technique: 'T1078', status: 'open',
      explanation_text: 'CRITICAL — Phishing email clicked + anomalous login from foreign IP within 2 hours on same identity. Correlated multi-stage attack.',
      explanation_json: { features: [
        { name: 'text_urgency_score', value: 0.82, description: 'Urgency and credential-harvest language detected' },
        { name: 'geo_anomaly', value: 0.6, description: 'Access from unexpected geographic location' },
        { name: 'model_disagreement_signal', value: 0.15, description: 'Text and URL models disagree' },
      ]},
      source_event_ids: [101, 102], created_at: '2026-07-16T08:15:00Z', updated_at: '2026-07-16T08:15:00Z',
    },
    {
      id: 2, user_identity: 'scada-ops@power.guj.in', risk_score: 0.82, severity: 'high',
      threat_type: 'ot_anomaly', mitre_technique: 'T1021', status: 'investigating',
      explanation_text: 'Off-hours SCADA PLC access from new device fingerprint. Cross-segment traffic detected between IT and OT zones.',
      explanation_json: { features: [
        { name: 'ot_off_hours', value: 0.4, description: 'OT/SCADA accessed outside maintenance windows' },
        { name: 'cross_segment_traffic', value: 0.4, description: 'Cross OT/IT boundary unexpectedly' },
        { name: 'new_device', value: 0.15, description: 'Previously unseen device' },
      ]},
      source_event_ids: [103], created_at: '2026-07-16T07:42:00Z', updated_at: '2026-07-16T07:50:00Z',
    },
    {
      id: 3, user_identity: 'db-admin@bank.coop.in', risk_score: 0.78, severity: 'high',
      threat_type: 'data_exfil', mitre_technique: 'T1041', status: 'open',
      explanation_text: 'Abnormal outbound data transfer: 340MB uploaded to foreign IP over non-standard port. Upload-to-download ratio 15:1.',
      explanation_json: { features: [
        { name: 'high_outbound_volume', value: 0.35, description: 'Abnormally high outbound data transfer' },
        { name: 'abnormal_upload_ratio', value: 0.2, description: 'Upload ratio significantly higher than normal' },
        { name: 'suspicious_port', value: 0.3, description: 'Communication on known backdoor port' },
      ]},
      source_event_ids: [104], created_at: '2026-07-16T06:30:00Z', updated_at: '2026-07-16T06:30:00Z',
    },
    {
      id: 4, user_identity: 'accounts@msme-cluster.in', risk_score: 0.62, severity: 'medium',
      threat_type: 'phishing', mitre_technique: 'T1566', status: 'open',
      explanation_text: 'Hindi-language KYC update phishing email with spoofed SBI domain (sb1-kyc-update.com). SPF and DKIM checks failed.',
      explanation_json: { features: [
        { name: 'text_urgency_score', value: 0.65, description: 'Urgency language: "turant KYC update karein"' },
        { name: 'url_structural_score', value: 0.45, description: 'Spoofed bank domain in URL' },
        { name: 'spf_fail', value: 0.15, description: 'SPF authentication failed' },
      ]},
      source_event_ids: [105], created_at: '2026-07-16T05:15:00Z', updated_at: '2026-07-16T05:15:00Z',
    },
    {
      id: 5, user_identity: 'nurse01@district-hospital.guj.in', risk_score: 0.55, severity: 'medium',
      threat_type: 'brute_force', mitre_technique: 'T1110', status: 'confirmed',
      explanation_text: '47 failed login attempts from 12 rotating IPs targeting EHR system. Pattern consistent with credential stuffing.',
      explanation_json: { features: [
        { name: 'failed_login', value: 0.3, description: 'High rate of failed login attempts' },
        { name: 'off_hours_access', value: 0.15, description: 'Attempts at 2:30 AM IST' },
      ]},
      source_event_ids: [106, 107, 108], created_at: '2026-07-15T23:10:00Z', updated_at: '2026-07-16T01:00:00Z',
    },
    {
      id: 6, user_identity: 'portal-admin@muni-water.guj.in', risk_score: 0.48, severity: 'medium',
      threat_type: 'phishing', mitre_technique: 'T1566', status: 'open',
      explanation_text: 'Gujarati-language vendor invoice phishing with shortener URL (bit.ly). Domain registered 3 days ago.',
      explanation_json: { features: [
        { name: 'url_structural_score', value: 0.35, description: 'URL shortener with brand spoofing' },
        { name: 'text_urgency_score', value: 0.28, description: 'Payment urgency language detected' },
      ]},
      source_event_ids: [109], created_at: '2026-07-15T14:20:00Z', updated_at: '2026-07-15T14:20:00Z',
    },
    {
      id: 7, user_identity: 'vpn-user@state-dept.guj.in', risk_score: 0.42, severity: 'medium',
      threat_type: 'credential_compromise', mitre_technique: 'T1078', status: 'dismissed',
      explanation_text: 'VPN login from new city (Surat). User confirmed travel — false positive.',
      explanation_json: { features: [
        { name: 'geo_anomaly', value: 0.3, description: 'Login from new city' },
        { name: 'new_device', value: 0.15, description: 'New device fingerprint' },
      ]},
      source_event_ids: [110], created_at: '2026-07-15T10:05:00Z', updated_at: '2026-07-15T11:30:00Z',
    },
    {
      id: 8, user_identity: 'webmaster@gov-portal.guj.in', risk_score: 0.35, severity: 'low',
      threat_type: 'ddos', mitre_technique: 'T1498', status: 'resolved',
      explanation_text: 'Traffic spike on public portal — 3x normal volume from 2 ASNs. Rate limiting applied, subsided after 45 minutes.',
      explanation_json: { features: [
        { name: 'high_outbound_volume', value: 0.25, description: 'Unusual traffic volume' },
      ]},
      source_event_ids: [111, 112], created_at: '2026-07-14T16:00:00Z', updated_at: '2026-07-14T17:00:00Z',
    },
  ],
};

const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

export default function AlertQueue() {
  const [alerts, setAlerts] = useState(DEMO_ALERTS);
  const [loading, setLoading] = useState(false);
  const [filterSeverity, setFilterSeverity] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [sortField, setSortField] = useState('risk_score');
  const [sortDir, setSortDir] = useState('desc');
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    fetchAlerts({ severity: filterSeverity || undefined, status: filterStatus || undefined })
      .then((d) => setAlerts(d))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [filterSeverity, filterStatus]);

  const handleUpdateStatus = async (id, status) => {
    try {
      await updateAlertStatus(id, status);
      setAlerts(prev => ({
        ...prev,
        alerts: prev.alerts.map(a => a.id === id ? { ...a, status } : a)
      }));
    } catch (err) {
      console.error("Failed to update status", err);
      alert("Failed to update status: " + err.message);
    }
  };

  const sortedAlerts = [...alerts.alerts].sort((a, b) => {
    let av, bv;
    if (sortField === 'risk_score') { av = a.risk_score; bv = b.risk_score; }
    else if (sortField === 'severity') { av = SEVERITY_ORDER[a.severity]; bv = SEVERITY_ORDER[b.severity]; }
    else if (sortField === 'created_at') { av = new Date(a.created_at); bv = new Date(b.created_at); }
    else { av = a[sortField]; bv = b[sortField]; }
    return sortDir === 'desc' ? (bv > av ? 1 : -1) : (av > bv ? 1 : -1);
  });

  const toggleSort = (field) => {
    if (sortField === field) setSortDir(d => d === 'desc' ? 'asc' : 'desc');
    else { setSortField(field); setSortDir('desc'); }
  };

  const SortIcon = ({ field }) => {
    if (sortField !== field) return null;
    return sortDir === 'desc' ? <ChevronDown size={14} /> : <ChevronUp size={14} />;
  };

  const formatTime = (ts) => {
    const d = new Date(ts);
    return d.toLocaleString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div>
      <div className="page-header">
        <h1>⚡ Alert Queue</h1>
        <p>Prioritised threat alerts with SHAP explanations — sorted by risk score</p>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-6">
        <Filter size={16} style={{ color: 'var(--text-tertiary)' }} />
        <select
          value={filterSeverity}
          onChange={e => setFilterSeverity(e.target.value)}
          style={{
            background: 'var(--bg-input)', border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-md)', padding: '6px 12px',
            color: 'var(--text-primary)', fontSize: 'var(--text-sm)',
            fontFamily: 'var(--font-sans)',
          }}
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={filterStatus}
          onChange={e => setFilterStatus(e.target.value)}
          style={{
            background: 'var(--bg-input)', border: '1px solid var(--border-primary)',
            borderRadius: 'var(--radius-md)', padding: '6px 12px',
            color: 'var(--text-primary)', fontSize: 'var(--text-sm)',
            fontFamily: 'var(--font-sans)',
          }}
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="investigating">Investigating</option>
          <option value="confirmed">Confirmed</option>
          <option value="dismissed">Dismissed</option>
        </select>
        <span className="text-xs text-muted" style={{ marginLeft: 'auto' }}>
          Showing {sortedAlerts.length} of {alerts.total} alerts
        </span>
      </div>

      {/* Alert Table */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <table className="alert-table">
          <thead>
            <tr>
              <th style={{ width: 100, cursor: 'pointer' }} onClick={() => toggleSort('severity')}>
                Severity <SortIcon field="severity" />
              </th>
              <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('risk_score')}>
                Risk <SortIcon field="risk_score" />
              </th>
              <th>Threat Type</th>
              <th>MITRE</th>
              <th>Identity</th>
              <th>Explanation</th>
              <th>Status</th>
              <th style={{ cursor: 'pointer' }} onClick={() => toggleSort('created_at')}>
                Time <SortIcon field="created_at" />
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedAlerts.map(alert => (
              <React.Fragment key={alert.id}>
                <tr
                  className={`severity-${alert.severity}-row`}
                  onClick={() => setExpandedId(expandedId === alert.id ? null : alert.id)}
                >
                  <td><span className={`severity-badge ${alert.severity}`}>{alert.severity}</span></td>
                  <td>
                    <div className="risk-score-bar">
                      <div className="risk-score-track">
                        <div
                          className={`risk-score-fill ${alert.severity}`}
                          style={{ width: `${alert.risk_score * 100}%` }}
                        />
                      </div>
                      <span className="risk-score-value mono">{alert.risk_score.toFixed(2)}</span>
                    </div>
                  </td>
                  <td style={{ textTransform: 'capitalize' }}>{alert.threat_type.replace(/_/g, ' ')}</td>
                  <td><span className="mitre-tag">{alert.mitre_technique}</span></td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}>
                    {alert.user_identity || '—'}
                  </td>
                  <td style={{
                    maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                  }}>
                    {alert.explanation_text}
                  </td>
                  <td><span className={`status-badge ${alert.status}`}>{alert.status}</span></td>
                  <td style={{ fontSize: 'var(--text-xs)', whiteSpace: 'nowrap' }}>{formatTime(alert.created_at)}</td>
                </tr>

                {/* Expanded SHAP explanation */}
                {expandedId === alert.id && (
                  <tr>
                    <td colSpan={8} style={{ padding: 0, background: 'var(--bg-secondary)' }}>
                      <div className="shap-explanation" style={{ margin: '8px 16px 16px', borderRadius: 'var(--radius-md)' }}>
                        <div className="shap-title">🔍 SHAP Explanation — Why this was flagged</div>
                        {alert.explanation_json?.features?.map((f, i) => (
                          <div className="shap-feature" key={i}>
                            <span className="shap-feature-name">{f.description}</span>
                            <div className="shap-feature-bar">
                              <div className="shap-feature-bar-fill" style={{ width: `${f.value * 100}%` }} />
                            </div>
                            <span className="shap-feature-value">{f.value.toFixed(2)}</span>
                          </div>
                        ))}
                        <div className="shap-summary">{alert.explanation_text}</div>
                        <div className="btn-group mt-4">
                          <button className="btn btn-danger" onClick={() => handleUpdateStatus(alert.id, 'confirmed')}>
                            <AlertTriangle size={14} /> Confirm Threat
                          </button>
                          <button className="btn btn-secondary" onClick={() => handleUpdateStatus(alert.id, 'dismissed')}>Dismiss (False Positive)</button>
                          <button className="btn btn-primary" onClick={() => navigate(`/alerts/${alert.id}`)}>
                            View Full Detail →
                          </button>
                        </div>
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
