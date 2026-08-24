import React, { useState, useEffect } from 'react';
import HealthStatus from '../components/HealthStatus';
import CVUpload from '../components/CVUpload';
import CVList from '../components/CVList';
import CVChat from '../components/CVChat';

interface Resume {
  id: number;
  filename: string;
  uploaded_at: string;
  status?: 'queued' | 'parsing' | 'extracting' | 'indexing' | 'rag_ready' | 'failed';
  error_message?: string;
  trace_id?: string;
  parsing_duration?: number;
  extraction_duration?: number;
  indexing_duration?: number;
  verification_duration?: number;
  total_duration?: number;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (typeof window !== 'undefined' && window.location.port === '5173'
    ? 'http://localhost:8000' 
    : 'https://cv-rag-system-production.up.railway.app');

export const Home: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Retrieve existing resumes on load
  const fetchResumes = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/cv/list`);
      if (!response.ok) {
        throw new Error('Failed to load indexed CVs list');
      }
      const data = await response.json();
      setResumes(data);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Error loading resumes';
      setError(errMsg);
    }
  };

  useEffect(() => {
    fetchResumes();
  }, []);

  const handleUploadSuccess = (newResume: Resume) => {
    fetchResumes(); // Fetch list to get latest state from database
    setSelectedResume(newResume); // Automatically select newly uploaded resume
  };

  const handleDelete = async (id: number) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/cv/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        throw new Error('Failed to delete resume');
      }
      // Remove from list
      setResumes(prev => prev.filter(r => r.id !== id));
      // Reset selected if active
      if (selectedResume?.id === id) {
        setSelectedResume(null);
      }
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'An error occurred while deleting.';
      alert(errMsg);
    }
  };

  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <div className="header-badge">v1.1.0 (RAG Active)</div>
        <h1 className="dashboard-title">
          CV RAG System
        </h1>
        <p className="dashboard-subtitle">
          AI-Powered CV Parsing, Retrieval-Augmented Generation & 5-Second Readiness Pipeline
        </p>
      </header>

      <main className="dashboard-main-layout">
        {/* Sidebar Controls */}
        <div className="layout-sidebar">
          {/* Diagnostics Section */}
          <section className="diagnostics-section">
            <HealthStatus />
          </section>
          
          {/* CV Upload */}
          <CVUpload onUploadSuccess={handleUploadSuccess} />
          
          {/* Indexed CV List */}
          {error ? (
            <div className="error-message">
              <span>{error}</span>
              <button onClick={fetchResumes} className="refresh-btn">Retry</button>
            </div>
          ) : (
            <CVList 
              resumes={resumes}
              selectedId={selectedResume?.id || null}
              onSelect={setSelectedResume}
              onDelete={handleDelete}
            />
          )}
        </div>

        {/* RAG Workspace */}
        <div className="layout-workspace">
          <CVChat selectedResume={selectedResume} />
        </div>
      </main>

      <footer className="dashboard-footer-bar">
        <p>© 2026 CV RAG System. Built with FastAPI, PostgreSQL, React, and TypeScript.</p>
      </footer>
    </div>
  );
};

export default Home;
