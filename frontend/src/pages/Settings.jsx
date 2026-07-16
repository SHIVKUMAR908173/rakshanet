import React, { useState } from 'react';
import { Settings as SettingsIcon, Bell, Shield, Users, Database, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user, logout } = useAuth();
  const [showToast, setShowToast] = useState(false);

  const handleEditProfile = () => {
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

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
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{user?.name || 'Analyst Profile'}</div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)' }}>{user?.email || 'Update your name, email, and role'}</div>
              </div>
              <button className="playbook-btn" onClick={handleEditProfile}>Edit Profile</button>
            </div>
            
            <div style={{ height: '1px', background: 'rgba(148,163,184,0.1)', margin: '12px 0' }} />
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>Sign Out</div>
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--text-tertiary)' }}>Log out of the RakshaNet platform</div>
              </div>
              <button 
                className="playbook-btn" 
                style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', border: '1px solid rgba(239, 68, 68, 0.2)' }}
                onClick={logout}
              >
                <LogOut size={16} style={{ marginRight: '8px', display: 'inline' }} />
                Sign Out
              </button>
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

      {/* Simulated Toast Notification */}
      {showToast && (
        <div style={{
          position: 'fixed',
          bottom: '24px',
          right: '24px',
          background: 'var(--success)',
          color: 'white',
          padding: '16px 24px',
          borderRadius: '8px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          zIndex: 50,
          animation: 'slideIn 0.3s ease-out'
        }}>
          ✅ Profile updated successfully!
        </div>
      )}
    </div>
  );
}
