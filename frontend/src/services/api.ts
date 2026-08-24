import type { HealthCheckResponse } from '../types';

let rawApiUrl = import.meta.env.VITE_API_URL || '';
if (!rawApiUrl || rawApiUrl.includes('YOUR-CURRENT-RAILWAY-DOMAIN')) {
  rawApiUrl = typeof window !== 'undefined' && window.location.port === '5173'
    ? 'http://localhost:8000'
    : 'https://cv-rag-system-production.up.railway.app';
}
export const API_BASE_URL = rawApiUrl;

export async function checkHealth(): Promise<HealthCheckResponse> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`API health check failed with status: ${response.status}`);
  }
  return response.json();
}
