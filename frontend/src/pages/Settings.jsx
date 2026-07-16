import React from 'react';
import { Settings as SettingsIcon, Bell, Shield, Users, Database } from 'lucide-react';

export default function Settings() {
  return (
    <div>
      <div className="page-header">
        <h1>⚙️ Settings</h1>
        <p>Configure RakshaNet platform preferences and integrations</p>
      </div>

      <div style={{ maxWidth: '800px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
        
        {/* Profile Settings */}
        <div className="chart-card">
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Users size={18} />
            Account Preferences
          </div>
          <div style={{ padding: '16px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', marginTop: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Analyst Profile</div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)' }}>Update your name, email, and role</div>
              </div>
              <button className="playbook-btn">Edit Profile</button>
            </div>
          </div>
        </div>

        {/* Engine Configuration */}
        <div className="chart-card">
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Shield size={18} />
            Detection Engines
          </div>
          <div style={{ padding: '16px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', marginTop: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Correlation Window</div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)' }}>Time window (in hours) to link related events</div>
              </div>
              <div style={{ color: 'var(--text-secondary)', fontWeight: 'bold' }}>24 Hours</div>
            </div>
            <div style={{ height: '1px', background: 'rgba(148,163,184,0.1)', margin: '12px 0' }} />
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Severity Thresholds</div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)' }}>Risk score boundaries for alert generation</div>
              </div>
              <button className="playbook-btn">Configure</button>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="chart-card">
          <div className="card-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Bell size={18} />
            Notifications
          </div>
          <div style={{ padding: '16px', background: 'var(--bg-tertiary)', borderRadius: 'var(--radius-md)', marginTop: '12px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Email Alerts</div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)' }}>Receive email notifications for Critical alerts</div>
              </div>
              <div className="status-badge resolved">Enabled</div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
