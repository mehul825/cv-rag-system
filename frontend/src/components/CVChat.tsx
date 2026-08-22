import React, { useState, useEffect, useRef } from 'react';

interface Resume {
  id: number;
  filename: string;
  uploaded_at: string;
}

interface Message {
  id: string;
  sender: 'user' | 'system' | 'assistant';
  text: string;
  timestamp: Date;
}

interface CVChatProps {
  selectedResume: Resume | null;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const CVChat: React.FC<CVChatProps> = ({ selectedResume }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of chat when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Clear chat history when user switches resumes
  useEffect(() => {
    if (selectedResume) {
      setMessages([
        {
          id: 'welcome',
          sender: 'system',
          text: `You have loaded "${selectedResume.filename}". Ask me any questions regarding their experience, education, projects, or skill set.`,
          timestamp: new Date()
        }
      ]);
    } else {
      setMessages([]);
    }
  }, [selectedResume]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !selectedResume || isLoading) return;

    const userMessageText = inputValue.trim();
    setInputValue('');

    // 1. Add user message to state
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: userMessageText,
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // 2. Call the RAG Query endpoint
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
      
      // 3. Add AI response to state
      const assistantMessage: Message = {
        id: `ai-${Date.now()}`,
        sender: 'assistant',
        text: data.answer,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to query CV.';
      // Add a system error message to the log
      const errSystemMsg: Message = {
        id: `err-${Date.now()}`,
        sender: 'system',
        text: `Error: ${errMsg} Please make sure your OpenAI API key is valid.`,
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
          <h4>Interactive Q&A Session</h4>
          <p>Select an indexed CV from the left sidebar to start asking questions using Retrieval-Augmented Generation.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="cv-chat-container">
      <div className="chat-header">
        <div className="chat-header-info">
          <div className="active-dot"></div>
          <h4>Query Context: {selectedResume.filename}</h4>
        </div>
        <div className="rag-badge">RAG Active</div>
      </div>

      <div className="chat-messages-area">
        {messages.map((msg) => (
          <div key={msg.id} className={`message-bubble-wrapper ${msg.sender}`}>
            {msg.sender === 'assistant' && (
              <div className="avatar assistant-avatar">AI</div>
            )}
            <div className={`message-bubble ${msg.sender}`}>
              <p className="message-text">{msg.text}</p>
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
        
        <div ref={chatEndRef} />
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
    </div>
  );
};
export default CVChat;
