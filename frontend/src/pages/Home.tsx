import React, { useState, useEffect } from 'react';
import HealthStatus from '../components/HealthStatus';
import CVUpload from '../components/CVUpload';
import CVList from '../components/CVList';
import CVChat from '../components/CVChat';
import { API_BASE_URL } from '../services/api';


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



export const Home: React.FC = () => {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [selectedResume, setSelectedResume] = useState<Resume | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);

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

  // Poll CV status while uploading or while any resume is processing
  useEffect(() => {
    const hasProcessing = resumes.some(
      r => r.status && ['queued', 'parsing', 'extracting', 'indexing'].includes(r.status)
    );

    if (isUploading || hasProcessing) {
      const interval = setInterval(() => {
        fetchResumes();
      }, 3000);
      return () => clearInterval(interval);
    }
  }, [isUploading, resumes]);

  // Synchronize selectedResume whenever resumes list updates
  useEffect(() => {
    if (selectedResume) {
      const updated = resumes.find(r => r.id === selectedResume.id);
      if (updated && (
        updated.status !== selectedResume.status || 
        updated.error_message !== selectedResume.error_message ||
        updated.total_duration !== selectedResume.total_duration
      )) {
        setSelectedResume(updated);
      }
    }
  }, [resumes, selectedResume]);

  const handleUploadStart = () => {
    setIsUploading(true);
    // Fetch immediately to register the new resume in the list as queued/parsing
    setTimeout(() => fetchResumes(), 500);
    setTimeout(() => fetchResumes(), 1500);
  };

  const handleUploadComplete = () => {
    setIsUploading(false);
    fetchResumes();
  };

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
          <CVUpload 
            onUploadSuccess={handleUploadSuccess} 
            onUploadStart={handleUploadStart}
            onUploadComplete={handleUploadComplete}
          />
          
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
