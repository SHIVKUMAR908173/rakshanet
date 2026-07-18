import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';

export default function AnalyticsDashboard({ alerts }) {
  if (!alerts || alerts.length === 0) {
    return null;
  }

  // 1. Prepare data for the Line Chart (Alerts over time - simplified by day)
  const alertsByDate = {};
  alerts.forEach(alert => {
    // Assuming created_at is a string like "2026-07-18T10:45:00Z"
    const dateObj = new Date(alert.created_at);
    // Create a simple MM/DD label
    const dateLabel = `${dateObj.getMonth() + 1}/${dateObj.getDate()}`;
    
    if (!alertsByDate[dateLabel]) {
      alertsByDate[dateLabel] = 0;
    }
    alertsByDate[dateLabel] += 1;
  });

  const lineData = Object.keys(alertsByDate).map(date => ({
    date,
    alerts: alertsByDate[date]
  })).sort((a, b) => new Date(a.date) - new Date(b.date));

  // 2. Prepare data for the Donut Chart (Severity distribution)
  const severityCounts = { low: 0, medium: 0, high: 0, critical: 0 };
  alerts.forEach(alert => {
    if (severityCounts[alert.severity] !== undefined) {
      severityCounts[alert.severity] += 1;
    }
  });

  const pieData = [
    { name: 'Critical', value: severityCounts.critical, color: '#ef4444' }, // red-500
    { name: 'High', value: severityCounts.high, color: '#f97316' },     // orange-500
    { name: 'Medium', value: severityCounts.medium, color: '#eab308' }, // yellow-500
    { name: 'Low', value: severityCounts.low, color: '#3b82f6' }        // blue-500
  ].filter(item => item.value > 0);

  return (
    <div style={{ display: 'flex', gap: '24px', marginBottom: '32px' }}>
      
      {/* Line Chart Card */}
      <div style={{
        flex: 2,
        background: 'rgba(30, 41, 59, 0.5)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '24px',
      }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)' }}>
          Alert Volume (Recent)
        </h3>
        <div style={{ height: '240px' }}>
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={lineData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
              <XAxis dataKey="date" stroke="var(--text-tertiary)" fontSize={12} tickMargin={10} />
              <YAxis stroke="var(--text-tertiary)" fontSize={12} allowDecimals={false} />
              <RechartsTooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                itemStyle={{ color: 'var(--text-primary)' }}
              />
              <Line type="monotone" dataKey="alerts" stroke="var(--primary)" strokeWidth={3} dot={{ r: 4, fill: 'var(--primary)' }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Donut Chart Card */}
      <div style={{
        flex: 1,
        background: 'rgba(30, 41, 59, 0.5)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '16px',
        padding: '24px',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <h3 style={{ margin: '0 0 16px 0', fontSize: '16px', fontWeight: '600', color: 'var(--text-primary)' }}>
          Severity Distribution
        </h3>
        <div style={{ height: '240px', flex: 1 }}>
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={5}
                dataKey="value"
                stroke="none"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <RechartsTooltip 
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: 'var(--text-primary)' }}
                itemStyle={{ color: 'var(--text-primary)' }}
              />
              <Legend verticalAlign="bottom" height={36} iconType="circle" />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
}
