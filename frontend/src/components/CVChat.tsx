import React, { useState, useEffect, useRef } from 'react';
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

interface Citation {
  resume_id: number;
  filename: string;
  chunk_index: number;
  text_snippet: string;
}

interface Message {
  id: string;
  sender: 'user' | 'system' | 'assistant';
  text: string;
  timestamp: Date;
  citations?: Citation[];
}

interface CVChatProps {
  selectedResume: Resume | null;
}



export const CVChat: React.FC<CVChatProps> = ({ selectedResume }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'profile' | 'json'>('chat');

  // Structured extraction states
  const [extractedProfile, setExtractedProfile] = useState<any>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractionError, setExtractionError] = useState<string | null>(null);
  
  const chatContainerRef = useRef<HTMLDivElement>(null);

  // Helper to scroll to the bottom of the chat container
  const scrollToBottom = (force = false) => {
    const container = chatContainerRef.current;
    if (!container) return;
    
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 200;
    if (force || isNearBottom) {
      requestAnimationFrame(() => {
        container.scrollTo({
          top: container.scrollHeight,
          behavior: 'smooth'
        });
      });
    }
  };

  // Trigger scroll to bottom on new messages or loading state transitions
  useEffect(() => {
    if (activeTab === 'chat' && messages.length > 0) {
      const lastMsg = messages[messages.length - 1];
      const isUserMsg = lastMsg && lastMsg.sender === 'user';
      scrollToBottom(isUserMsg || isLoading);
    }
  }, [messages, isLoading, activeTab]);

  // Fetch structured profile data
  const fetchProfileData = async () => {
    if (!selectedResume || selectedResume.status !== 'rag_ready') return;
    setIsExtracting(true);
    setExtractionError(null);
    try {
      const response = await fetch(`${API_BASE_URL}/api/cv/${selectedResume.id}/extract/fixed`, {
        method: 'POST'
      });
      if (!response.ok) {
        throw new Error('Failed to load structured CV extraction data.');
      }
      const data = await response.json();
      setExtractedProfile(data);
    } catch (err) {
      setExtractionError(err instanceof Error ? err.message : 'Failed to extract structured CV data.');
    } finally {
      setIsExtracting(false);
    }
  };

  // Handle switching resumes
  useEffect(() => {
    if (selectedResume) {
      // Only reset messages if we're switching to a completely different CV
      // to avoid resetting the chat history when the status of the current CV updates
      setMessages(prev => {
        const welcomeMessageExists = prev.some(m => m.id === 'welcome');
        if (welcomeMessageExists && prev[0]?.text.includes(selectedResume.filename)) {
          return prev;
        }
        return [
          {
            id: 'welcome',
            sender: 'system',
            text: `You have loaded "${selectedResume.filename}". Ask me any questions regarding their experience, education, projects, or skill set.`,
            timestamp: new Date()
          }
        ];
      });
      
      setActiveTab('chat');
      setExtractedProfile(null);
      setExtractionError(null);
      
      if (selectedResume.status === 'rag_ready') {
        fetchProfileData();
      }
    } else {
      setMessages([]);
      setExtractedProfile(null);
    }
  }, [selectedResume]);

  // Scroll to bottom when user switches back to Chat tab
  useEffect(() => {
    if (activeTab === 'chat') {
      scrollToBottom(true);
    }
  }, [activeTab]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !selectedResume || isLoading) return;

    const userMessageText = inputValue.trim();
    setInputValue('');

    // Add user message to state
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: userMessageText,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Call the RAG Query endpoint
      const response = await fetch(`${API_BASE_URL}/api/cv/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          resume_id: selectedResume.id,
          question: userMessageText
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to query CV' }));
        throw new Error(errorData.detail || 'Failed to get an answer.');
      }

      const data = await response.json();
      
      // Add AI response with citations to state
      const assistantMessage: Message = {
        id: `ai-${Date.now()}`,
        sender: 'assistant',
        text: data.answer,
        timestamp: new Date(),
        citations: data.citations || []
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to query CV.';
      const errSystemMsg: Message = {
        id: `err-${Date.now()}`,
        sender: 'system',
        text: `Error: ${errMsg} Please make sure your Hugging Face API token is valid.`,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errSystemMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!selectedResume) {
    return (
      <div className="cv-chat-placeholder">
        <div className="placeholder-content">
          <div className="chat-placeholder-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
          </div>
          <h4>Interactive Candidate Analyzer</h4>
          <p>Select an indexed CV from the left sidebar to start asking questions or viewing extracted candidate data.</p>
        </div>
      </div>
    );
  }

  if (selectedResume.status && selectedResume.status !== 'rag_ready') {
    if (selectedResume.status === 'failed') {
      return (
        <div className="cv-chat-placeholder">
          <div className="placeholder-content">
            <div className="chat-placeholder-icon" style={{ color: '#f43f5e', background: 'rgba(244, 63, 94, 0.05)' }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="12" r="10"/>
                <line x1="12" y1="8" x2="12" y2="12"/>
                <line x1="12" y1="16" x2="12.01" y2="16"/>
              </svg>
            </div>
            <h4 style={{ color: '#fda4af' }}>CV Ingestion Failed</h4>
            <p style={{ color: 'var(--text-secondary)' }}>
              {selectedResume.error_message || 'An unknown error occurred during CV processing.'}
            </p>
          </div>
        </div>
      );
    }

    return (
      <div className="cv-chat-placeholder">
        <div className="placeholder-content">
          <div className="status-spinner-container" style={{ marginBottom: '1.5rem' }}>
            <div className="upload-spinner"></div>
          </div>
          <h4>Ingesting & Indexing CV...</h4>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '0.25rem' }}>
            Current step: <strong style={{ textTransform: 'capitalize', color: '#a5b4fc' }}>{selectedResume.status.replace('_', ' ')}</strong>
          </p>
          <p style={{ fontSize: '0.8rem', opacity: 0.7, color: 'var(--text-muted)', maxWidth: '300px' }}>
            Please wait while the AI extracts details, generates vector embeddings, and verifies RAG readiness.
          </p>
        </div>
      </div>
    );
  }

  const renderProfileTab = () => {
    if (isExtracting) {
      return (
        <div className="extraction-status-container">
          <div className="status-spinner-container">
            <div className="upload-spinner"></div>
          </div>
          <h4>Analyzing & Structuring CV Data...</h4>
          <p>Extracting schema fields using Gemma 3 4B Instruct.</p>
        </div>
      );
    }

    if (extractionError) {
      return (
        <div className="extraction-error-container">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="48" height="48" className="error-icon">
            <circle cx="12" cy="12" r="10"/>
            <line x1="12" y1="8" x2="12" y2="12"/>
            <line x1="12" y1="16" x2="12.01" y2="16"/>
          </svg>
          <h4>Structured Extraction Failed</h4>
          <p>{extractionError}</p>
          <button onClick={fetchProfileData} className="retry-btn">
            Retry Extraction
          </button>
        </div>
      );
    }

    if (!extractedProfile) {
      return (
        <div className="extraction-empty-container">
          <p>No structured data extracted.</p>
        </div>
      );
    }

    // Support backward compatibility for legacy extractions
    const explicit = extractedProfile.explicit_data || {
      personal_info: extractedProfile.personal_info,
      skills: extractedProfile.skills || [],
      education: extractedProfile.education || [],
      experience: extractedProfile.experience || [],
      projects: extractedProfile.projects || [],
      certifications: extractedProfile.certifications || []
    };

    const derived = extractedProfile.derived_data || {
      total_years_experience: 0,
      employment_gaps: [],
      number_of_companies: 0,
      skill_count: explicit.skills?.length || 0,
      duration_calculations: []
    };

    const inferred = extractedProfile.inferred_data || {
      seniority_level: 'Unspecified',
      candidate_strengths: [],
      suitable_job_roles: [],
      possible_areas_of_expertise: [],
      ai_label: 'AI-Generated Inference'
    };

    const { personal_info, skills, education, experience, projects, certifications } = explicit;

    return (
      <div className="profile-tab-content">
        
        {/* DERIVED DATA SECTION */}
        <div className="profile-section-card">
          <h4 className="section-title">Derived Metrics (Deterministic)</h4>
          <div className="derived-metrics-grid">
            <div className="metric-stat-card">
              <span className="metric-value">{derived.total_years_experience}</span>
              <span className="metric-title">Years Experience</span>
            </div>
            <div className="metric-stat-card">
              <span className="metric-value">{derived.number_of_companies}</span>
              <span className="metric-title">Companies</span>
            </div>
            <div className="metric-stat-card">
              <span className="metric-value">{derived.skill_count}</span>
              <span className="metric-title">Skills Found</span>
            </div>
          </div>
          
          {derived.employment_gaps && derived.employment_gaps.length > 0 && (
            <div className="gap-alerts-list">
              {derived.employment_gaps.map((gap: string, idx: number) => (
                <div key={idx} className="gap-alert-banner">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" width="16" height="16">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                  <span>{gap}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* INFERRED DATA SECTION */}
        <div className="profile-section-card inferred-insights-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '0.5rem' }}>
            <h4 className="section-title" style={{ border: 'none', margin: 0, padding: 0 }}>AI-Inferred Insights</h4>
            <span className="ai-disclaimer-tag">{inferred.ai_label}</span>
          </div>

          <div className="insight-item-grid">
            <div className="insight-item-group">
              <span className="insight-label">Seniority Estimate</span>
              <span className="insight-value-tag">{inferred.seniority_level || 'N/A'}</span>
            </div>
            {inferred.suitable_job_roles && inferred.suitable_job_roles.length > 0 && (
              <div className="insight-item-group">
                <span className="insight-label">Suitable Job Roles</span>
                <div className="tech-tags mini" style={{ marginTop: '0.2rem' }}>
                  {inferred.suitable_job_roles.map((role: string, idx: number) => (
                    <span key={idx} className="tech-tag" style={{ color: '#34d399', borderColor: 'rgba(16, 185, 129, 0.2)' }}>{role}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {inferred.candidate_strengths && inferred.candidate_strengths.length > 0 && (
            <div style={{ marginTop: '1.25rem' }}>
              <span className="insight-label" style={{ display: 'block', marginBottom: '0.5rem' }}>Core Candidate Strengths</span>
              <ul className="insight-bullets-list">
                {inferred.candidate_strengths.map((str: string, idx: number) => (
                  <li key={idx}>{str}</li>
                ))}
              </ul>
            </div>
          )}

          {inferred.possible_areas_of_expertise && inferred.possible_areas_of_expertise.length > 0 && (
            <div style={{ marginTop: '1.25rem' }}>
              <span className="insight-label" style={{ display: 'block', marginBottom: '0.4rem' }}>Possible Focus/Expertise Areas</span>
              <div className="tech-tags mini">
                {inferred.possible_areas_of_expertise.map((exp: string, idx: number) => (
                  <span key={idx} className="tech-tag skill-tag">{exp}</span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* EXPLICIT DATA - Personal Details */}
        <div className="profile-section-card">
          <h4 className="section-title">Explicit Personal Details</h4>
          <div className="personal-info-grid">
            <div className="info-item">
              <span className="info-label">Name</span>
              <span className="info-value">{personal_info?.name || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Email</span>
              <span className="info-value">{personal_info?.email || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Phone</span>
              <span className="info-value">{personal_info?.phone || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="info-label">Location</span>
              <span className="info-value">{personal_info?.location || 'N/A'}</span>
            </div>
            {personal_info?.linkedin && (
              <div className="info-item full-width">
                <span className="info-label">LinkedIn</span>
                <span className="info-value">
                  <a href={personal_info.linkedin} target="_blank" rel="noopener noreferrer" className="profile-link">
                    {personal_info.linkedin}
                  </a>
                </span>
              </div>
            )}
          </div>
        </div>

        {/* EXPLICIT DATA - Skills */}
        <div className="profile-section-card">
          <h4 className="section-title">Explicit Technical & Professional Skills</h4>
          {skills && skills.length > 0 ? (
            <div className="tech-tags">
              {skills.map((skill: string, idx: number) => (
                <span key={idx} className="tech-tag skill-tag">{skill}</span>
              ))}
            </div>
          ) : (
            <p className="no-data-msg">No skills listed.</p>
          )}
        </div>

        {/* EXPLICIT DATA - Experience */}
        <div className="profile-section-card">
          <h4 className="section-title">Explicit Work Experience</h4>
          {experience && experience.length > 0 ? (
            <div className="timeline-list">
              {experience.map((exp: any, idx: number) => {
                const durationDetail = derived.duration_calculations?.find((d: any) => d.company?.toLowerCase() === exp.company?.toLowerCase());
                const months = durationDetail?.duration_months || 0;
                const durationLabel = months > 0 
                  ? ` (${Math.floor(months / 12) > 0 ? `${Math.floor(months / 12)}y ` : ''}${months % 12}m)`
                  : '';
                return (
                  <div key={idx} className="timeline-item">
                    <div className="timeline-header">
                      <h5 className="role-title">{exp.role || 'Role N/A'}</h5>
                      <span className="duration-badge">{exp.start_date || 'N/A'} - {exp.end_date || 'N/A'}{durationLabel}</span>
                    </div>
                    <p className="company-title">{exp.company || 'Company N/A'}</p>
                    {exp.description && <p className="job-desc">{exp.description}</p>}
                    {exp.technologies && exp.technologies.length > 0 && (
                      <div className="tech-tags mini">
                        {exp.technologies.map((tech: string, tIdx: number) => (
                          <span key={tIdx} className="tech-tag">{tech}</span>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="no-data-msg">No work experience listed.</p>
          )}
        </div>

        {/* EXPLICIT DATA - Education */}
        <div className="profile-section-card">
          <h4 className="section-title">Explicit Education History</h4>
          {education && education.length > 0 ? (
            <div className="timeline-list">
              {education.map((edu: any, idx: number) => (
                <div key={idx} className="timeline-item">
                  <div className="timeline-header">
                    <h5 className="degree-title">{edu.degree || 'Degree N/A'} {edu.field_of_study ? `in ${edu.field_of_study}` : ''}</h5>
                    <span className="duration-badge">{edu.start_date || 'N/A'} - {edu.end_date || 'N/A'}</span>
                  </div>
                  <p className="school-title">{edu.school || 'School N/A'}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="no-data-msg">No education listed.</p>
          )}
        </div>

        {/* EXPLICIT DATA - Projects */}
        <div className="profile-section-card">
          <h4 className="section-title">Explicit Featured Projects</h4>
          {projects && projects.length > 0 ? (
            <div className="projects-grid">
              {projects.map((proj: any, idx: number) => (
                <div key={idx} className="project-item-card">
                  <h5 className="project-title">{proj.title || 'Project'}</h5>
                  {proj.description && <p className="project-desc">{proj.description}</p>}
                  {proj.technologies && proj.technologies.length > 0 && (
                    <div className="tech-tags mini">
                      {proj.technologies.map((tech: string, tIdx: number) => (
                        <span key={tIdx} className="tech-tag">{tech}</span>
                      ))}
                    </div>
                  )}
                  {proj.link && (
                    <a href={proj.link} target="_blank" rel="noopener noreferrer" className="project-link-btn">
                      View Project Source &rarr;
                    </a>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="no-data-msg">No project details listed.</p>
          )}
        </div>

        {/* EXPLICIT DATA - Certifications */}
        <div className="profile-section-card">
          <h4 className="section-title">Explicit Certifications & Courses</h4>
          {certifications && certifications.length > 0 ? (
            <div className="tech-tags">
              {certifications.map((cert: string, idx: number) => (
                <span key={idx} className="tech-tag cert-tag">{cert}</span>
              ))}
            </div>
          ) : (
            <p className="no-data-msg">No certifications listed.</p>
          )}
        </div>
      </div>
    );
  };

  const renderJSONTab = () => {
    if (isExtracting) {
      return (
        <div className="extraction-status-container">
          <div className="status-spinner-container">
            <div className="upload-spinner"></div>
          </div>
          <h4>Retrieving raw JSON details...</h4>
        </div>
      );
    }

    if (extractionError) {
      return (
        <div className="extraction-error-container">
          <h4>Failed to render JSON</h4>
          <p>{extractionError}</p>
        </div>
      );
    }

    return (
      <div className="json-tab-content">
        <pre className="json-code-block">
          <code>{JSON.stringify(extractedProfile || {}, null, 2)}</code>
        </pre>
      </div>
    );
  };

  return (
    <div className="cv-chat-container">
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="active-dot"></div>
          <h4>{selectedResume.filename}</h4>
        </div>
        <div className="tab-buttons">
          <button 
            className={`tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            RAG Chat
          </button>
          <button 
            className={`tab-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            Structured Profile
          </button>
          <button 
            className={`tab-btn ${activeTab === 'json' ? 'active' : ''}`}
            onClick={() => setActiveTab('json')}
          >
            Raw JSON
          </button>
        </div>
      </div>

      {activeTab === 'chat' ? (
        <>
          <div className="chat-messages-area" ref={chatContainerRef}>
            {messages.map((msg) => (
              <div key={msg.id} className={`message-bubble-wrapper ${msg.sender}`}>
                {msg.sender === 'assistant' && (
                  <div className="avatar assistant-avatar">AI</div>
                )}
                <div className={`message-bubble ${msg.sender}`}>
                  <p className="message-text">{msg.text}</p>
                  
                  {/* Sources Citations list */}
                  {msg.citations && msg.citations.length > 0 && (
                    <div className="citations-container">
                      <div className="citations-header">Sources Cited:</div>
                      <div className="citations-list">
                        {msg.citations.map((cite, idx) => (
                          <div key={idx} className="citation-badge" title={cite.text_snippet}>
                            [{idx + 1}] {cite.filename} (Chunk #{cite.chunk_index})
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <span className="message-time">
                    {msg.timestamp.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                {msg.sender === 'user' && (
                  <div className="avatar user-avatar">ME</div>
                )}
              </div>
            ))}
            
            {isLoading && (
              <div className="message-bubble-wrapper assistant">
                <div className="avatar assistant-avatar">AI</div>
                <div className="message-bubble assistant loading">
                  <div className="typing-skeleton">
                    <span className="dot"></span>
                    <span className="dot"></span>
                    <span className="dot"></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <form className="chat-input-form" onSubmit={handleSend}>
            <input 
              type="text" 
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder={`Ask about ${selectedResume.filename}...`}
              disabled={isLoading}
              className="chat-text-input"
            />
            <button 
              type="submit" 
              disabled={!inputValue.trim() || isLoading}
              className="chat-send-btn"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="22" y1="2" x2="11" y2="13"/>
                <polygon points="22 2 15 22 11 13 2 9 22 2"/>
              </svg>
            </button>
          </form>
        </>
      ) : activeTab === 'profile' ? (
        renderProfileTab()
      ) : (
        renderJSONTab()
      )}
    </div>
  );
};

export default CVChat;
