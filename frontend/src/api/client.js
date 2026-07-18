/**
 * RakshaNet API Client — wraps all backend API calls.
 */

const API_BASE = '/api/v1';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  const token = localStorage.getItem('rakshanet_token');
  const headers = { 'Content-Type': 'application/json' };
  
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  const config = {
    headers: { ...headers, ...(options.headers || {}) },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// ── Dashboard ──
export const fetchDashboardSummary = () => request('/dashboard/summary');

// ── Alerts ──
export const fetchAlerts = (params = {}) => {
  const query = new URLSearchParams();
  if (params.severity) query.set('severity', params.severity);
  if (params.status) query.set('status', params.status);
  if (params.threat_type) query.set('threat_type', params.threat_type);
  if (params.page) query.set('page', params.page);
  if (params.page_size) query.set('page_size', params.page_size);
  const qs = query.toString();
  return request(`/alerts${qs ? '?' + qs : ''}`);
};

export const fetchAlert = (id) => request(`/alerts/${id}`);

export const submitFeedback = (alertId, data) =>
  request(`/alerts/${alertId}/feedback`, {
    method: 'POST',
    body: JSON.stringify(data),
  });

export const updateAlertStatus = (alertId, status) =>
  request(`/alerts/${alertId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });

// ── Playbooks ──
export const fetchPlaybooks = (params = {}) => {
  const query = new URLSearchParams();
  if (params.threat_type) query.set('threat_type', params.threat_type);
  if (params.severity) query.set('severity', params.severity);
  const qs = query.toString();
  return request(`/playbooks${qs ? '?' + qs : ''}`);
};

export const fetchPlaybooksByThreat = (threatType, severity) => {
  const query = severity ? `?severity=${severity}` : '';
  return request(`/playbooks/${threatType}${query}`);
};

// ── Incidents ──
export const createIncident = (data) =>
  request('/incidents', { method: 'POST', body: JSON.stringify(data) });

export const fetchIncidents = (params = {}) => {
  const query = new URLSearchParams();
  if (params.status) query.set('status', params.status);
  if (params.page) query.set('page', params.page);
  const qs = query.toString();
  return request(`/incidents${qs ? '?' + qs : ''}`);
};

export const fetchIncident = (id) => request(`/incidents/${id}`);

export const updateIncident = (id, data) =>
  request(`/incidents/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });

// ── Ingestion (for demo) ──
export const ingestEmail = (data) =>
  request('/ingest/email', { method: 'POST', body: JSON.stringify(data) });

export const ingestNetworkLog = (data) =>
  request('/ingest/network-log', { method: 'POST', body: JSON.stringify(data) });
