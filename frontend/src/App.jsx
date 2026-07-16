import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';

import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import AlertQueue from './pages/AlertQueue';
import AlertDetail from './pages/AlertDetail';
import PlaybookLibrary from './pages/PlaybookLibrary';
import Incidents from './pages/Incidents';
import Settings from './pages/Settings';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="alerts" element={<AlertQueue />} />
          <Route path="alerts/:id" element={<AlertDetail />} />
          <Route path="playbooks" element={<PlaybookLibrary />} />
          <Route path="incidents" element={<Incidents />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
