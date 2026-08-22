import React, { useEffect, useState } from 'react';
import { checkHealth } from '../services/api';
import type { HealthCheckResponse } from '../types';

export const HealthStatus: React.FC = () => {
  const [health, setHealth] = useState<HealthCheckResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<string>('');

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await checkHealth();
      setHealth(data);
      setLastChecked(new Date().toLocaleTimeString());
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to connect to backend API';
      setError(errMsg);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000); // Auto-check every 15s
    return () => clearInterval(interval);
  }, []);

  const getStatusClass = (status?: string) => {
    if (status === 'healthy') return 'status-healthy';
    if (status === 'degraded' || (status && status.includes('unhealthy'))) return 'status-unhealthy';
    return 'status-unknown';
  };

  return (
    <div className="health-card">
      <div className="health-header">
        <h3 className="health-title">System Diagnostics</h3>
        <button 
          onClick={fetchHealth} 
          disabled={loading}
          className={`refresh-btn ${loading ? 'loading' : ''}`}
        >
          {loading ? (
            <svg className="spinner" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            </svg>
          ) : 'Check Now'}
        </button>
      </div>

      <div className="status-grid">
        {/* API Status */}
        <div className="status-item">
          <div className="status-label">Backend API</div>
          <div className={`status-badge ${loading ? 'status-checking' : getStatusClass(health?.services.api)}`}>
            {loading ? 'Checking...' : (health?.services.api === 'healthy' ? 'CONNECTED' : 'OFFLINE')}
          </div>
        </div>

        {/* Database Status */}
        <div className="status-item">
          <div className="status-label">PostgreSQL Database</div>
          <div className={`status-badge ${loading ? 'status-checking' : getStatusClass(health?.services.database)}`}>
            {loading ? 'Checking...' : (health?.services.database === 'healthy' ? 'CONNECTED' : 'DISCONNECTED')}
          </div>
        </div>
      </div>

      {error && (
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          <span className="error-text">Connection Error: {error}</span>
        </div>
      )}

      {health?.status === 'degraded' && health.services.database !== 'healthy' && (
        <div className="warning-message">
          <span className="warning-icon">⚠️</span>
          <span className="warning-text">API is running, but database connection failed. Ensure PostgreSQL container is running and initialized.</span>
        </div>
      )}

      <div className="health-footer">
        <div className="last-checked">
          {lastChecked ? `Last sync: ${lastChecked}` : 'Checking system status...'}
        </div>
        <div className="pulse-indicator">
          <span className="pulse-dot"></span>
          <span className="pulse-text">Live Monitoring</span>
        </div>
      </div>
    </div>
  );
};
export default HealthStatus;
