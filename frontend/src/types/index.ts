export interface ServiceStatus {
  api: string;
  database: string;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded';
  services: ServiceStatus;
}
