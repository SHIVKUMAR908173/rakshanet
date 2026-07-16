import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts';
import {
  Shield, AlertTriangle, Activity, CheckCircle,
  TrendingUp, Clock, Zap, Target,
} from 'lucide-react';
import { fetchDashboardSummary } from '../api/client';

// ── Demo data used when API is not yet connected ──
const DEMO_DATA = {
  total_alerts: 247,
  open_alerts: 38,
  critical_alerts: 5,
  high_alerts: 12,
  medium_alerts: 21,
  low_alerts: 209,
  total_incidents: 18,
  open_incidents: 4,
  resolved_incidents: 14,
  alerts_today: 12,
  avg_risk_score: 0.423,
  threat_type_breakdown: {
    phishing: 142,
    credential_compromise: 41,
    brute_force: 28,
    ot_anomaly: 19,
    data_exfil: 12,
    ddos: 5,
  },
  severity_breakdown: { low: 209, medium: 21, high: 12, critical: 5 },
  alerts_trend: [
    { date: '2026-07-01', count: 8 },
    { date: '2026-07-02', count: 12 },
    { date: '2026-07-03', count: 6 },
    { date: '2026-07-04', count: 15 },
    { date: '2026-07-05', count: 9 },
    { date: '2026-07-06', count: 22 },
    { date: '2026-07-07', count: 18 },
    { date: '2026-07-08', count: 11 },
    { date: '2026-07-09', count: 14 },
    { date: '2026-07-10', count: 7 },
    { date: '2026-07-11', count: 19 },
    { date: '2026-07-12', count: 25 },
    { date: '2026-07-13', count: 16 },
    { date: '2026-07-14', count: 31 },
    { date: '2026-07-15', count: 20 },
    { date: '2026-07-16', count: 12 },
  ],
  recent_alerts: [
    { id: 1, severity: 'critical', threat_type: 'credential_compromise', risk_score: 0.94, status: 'open', explanation_text: 'Phishing + anomalous login on same identity within 2 hours', created_at: '2026-07-16T08:15:00Z' },
    { id: 2, severity: 'high', threat_type: 'ot_anomaly', risk_score: 0.82, status: 'investigating', explanation_text: 'Off-hours SCADA access from new device', created_at: '2026-07-16T07:42:00Z' },
    { id: 3, severity: 'high', threat_type: 'data_exfil', risk_score: 0.78, status: 'open', explanation_text: 'Abnormal outbound transfer: 340MB to foreign IP', created_at: '2026-07-16T06:30:00Z' },
    { id: 4, severity: 'medium', threat_type: 'phishing', risk_score: 0.62, status: 'open', explanation_text: 'Hindi-language KYC phishing with spoofed SBI domain', created_at: '2026-07-16T05:15:00Z' },
    { id: 5, severity: 'medium', threat_type: 'brute_force', risk_score: 0.55, status: 'confirmed', explanation_text: '47 failed login attempts from rotating IPs', created_at: '2026-07-15T23:10:00Z' },
  ],
};

const SEVERITY_COLORS = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
};

const THREAT_COLORS = ['#3b82f6', '#8b5cf6', '#ef4444', '#f97316', '#06b6d4', '#eab308'];

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'rgba(15, 20, 37, 0.95)',
      border: '1px solid rgba(59, 130, 246, 0.3)',
      borderRadius: '8px',
      padding: '10px 14px',
      fontSize: '0.8125rem',
    }}>
      <p style={{ color: '#94a3b8', marginBottom: 4 }}>{label}</p>
      {payload.map((p, i) => (
        <p key={i} style={{ color: p.color || '#e2e8f0', fontWeight: 600 }}>
          {p.name}: {p.value}
        </p>
      ))}
    </div>
  );
};

export default function Dashboard() {
  const [data, setData] = useState(DEMO_DATA);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    fetchDashboardSummary()
      .then((d) => setData({ ...DEMO_DATA, ...d }))
      .catch(() => setData(DEMO_DATA))
      .finally(() => setLoading(false));
  }, []);

  const severityPieData = Object.entries(data.severity_breakdown).map(
    ([name, value]) => ({ name, value })
  );

  const threatBarData = Object.entries(data.threat_type_breakdown).map(
    ([name, value]) => ({ name: name.replace(/_/g, ' '), value })
  );

  const formatDate = (d) => {
    const parts = d.split('-');
    return `${parts[1]}/${parts[2]}`;
  };

  return (
    <div>
      <div className="page-header">
        <h1>🛡️ RakshaNet Dashboard</h1>
        <p>Real-time threat detection & guided response for critical infrastructure</p>
      </div>

      {/* ── Stats Grid ── */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue"><Shield size={22} /></div>
          <div className="stat-info">
            <span className="stat-label">Total Alerts</span>
            <span className="stat-value">{data.total_alerts}</span>
            <span className="stat-change">{data.alerts_today} today</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon red"><AlertTriangle size={22} /></div>
          <div className="stat-info">
            <span className="stat-label">Critical</span>
            <span className="stat-value" style={{ color: '#ef4444' }}>{data.critical_alerts}</span>
            <span className="stat-change">Requires immediate action</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon orange"><Zap size={22} /></div>
          <div className="stat-info">
            <span className="stat-label">Open Alerts</span>
            <span className="stat-value">{data.open_alerts}</span>
            <span className="stat-change">{data.high_alerts} high severity</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green"><CheckCircle size={22} /></div>
          <div className="stat-info">
            <span className="stat-label">Resolved</span>
            <span className="stat-value">{data.resolved_incidents}</span>
            <span className="stat-change">{data.total_incidents} total incidents</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon cyan"><Target size={22} /></div>
          <div className="stat-info">
            <span className="stat-label">Avg Risk Score</span>
            <span className="stat-value">{data.avg_risk_score.toFixed(2)}</span>
            <span className="stat-change">Across all events</span>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon blue"><Clock size={22} /></div>
          <div className="stat-info">
            <span className="stat-label">MTTD</span>
            <span className="stat-value">&lt;5m</span>
            <span className="stat-change">Mean time to detect</span>
          </div>
        </div>
      </div>

      {/* ── Charts ── */}
      <div className="charts-grid">
        {/* Alert Trend */}
        <div className="chart-card">
          <div className="card-title">Alert Trend (Last 16 Days)</div>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={data.alerts_trend}>
              <defs>
                <linearGradient id="alertGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
              <XAxis
                dataKey="date"
                tickFormatter={formatDate}
                tick={{ fill: '#64748b', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(148,163,184,0.1)' }}
              />
              <YAxis
                tick={{ fill: '#64748b', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(148,163,184,0.1)' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="count"
                name="Alerts"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#alertGradient)"
                dot={{ fill: '#3b82f6', r: 3, strokeWidth: 0 }}
                activeDot={{ r: 5, fill: '#60a5fa', stroke: '#3b82f6', strokeWidth: 2 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Severity Distribution */}
        <div className="chart-card">
          <div className="card-title">Severity Distribution</div>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie
                data={severityPieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={95}
                paddingAngle={3}
                dataKey="value"
              >
                {severityPieData.map((entry) => (
                  <Cell
                    key={entry.name}
                    fill={SEVERITY_COLORS[entry.name] || '#64748b'}
                    stroke="transparent"
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: '12px', color: '#94a3b8' }}
                formatter={(value) => (
                  <span style={{ color: '#94a3b8', textTransform: 'capitalize' }}>{value}</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Threat Type Breakdown */}
        <div className="chart-card">
          <div className="card-title">Threat Type Breakdown</div>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={threatBarData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.08)" />
              <XAxis
                type="number"
                tick={{ fill: '#64748b', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(148,163,184,0.1)' }}
              />
              <YAxis
                dataKey="name"
                type="category"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                axisLine={{ stroke: 'rgba(148,163,184,0.1)' }}
                width={120}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="value" name="Count" radius={[0, 4, 4, 0]} barSize={18}>
                {threatBarData.map((_, i) => (
                  <Cell key={i} fill={THREAT_COLORS[i % THREAT_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Recent Alerts */}
        <div className="chart-card">
          <div className="card-title">Recent Alerts</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {data.recent_alerts.map((alert) => (
              <div
                key={alert.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '10px 12px',
                  background: 'var(--bg-tertiary)',
                  borderRadius: 'var(--radius-md)',
                  borderLeft: `3px solid ${SEVERITY_COLORS[alert.severity]}`,
                }}
              >
                <span className={`severity-badge ${alert.severity}`}>
                  {alert.severity}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontSize: 'var(--text-sm)',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}>
                    {alert.explanation_text}
                  </div>
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--text-tertiary)', marginTop: 2 }}>
                    <span className="mitre-tag" style={{ marginRight: 8 }}>
                      {alert.threat_type.replace(/_/g, ' ')}
                    </span>
                    Score: {alert.risk_score.toFixed(2)}
                  </div>
                </div>
                <span className={`status-badge ${alert.status}`}>{alert.status}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
