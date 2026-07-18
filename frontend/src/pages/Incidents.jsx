import React from 'react';
import { FileWarning, Plus, Search, Filter } from 'lucide-react';

export default function Incidents() {
  return (
    <div>
      <div className="page-header">
        <div className="flex items-center justify-between">
          <div>
            <h1>🚨 Incidents</h1>
            <p>Tracked and escalated security incidents</p>
          </div>
          <button className="btn btn-primary" onClick={() => alert('New Incident dialog would open here.')}>
            <Plus size={16} /> Open New Incident
          </button>
        </div>
      </div>

      <div className="empty-state card">
        <FileWarning size={48} />
        <h3>No Open Incidents</h3>
        <p>All clear! There are currently no active incidents requiring your attention.</p>
        <button className="btn btn-secondary mt-6" onClick={() => alert('Loading resolved incidents...')}>View Resolved Incidents</button>
      </div>
    </div>
  );
}
