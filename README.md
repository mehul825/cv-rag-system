# CV RAG System

An AI-powered CV/resume analysis, Retrieval-Augmented Generation (RAG) chat, and structured JSON extraction system. This application allows recruiters and hiring managers to upload PDF resumes, parse and index them, and conduct interactive context-backed Q&A chat sessions or extract structured candidate information using the serverless Hugging Face provider running the state-of-the-art **Gemma 3 4B Instruct** model.

---

## 1. Project Overview & Purpose

The CV RAG System is designed to simplify candidate screening and structured resume parsing. During recruitment, parsing unstructured resume data into reliable profiles can be slow and prone to errors.

This project implements a hybrid local-serverless RAG and extraction pipeline:
1. **Document Ingestion & Processing Tracking**: Uploads PDF CVs/resumes (single or batch) and cycles through real database processing states (`queued` $\rightarrow$ `parsing` $\rightarrow$ `extracting` $\rightarrow$ `indexing` $\rightarrow$ `rag_ready` or `failed`).
2. **Document Ingestion**: Extracts raw text from uploaded PDF CVs/resumes using the `pypdf` parsing library.
3. **Text Chunking**: Dynamically segments extracted text into semantic, overlapping blocks.
4. **Local Vectorization**: Generates vector embeddings using the local Ollama instance running the `nomic-embed-text` model.
5. **Vector Storage**: Indexes and stores embeddings in a PostgreSQL database as JSON arrays.
6. **Contextual Retrieval**: Ranks CV chunks using dimension-agnostic cosine similarity calculations computed directly in Python.
7. **Structured Parsing**: Uses the serverless Hugging Face endpoint running **Gemma 3 4B Instruct** to perform JSON extraction (both fixed schemas and dynamic/custom keys).
8. **RAG-Backed Interaction**: Queries **Gemma 3 4B Instruct** on Hugging Face to generate professional, context-bounded answers during interactive chat sessions.

### Serverless GPU Provider Justification

The **Hugging Face Serverless Inference API** was selected as the serverless GPU provider for this project due to several key factors:
- **On-Demand Inference**: It provides serverless execution on remote GPU hardware without requiring persistent GPU instances, meaning there is zero idle cost and high cost-efficiency.
- **Minimal Infrastructure Management**: There is no need to set up, configure, and maintain remote GPU clusters, deploy custom Docker images on serverless container clouds (e.g., RunPod or Modal), or manage scaling policies.
- **Model Availability**: Hugging Face natively hosts and exposes the state-of-the-art **Gemma 3 4B Instruct** model (`google/gemma-3-4b-it`) out of the box through their OpenAI-compatible endpoint.
- **Low-Latency & High Availability**: Requests are routed dynamically to active instances, reducing cold-start times compared to custom container startup models.

---

## 2. Features

*   **Single and Batch PDF CV Upload**: Drag and drop one or multiple resume files. The system processes each CV inside nested transaction savepoints so individual failures do not block the batch queue.
*   **PDF Text Parsing (`pypdf`)**: Direct text extraction from file bytes without needing intermediate disk writes.
*   **Vector Chunking and Embeddings**: Text chunking with 800-character windows and 150-character overlap, paired with local `nomic-embed-text` embeddings.
*   **RAG Chat with Citations**: Context-bounded chat completions showing source citation tooltips containing filename, chunk index, and snippet previews.
*   **Gemma 3 4B Instruct Integration**: Serverless completions for RAG answers, structural extraction, and corrective retry iterations.
*   **JSON Validation and Retry/Correction Loop**: Validation against Pydantic schemas. Invalid outputs are automatically sent back to the LLM with repair prompts up to 2 times.
*   **Explicit, Derived, and Inferred Extraction**:
    *   *Explicit*: Personal info, education, skills, and work history.
    *   *Derived*: Date calculations (years of experience, gap detections, company counts) computed deterministically in Python.
    *   *Inferred*: AI-deduced insights (suitability tags, seniority tier, core strengths) marked with clear warnings.
*   **Structured PostgreSQL Storage/Cache**: Structured extraction results are saved in the `extracted_data` JSON column in PostgreSQL, avoiding redundant LLM costs on page loads.
*   **Real Backend Ingestion Status**: Real-time status reporting (`queued` $\rightarrow$ `parsing` $\rightarrow$ `extracting` $\rightarrow$ `indexing` $\rightarrow$ `rag_ready` or `failed`).
*   **Request/Trace IDs & Stage Timing**: Every ingestion has a unique trace UUID and records durations for parsing, extraction, embedding, verification, and total times.
*   **Post-Indexing RAG-Ready Verification**: Automatically queries the vector index post-indexing to ensure chunks are searchable before promoting status to `rag_ready`.
*   **Resume Listing and Deletion**: Delete CV records along with all associated chunk vector embeddings.
*   **System Health & Diagnostics**: Live REST checks for server status and database connectivity.

---

## 3. Technology Stack

*   **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 (asyncpg driver)
*   **Frontend**: React 18, TypeScript, Vite, Vanilla CSS HSL tokens (TailwindCSS not used)
*   **Database**: PostgreSQL 16
*   **LLM Inference (Chat & Extraction)**: Hugging Face Serverless Inference (`google/gemma-3-4b-it`)
*   **Embedding Engine (Local Vectors)**: Ollama (`nomic-embed-text`)
*   **PDF Parser**: `pypdf`
*   **Orchestration**: Docker, Docker Compose

---

## 4. System Architecture

The following block chart maps the data flow throughout the application:

```
                                  User
                                    ↓
                              React Frontend
                                    ↓
                             FastAPI Backend
                                    ├── PDF Parsing [pypdf]
                                    ├── Text Chunking
                                    ├── Ollama → nomic-embed-text → Embeddings
                                    ├── PostgreSQL → Resume Data / Chunks / Structured JSON
                                    ├── Cosine Similarity → RAG Retrieval
                                    └── Hugging Face → google/gemma-3-4b-it
                                                          ↓
                                                   Answer + Citations
```

---

## 5. Project Structure

```
cv-rag-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── cv.py
│   │   │   └── health.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── database.py
│   │   ├── models/
│   │   │   └── resume.py
│   │   ├── schemas/
│   │   │   └── cv_schema.py
│   │   ├── services/
│   │   │   ├── embeddings.py
│   │   │   ├── extractor.py
│   │   │   ├── openai_service.py
│   │   │   └── pdf_parser.py
│   │   └── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── CVChat.tsx
│   │   │   ├── CVList.tsx
│   │   │   ├── CVUpload.tsx
│   │   │   └── HealthStatus.tsx
│   │   ├── pages/
│   │   │   └── Home.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── Dockerfile
│   └── package.json
└── docker-compose.yml
```

---

## 6. Setup & Running Instructions

### Prerequisites
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
*   [Ollama](https://ollama.com/) installed and running on the host machine.

### Step 1: Set Up Local Embedding Model
In your host command terminal, pull the embeddings model:
```bash
ollama pull nomic-embed-text
```

### Step 2: Configure Environment Variables
Create a `.env` file in the `backend/` folder by copying `.env.example`:
```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` to configure your tokens (placeholders below, do not commit raw tokens):
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

OLLAMA_BASE_URL=http://host.docker.internal:11434/v1
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

HF_TOKEN=your_hugging_face_token_here
HF_MODEL=google/gemma-3-4b-it
```

### Step 3: Run the Application
From the repository root, build and start all containers:
```bash
docker compose up -d --build
```

### Step 4: Access the System
*   **Web Frontend Interface**: `http://localhost:5173`
*   **FastAPI REST API**: `http://localhost:8000`
*   **Swagger API Docs**: `http://localhost:8000/docs`

---

## 7. API Reference Docs

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/health` | Server health and database connection check. |
| **POST** | `/api/cv/upload` | Upload a single CV PDF, run inline extraction, and index. |
| **POST** | `/api/cv/upload/batch` | Upload multiple CVs in a batch queue. |
| **GET** | `/api/cv/list` | Fetch all indexed CVs with status and timing metadata. |
| **DELETE** | `/api/cv/{resume_id}` | Deletes a CV and its chunks from PostgreSQL. |
| **POST** | `/api/cv/query` | RAG-based context Q&A query with citation references. |
| **POST** | `/api/cv/extract/fixed` | Parse direct PDF bytes to fixed template JSON. |
| **POST** | `/api/cv/extract/dynamic` | Parse direct PDF bytes using custom mapping fields. |
| **POST** | `/api/cv/{resume_id}/extract/fixed` | Load database CV text and return fixed schema. |
| **POST** | `/api/cv/{resume_id}/extract/dynamic` | Load database CV text and return dynamic schema. |
| **GET** | `/api/cv/{resume_id}/structured` | Return cached structured profile from the database. |

---

## 8. How to Use the Application

1.  **Ingest CVs**: Drag and drop one or multiple PDF resumes onto the upload panel.
2.  **Monitor Progress**: View real-time parsing, extraction, and indexing status badges. Hover over the badge to view trace UUIDs and timings.
3.  **Conduct RAG Chat**: Select a resume from the list and enter queries (e.g. *"What is the candidate's experience in Python?"*). Read context-bounded answers and hover over source citations.
4.  **View Structured Profiles**: Switch tabs to "Structured Profile" to view explicit details, derived gaps/durations, and inferred AI strengths.
5.  **View Raw JSON**: Check the formatted parsed payload directly under the "Raw JSON" tab.

---

## 9. Submission Folder Structure

The final submission package expects the following folders and files, to be created and populated during packaging:

```
samples/
├── cv_1.pdf
├── cv_1_expected.json
├── cv_2.pdf
├── cv_2_expected.json
├── cv_3.pdf
└── cv_3_expected.json

demo/
├── upload.png
├── structured-profile.png
├── raw-json.png
├── rag-chat.png
└── citations.png
```

---

## 10. Testing & Verification Results

*   **Frontend User Interface**: **PASS**
*   **Backend FastAPI Endpoints**: **PASS**
*   **Single and Batch Uploading**: **PASS**
*   **RAG Citations & Tooltips**: **PASS**
*   **Status Indicators & Timings**: **PASS**
*   **TypeScript Compilation**: `npx tsc --noEmit` $\rightarrow$ **PASS** (0 errors)
*   **Python Syntax Verification**: `python -m compileall app/` $\rightarrow$ **PASS** (0 errors)
*   **Docker Compose Deployment**: **PASS**

---

## 11. Known Limitations

*   **Batch Ingestion Size Limits**: Small batches (tested up to 3 PDFs at once) process successfully. However, large batches (e.g., 8+ files at once) may exceed the API processing timeouts because LLM operations run synchronously.

---

## 12. Assignment Requirement Mapping

| Requirement | Implementation Status | Prove Location (Files/Functions) |
| :--- | :--- | :--- |
| **Gemma 3 4B Instruct Serverless** | **COMPLETED** | `openai_service.py` $\rightarrow$ queries HF model endpoint. |
| **Fixed/Dynamic JSON Extraction** | **COMPLETED** | `extractor.py` $\rightarrow$ schema parser and gemma prompts. |
| **Explicit, Derived, and Inferred Data** | **COMPLETED** | `cv_schema.py` $\rightarrow$ Schema structure; `extractor.py` $\rightarrow$ Python gap calculations. |
| **JSON Validation & Correction Loop** | **COMPLETED** | `extractor.py` $\rightarrow$ validation correction loop (max 2 retries). |
| **Multiple CV Ingestion** | **COMPLETED** | `cv.py` $\rightarrow$ `upload_cvs_batch` batch transaction loop. |
| **Structured JSON Storage** | **COMPLETED** | `resume.py` $\rightarrow$ `extracted_data` JSON column in DB. |
| **RAG Retrieval with Citations** | **COMPLETED** | `openai_service.py` $\rightarrow$ citation queries; `CVChat.tsx` $\rightarrow$ Badges. |
| **Stage-Level Timings & Trace IDs** | **COMPLETED** | `cv.py` $\rightarrow$ `trace_id` and timing calculations in uploader. |
| **Post-Indexing RAG Verification** | **COMPLETED** | `cv.py` $\rightarrow$ RAG checks post-indexing. |
| **Indexed Status Badges** | **COMPLETED** | `CVList.tsx` $\rightarrow$ Displays live DB status and timing tooltips. |
