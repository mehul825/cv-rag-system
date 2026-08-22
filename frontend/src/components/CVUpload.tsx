import React, { useState, useRef } from 'react';

interface Resume {
  id: number;
  filename: string;
  uploaded_at: string;
}

interface CVUploadProps {
  onUploadSuccess: (resume: Resume) => void;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const CVUpload: React.FC<CVUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      await uploadFile(files[0]);
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await uploadFile(files[0]);
    }
  };

  const uploadFile = async (file: File) => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      setError('Only PDF files are supported.');
      return;
    }

    setIsUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('file', file);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout

    try {
      const response = await fetch(`${API_BASE_URL}/api/cv/upload`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Upload failed' }));
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data: Resume = await response.json();
      onUploadSuccess(data);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      clearTimeout(timeoutId);
      const isAbortError = err instanceof Error && err.name === 'AbortError';
      const errMsg = err instanceof Error ? err.message : 'An error occurred during upload.';
      if (isAbortError) {
        setError('Indexing took too long and timed out. Please try again.');
      } else {
        setError(errMsg);
      }
    } finally {
      setIsUploading(false);
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="cv-upload-container">
      <h3 className="component-title">Upload Resume</h3>
      
      <div 
        className={`drop-zone ${isDragging ? 'dragging' : ''} ${isUploading ? 'uploading' : ''}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={!isUploading ? triggerFileSelect : undefined}
      >
        <input 
          type="file" 
          ref={fileInputRef}
          onChange={handleFileChange}
          accept=".pdf"
          style={{ display: 'none' }}
        />
        
        <div className="drop-zone-content">
          {isUploading ? (
            <>
              <div className="upload-spinner"></div>
              <p className="upload-status-text">Processing and Indexing Resume...</p>
              <p className="upload-substatus-text">Extracting text & generating vector embeddings</p>
            </>
          ) : (
            <>
              <div className="upload-icon-container">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
                </svg>
              </div>
              <p className="upload-main-text">Drag & drop your CV PDF here, or <span className="browse-link">browse</span></p>
              <p className="upload-info-text">Supports PDF format up to 10MB</p>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="error-message">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="18" height="18">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
export default CVUpload;
