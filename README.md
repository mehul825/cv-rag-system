# CV RAG System

An AI-powered CV parsing, Retrieval-Augmented Generation (RAG), and candidate readiness pipeline. This application allows recruiters and hiring managers to upload PDF resumes, parse and index them locally, and conduct interactive context-backed Q&A chat sessions entirely on local machines without incurring API costs.

---

## 1. Project Overview & Purpose

The CV RAG System is designed to address privacy, cost, and latency concerns associated with cloud-based LLM platforms. During recruitment, parsing sensitive resume data through paid cloud endpoints can lead to compliance issues and high operational costs.

This project implements a fully local-first RAG pipeline:
1. Document Ingestion: Extracts raw text from uploaded PDF CVs/resumes.
2. Text Chunking: Dynamically segments extracted text into semantic, overlapping blocks.
3. Local Vectorization: Generates vector embeddings using the local model nomic-embed-text.
4. Vector Storage: Indexes and stores embeddings in a PostgreSQL database as JSON arrays.
5. Contextual Retrieval: Ranks CV chunks using dimension-agnostic cosine similarity calculations computed directly in Python.
6. Local LLM Interaction: Queries the local model llama3.2 to generate professional, context-bounded answers.

---

## 2. Main Features

- Local PDF Upload & Processing: Direct-to-app file interface that extracts text content locally in Python.
- Smart Chunking: Splits text into semantic chunks (800 characters, 150 overlap) without dividing words in half.
- Local AI Embedding Engine: Generates embeddings using a local Ollama instance running the nomic-embed-text model.
- Dimension-Agnostic Retrieval: Custom Python-based vector search that supports any embedding size (such as Ollama's 768 dimensions), removing the need for specialized vector plugins like pgvector.
- Context-Bound LLM Chat: An interactive chat terminal powered by llama3.2 that uses only the candidate's resume context to answer questions, preventing hallucinations.
- System Health Diagnostics Panel: Displays live monitoring status of the FastAPI server and the PostgreSQL database.
- Premium Dark Mode UI: A responsive web dashboard styled with glassmorphism, dynamic transitions, and real-time status indicators.

---

## 3. System Architecture

The following diagram illustrates the flow of CV indexing (ingestion) and interactive question answering (retrieval):

```mermaid
graph TD
    %% Ingestion Flow
    subgraph Ingestion Pipeline
        A[PDF CV Upload] --> B[pypdf Text Extraction]
        B --> C[Overlapping Text Chunking]
        C --> D[Ollama nomic-embed-text API]
        D --> E[(PostgreSQL Database JSON Column)]
    end

    %% Query Flow
    subgraph RAG Retrieval & Q&A
        F[User Question] --> G[Ollama nomic-embed-text API]
        G --> H[Python Cosine Similarity Ranker]
        E --> H
        H --> I[Top-5 Context Chunks]
        I --> J[Prompt builder]
        F --> J
        J --> K[Ollama llama3.2 API]
        K --> L[Assistant Answer]
    end

    style E fill:#2e8b57,stroke:#fff,stroke-width:2px;
    style A fill:#4682b4,stroke:#fff,stroke-width:2px;
    style F fill:#4682b4,stroke:#fff,stroke-width:2px;
    style L fill:#d2691e,stroke:#fff,stroke-width:2px;
```

---

## 4. Technologies Used

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| Frontend | React 18, Vite, TypeScript | User dashboard, interactive chat component, file uploads, and state management. |
| Backend | FastAPI, Python 3.11+, Pydantic v2 | High-performance asynchronous API endpoints, validation, and RAG services. |
| Database | PostgreSQL 16 (via SQLAlchemy & asyncpg) | Persistent storage of parsed resumes, metadata, and JSON-indexed chunk embeddings. |
| Orchestration | Docker, Docker Compose | Service encapsulation, networking, volume management, and ease of deployment. |
| Local LLM | Ollama (llama3.2 & nomic-embed-text) | Local vector extraction and retrieval-augmented text generation. |
| RAG Operations | Python (math standard library, numpy) | In-process cosine similarity scoring for semantic search. |

---

## 5. Project Folder Structure

```
cv-rag-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── cv.py                  # API endpoints (upload, list, delete, query)
│   │   ├── core/
│   │   │   ├── config.py              # Configuration & env variable resolution
│   │   │   └── database.py            # SQLAlchemy async database connection
│   │   ├── models/
│   │   │   └── resume.py              # Resume and ResumeChunk DB models
│   │   ├── services/
│   │   │   ├── openai_service.py      # Ollama compatibility endpoint connector
│   │   │   ├── pdf_parser.py          # PDF text extractor and chunker
│   │   │   └── rag_service.py         # Python-based cosine similarity ranker
│   │   └── main.py                    # App entrypoint and startup hooks
│   ├── .env                           # Local environment variables
│   ├── .env.example                   # Backend environment template
│   ├── Dockerfile                     # FastAPI Docker container definition
│   └── requirements.txt               # Backend Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── components/                # Modular UI widgets (CVChat, CVList, CVUpload, HealthStatus)
│   │   ├── pages/
│   │   │   └── Home.tsx               # Main application container dashboard
│   │   ├── services/
│   │   │   └── api.ts                 # Fetch handler for health endpoints
│   │   ├── types/                     # TypeScript interface definitions
│   │   ├── App.tsx                    # Main App wrapper
│   │   └── index.css                  # Modern dark-mode stylesheets
│   ├── Dockerfile                     # Vite/React SPA Docker container definition
│   └── package.json                   # Node dependencies
│
├── docker-compose.yml                 # Main multi-container service orchestrator
├── .env                               # Root DB credentials file shared with compose
├── .env.example                       # Root DB credentials template
└── README.md                          # Project documentation
```

---

## 6. Prerequisites

Ensure you have the following installed on your host environment:
1. Docker Desktop (version 20.10+) and Docker Compose.
2. Ollama (installed and running locally on port 11434).
3. Python 3.11+ (Optional, only needed for local execution outside Docker).
4. Node.js 18+ (Optional, only needed for local execution outside Docker).

---

## 7. Environment Variable Configuration

### Root Environment (.env in root directory)
Defines basic PostgreSQL configuration variables shared with docker-compose.yml:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=cv_rag
```

### Backend Environment (backend/.env in backend folder)
Configures connection parameters and local model endpoints:

**For Docker Compose Setup:**
```env
PROJECT_NAME="CV RAG System API"
APP_ENV=development
DEBUG=true

POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=cv_rag
POSTGRES_HOST=db
POSTGRES_PORT=5432

DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/cv_rag
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Ollama local configuration (connecting to host machine from container)
OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
OLLAMA_CHAT_MODEL=llama3.2
```

**For Native Local Setup (No Docker):**
```env
# Change database host to localhost and Ollama URL to localhost
POSTGRES_HOST=localhost
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/cv_rag
OLLAMA_BASE_URL=http://localhost:11434/v1
```

---

## 8. Ollama Model Setup

Before running the application, you must pull the required embedding and LLM models locally:

```bash
# 1. Download the high-quality 768-dimensional text embedding model
ollama pull nomic-embed-text

# 2. Download the lightweight 3B parameter conversational model
ollama pull llama3.2
```

Verify that both models are downloaded and ready:
```bash
ollama list
```

---

## 9. Running the Application

Follow these steps to run the application locally:

Step 1: Install Ollama
Download and install Ollama from [ollama.com](https://ollama.com/) and ensure the application is running.

Step 2: Pull the required models:
- ollama pull nomic-embed-text
- ollama pull llama3.2

Step 3: Start Docker Desktop
Launch Docker Desktop on your system and verify it is running correctly.

Step 4: Go to the project root
Open a terminal and navigate to the project directory (cv-rag-system).

Step 5: Run:
```bash
docker compose up -d --build
```

Step 6: Open:
- Frontend: http://localhost:5173
- Backend: http://localhost:8000
- Swagger API: http://localhost:8000/docs

### Stopping the Application
To stop the services and remove containers, run:
```bash
docker compose down
```

---

## 10. How to Use the CV RAG System

### Step 1: Upload and Index a CV
1. Open the Frontend interface (http://localhost:5173).
2. Confirm both api and database statuses are green/healthy in the left sidebar diagnostics panel.
3. Click the Upload CV (PDF) card. Select a candidate CV PDF from your file system.
4. The system will extract text, chunk it, send the chunks to the local Ollama embeddings model, and save the metadata and vectors to the PostgreSQL database.
5. The parsed file will now appear in the Indexed CVs list in the sidebar.

### Step 2: Ask Questions / Query the RAG
1. Click on the uploaded resume from the Indexed CVs sidebar. This loads the file as the active RAG workspace query context.
2. In the right pane, the conversational terminal will unlock.
3. Type a question in the input box about the candidate's skills, qualifications, or experience.
4. Hit Enter. The system retrieves relevant chunks using cosine similarity, builds a system prompt, and feeds it locally to llama3.2 to generate a professional summary.

### Example Recruiter Questions:
- "Does this candidate have experience with Python and FastAPI?"
- "Summarize the candidate's work experience at their last job."
- "What is this candidate's educational background and certificates?"
- "Does this resume mention any team leadership or project management roles?"

---

## 11. Troubleshooting & FAQ

#### 1. Connection refused to host.docker.internal inside Docker container
On some systems (specifically Linux hosts), host.docker.internal is not registered in the container DNS by default.
* Resolution: 
  You can run Ollama to listen globally on your host machine by setting the environment variable OLLAMA_HOST=0.0.0.0 before launching the agent. Then, update the OLLAMA_BASE_URL in backend/.env to point to the host machine's actual local network IP (e.g., http://192.168.1.50:11434/v1).

#### 2. High CPU / Slow generation during Q&A
Since models run locally, execution speeds depend on your system's resources (CPU, RAM, GPU).
* Resolution: 
  1. If running on a laptop, connect to a power supply.
  2. If using Docker, allocate additional CPU and RAM resources in Docker Desktop settings.
  3. Close background apps consuming large amounts of RAM/CPU.

#### 3. Error queries in frontend UI
If the UI displays a network query error, verify that the backend container can reach the Ollama service on the host machine, and check the backend container logs using docker compose logs backend.

---

## 12. Project Workflow Summary

```
[PDF Ingestion] ──────> [Chunking] ──────> [Embedding] ──────> [SQL Storage]
(pypdf extract)       (800 char splits)   (nomic-embed)        (Postgres JSON)
                                                                     │
                                                                     ▼
[Response Output] <──── [Local LLM] <───── [Context Match] <──── [Similarity]
(Professional)         (llama3.2)         (Top 5 Chunks)      (Cosine search)
```

---

## 13. Conclusion

The CV RAG System proves that local-first enterprise-level resume processing is not only feasible but highly efficient. By combining the speed of FastAPI, the reliability of PostgreSQL, the modularity of React, and the local intelligence of Ollama, this architecture secures applicant privacy, removes cloud service subscription dependencies, and offers a robust recruitment analysis tool.
