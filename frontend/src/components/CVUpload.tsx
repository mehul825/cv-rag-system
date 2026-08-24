import React, { useState, useRef } from 'react';

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

interface CVUploadProps {
  onUploadSuccess: (resume: Resume) => void;
}

interface UploadingFile {
  name: string;
  status: 'Pending' | 'Uploading' | 'Parsing' | 'Indexing' | 'Completed' | 'Failed';
  error?: string;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (typeof window !== 'undefined' && window.location.port === '5173'
    ? 'http://localhost:8000' 
    : (typeof window !== 'undefined' ? window.location.origin : ''));

export const CVUpload: React.FC<CVUploadProps> = ({ onUploadSuccess }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [batchFiles, setBatchFiles] = useState<UploadingFile[]>([]);
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
      await uploadFilesBatch(Array.from(files));
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      await uploadFilesBatch(Array.from(files));
    }
  };

  const uploadFilesBatch = async (files: File[]) => {
    const pdfFiles = files.filter(f => f.name.toLowerCase().endsWith('.pdf'));
    
    if (pdfFiles.length === 0) {
      setError('Please select at least one valid PDF file.');
      return;
    }

    setError(null);
    setIsUploading(true);

    // Set initial file list state with "Uploading" status
    const initialFilesState = files.map(file => ({
      name: file.name,
      status: file.name.toLowerCase().endsWith('.pdf') ? ('Uploading' as const) : ('Failed' as const),
      error: file.name.toLowerCase().endsWith('.pdf') ? undefined : 'Only PDF files are supported.'
    }));
    setBatchFiles(initialFilesState);

    // Prepare Multipart Form Data
    const formData = new FormData();
    pdfFiles.forEach(file => {
      formData.append('files', file);
    });

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000); // 60s timeout for batch

    try {
      // Simulate state transitions on client side for responsive feedback
      setTimeout(() => {
        setBatchFiles(prev => 
          prev.map(f => f.status === 'Uploading' ? { ...f, status: 'Parsing' } : f)
        );
      }, 1500);

      setTimeout(() => {
        setBatchFiles(prev => 
          prev.map(f => f.status === 'Parsing' ? { ...f, status: 'Indexing' } : f)
        );
      }, 4000);

      const response = await fetch(`${API_BASE_URL}/api/cv/upload/batch`, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });
      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Batch upload failed' }));
        throw new Error(errorData.detail || 'Batch upload failed');
      }

      const data = await response.json(); // Array of BatchUploadResult

      // Update state matching result of each file
      setBatchFiles(prev => {
        return prev.map(localFile => {
          const remoteResult = data.find((r: any) => r.filename === localFile.name);
          if (remoteResult) {
            return {
              name: localFile.name,
              status: remoteResult.status === 'completed' ? 'Completed' : 'Failed',
              error: remoteResult.error
            };
          }
          return localFile;
        });
      });

      // Refresh list using the last successful resume entry
      const completed = data.filter((r: any) => r.status === 'completed');
      if (completed.length > 0) {
        const lastSuccess = completed[completed.length - 1];
        onUploadSuccess({
          id: lastSuccess.resume_id,
          filename: lastSuccess.filename,
          uploaded_at: new Date().toISOString()
        });
      }
      
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      clearTimeout(timeoutId);
      const isAbortError = err instanceof Error && err.name === 'AbortError';
      const errMsg = err instanceof Error ? err.message : 'An error occurred during upload.';
      
      setBatchFiles(prev => 
        prev.map(f => f.status !== 'Failed' ? { ...f, status: 'Failed', error: isAbortError ? 'Operation timed out.' : errMsg } : f)
      );
      setError(isAbortError ? 'Batch processing timed out. Please try again with fewer files.' : errMsg);
    } finally {
      setIsUploading(false);
    }
  };

  const triggerFileSelect = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="cv-upload-container">
      <h3 className="component-title">Upload Resumes</h3>
      
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
          multiple
          style={{ display: 'none' }}
        />
        
        <div className="drop-zone-content">
          {isUploading ? (
            <>
              <div className="upload-spinner"></div>
              <p className="upload-status-text">Batch Ingestion Running...</p>
              <p className="upload-substatus-text">Extracting text & generating vector indexes</p>
            </>
          ) : (
            <>
              <div className="upload-icon-container">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
                </svg>
              </div>
              <p className="upload-main-text">Drag & drop CV PDFs here, or <span className="browse-link">browse</span></p>
              <p className="upload-info-text">Supports multiple PDF files up to 10MB each</p>
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

      {batchFiles.length > 0 && (
        <div className="upload-files-list">
          {batchFiles.map((file, idx) => (
            <div key={idx} className={`upload-file-item ${file.status.toLowerCase()}`}>
              <div className="file-item-info">
                <span className="file-name" title={file.name}>{file.name}</span>
                <span className="file-status">{file.status}</span>
              </div>
              {file.error && <p className="file-error-msg">{file.error}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CVUpload;
