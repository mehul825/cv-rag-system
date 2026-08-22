import React from 'react';

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

interface CVListProps {
  resumes: Resume[];
  selectedId: number | null;
  onSelect: (resume: Resume) => void;
  onDelete: (id: number) => void;
}

export const CVList: React.FC<CVListProps> = ({ resumes, selectedId, onSelect, onDelete }) => {
  
  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString(undefined, { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateString;
    }
  };

  return (
    <div className="cv-list-container">
      <div className="list-header">
        <h3 className="component-title">Indexed Resumes</h3>
        <span className="count-badge">{resumes.length} total</span>
      </div>

      {resumes.length === 0 ? (
        <div className="empty-list-state">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="9" y1="15" x2="15" y2="15"/>
            <line x1="9" y1="19" x2="13" y2="19"/>
            <line x1="9" y1="11" x2="11" y2="11"/>
          </svg>
          <p>No resumes uploaded yet</p>
          <span className="empty-subtext">Upload a PDF CV to start chatting</span>
        </div>
      ) : (
        <div className="resumes-scroll-list">
          {resumes.map((resume) => (
            <div 
              key={resume.id}
              className={`resume-item ${selectedId === resume.id ? 'active' : ''}`}
              onClick={() => onSelect(resume)}
            >
              <div className="resume-item-main">
                <div className="pdf-icon">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                    <polyline points="14 2 14 8 20 8"/>
                  </svg>
                </div>
                <div className="resume-details">
                  <p className="resume-filename" title={resume.filename}>
                    {resume.filename}
                  </p>
                  <div className="resume-meta-row">
                    <p className="resume-date">
                      {formatDate(resume.uploaded_at)}
                    </p>
                    {resume.status && (
                      <span 
                        className={`status-badge-inline ${resume.status}`}
                        title={
                          resume.status === 'failed' && resume.error_message
                            ? `Error: ${resume.error_message}`
                            : `Status: ${resume.status}\nTrace ID: ${resume.trace_id || 'N/A'}\nParsing: ${resume.parsing_duration?.toFixed(2) || 0}s\nExtraction: ${resume.extraction_duration?.toFixed(2) || 0}s\nIndexing: ${resume.indexing_duration?.toFixed(2) || 0}s\nVerification: ${resume.verification_duration?.toFixed(2) || 0}s\nTotal: ${resume.total_duration?.toFixed(2) || 0}s`
                        }
                      >
                        {resume.status.replace('_', ' ')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              <button 
                className="delete-button"
                title="Delete resume and embeddings"
                onClick={(e) => {
                  e.stopPropagation(); // Avoid selecting when deleting
                  if (confirm(`Are you sure you want to delete ${resume.filename}? This will remove all associated index embeddings.`)) {
                    onDelete(resume.id);
                  }
                }}
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  <line x1="10" y1="11" x2="10" y2="17"/>
                  <line x1="14" y1="11" x2="14" y2="17"/>
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
export default CVList;
