import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  AlertTriangle,
  BookOpen,
  FileWarning,
  Settings,
  Shield,
  Activity,
} from 'lucide-react';

export default function Sidebar() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/alerts', label: 'Alert Queue', icon: AlertTriangle, badge: null },
    { path: '/playbooks', label: 'Playbook Library', icon: BookOpen },
    { path: '/incidents', label: 'Incidents', icon: FileWarning },
  ];

  const systemItems = [
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">R</div>
        <div>
          <div className="sidebar-title">RakshaNet</div>
          <div className="sidebar-subtitle">Threat Detection</div>
        </div>
      </div>

      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Monitoring</div>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
            end={item.path === '/'}
          >
            <item.icon />
            <span>{item.label}</span>
            {item.badge && <span className="nav-badge">{item.badge}</span>}
          </NavLink>
        ))}

        <div className="sidebar-section-label" style={{ marginTop: 'auto' }}>
          System
        </div>
        {systemItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `nav-item ${isActive ? 'active' : ''}`
            }
          >
            <item.icon />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className="status-dot" />
          <span>All engines operational</span>
        </div>
        <div className="sidebar-status" style={{ marginTop: '4px' }}>
          <Activity size={12} />
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}>
            v0.1.0 — Prototype
          </span>
        </div>
      </div>
    </aside>
  );
}
