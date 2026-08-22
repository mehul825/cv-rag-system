# Gap Analysis: CV RAG & Ingestion System

This document outlines the strict gap analysis comparing the current codebase against the **17 Assignment Requirements**. For each requirement, its status is marked as **COMPLETED**, **PARTIALLY COMPLETED**, or **MISSING**. For any non-completed items, the exact files requiring creation or modification are specified.

---

## Executive Summary Table

| # | Assignment Requirement | Status | Key Files to Change / Create |
| :--- | :--- | :--- | :--- |
| 1 | Gemma 3 4B Instruct on Serverless GPU | **MISSING** | [`config.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/core/config.py), [`openai_service.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/services/openai_service.py), `.env` |
| 2 | CV JSON extraction (fixed & dynamic schema) | **MISSING** | [NEW] `cv_schema.py`, [NEW] `extractor.py`, [`cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py) |
| 3 | Explicit, derived, and inferred CV data | **MISSING** | [NEW] `cv_schema.py`, [NEW] `extractor.py` |
| 4 | JSON validation and correction loop | **MISSING** | [NEW] `extractor.py`, [`requirements.txt`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/requirements.txt) |
| 5 | Multiple CV batch processing & merge logic | **COMPLETED** | [`cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py), [`CVUpload.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVUpload.tsx) |
| 6 | Store extracted structured JSON | **MISSING** | [`resume.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/models/resume.py), [`cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py) |
| 7 | RAG chat with retrieval and citations | **PARTIALLY COMPLETED** | [`openai_service.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/services/openai_service.py), [`cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py), [`CVChat.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVChat.tsx) |
| 8 | Streaming chat responses | **MISSING** | [`openai_service.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/services/openai_service.py), [`cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py), [`CVChat.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVChat.tsx) |
| 9 | JSON View & Formatted CV View in UI | **COMPLETED** | [`CVChat.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVChat.tsx) |
| 10 | Processing statuses (queued, extracting, validated, indexing, rag_ready, failed, degraded) | **MISSING** | [`resume.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/models/resume.py), [`cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py), [`CVList.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVList.tsx) |
| 11 | Request/trace IDs & stage-level timing | **MISSING** | [`resume.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/models/resume.py), [`cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py) |
| 12 | RAG-ready verification check | **MISSING** | [NEW] `verifier.py`, [`cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py) |
| 13 | Benchmark at least 10 CVs (warm path) | **MISSING** | [NEW] `run_benchmark.py` |
| 14 | Percentiles & cold-start latency tracking | **MISSING** | [NEW] `run_benchmark.py` |
| 15 | `samples/` folder (3 sample CVs + expected JSON) | **MISSING** | [NEW] `samples/` directory and contents |
| 16 | `demo/` folder (screenshots or video demo) | **MISSING** | [NEW] `demo/` directory and contents |
| 17 | Comprehensive README updates | **PARTIALLY COMPLETED** | [`README.md`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/README.md) |

---

## Detailed Requirement Analysis

### 1. Gemma 3 4B Instruct deployed on a serverless GPU provider
* **Status**: **MISSING**
* **Current State**: The project is currently configured to route all LLM requests (chat and embedding) locally using an Ollama endpoint (`http://localhost:11434/v1` or `host.docker.internal`). It relies on `llama3.2` (3B) for chat and `nomic-embed-text` for vector embeddings.
* **Gap**: Need to connect to Gemma 3 4B Instruct hosted on a serverless GPU provider (e.g. Hugging Face Inference API, Together AI, Groq, or a serverless container running vLLM such as Modal/RunPod).
* **Exact Files to Change**:
  * [`backend/app/core/config.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/core/config.py): Add configuration variables for the serverless GPU provider API URL, Model name, and API authorization key.
  * [`backend/app/services/openai_service.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/services/openai_service.py): Reconfigure the client initialization logic to route chat completion requests to the serverless provider instead of the local Ollama instance when configured.
  * `backend/.env` & `backend/.env.example`: Expose configuration variables (`SERVERLESS_PROVIDER_URL`, `SERVERLESS_API_KEY`, etc.).

---

### 2. CV JSON extraction with a fixed but dynamic schema
* **Status**: **MISSING**
* **Current State**: The pipeline only parses raw PDF text and splits it into overlapping segments for RAG. No structured parsing or classification of CV sections is conducted.
* **Gap**: Integrate an extraction pipeline that uses Gemma 3 4B Instruct to read raw CV text and output structured JSON conforming to a Pydantic schema (representing sections like contact info, education, history, skills, etc., with dynamic/extendable fields).
* **Exact Files to Change**:
  * **[NEW]** `backend/app/schemas/cv_schema.py`: Create Pydantic models modeling the CV information.
  * **[NEW]** `backend/app/services/extractor.py`: Add an LLM extraction service that formats parsing requests, utilizes structured outputs or JSON mode, and extracts JSON content.
  * [`backend/app/api/cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py): Invoke the extraction service as part of the CV ingestion process.

---

### 3. Explicit, derived, and inferred CV data
* **Status**: **MISSING**
* **Current State**: Since no JSON extraction is performed, classification of information into explicit, derived, and inferred forms is absent.
* **Gap**: Update the schema and extraction logic to categorize the data:
  * *Explicit*: Directly stated data (e.g., candidate name, email, previous employer names, degree title).
  * *Derived*: Calculated information (e.g., total years of work experience, average tenure, time gaps between jobs, count of distinct technologies).
  * *Inferred*: Evaluative/reasoned content (e.g., candidate seniority level, key strengths, soft skills, suitability/role matching score).
* **Exact Files to Change**:
  * **[NEW]** `backend/app/schemas/cv_schema.py`: Structurally define sections for `explicit_data`, `derived_data`, and `inferred_data` inside the target Pydantic schema.
  * **[NEW]** `backend/app/services/extractor.py`: Instruct the LLM in the system prompt to parse explicit fields, calculate derived statistics, and reason about inferred attributes.

---

### 4. JSON validation and correction
* **Status**: **MISSING**
* **Current State**: No structured JSON output exists, and there is no verification or repair logic.
* **Gap**: Build a self-correction loop where the backend validates the raw LLM JSON output against the Pydantic schema. If validation errors occur, it should automatically query the LLM again with the validation traceback or utilize a repair utility (e.g., `json-repair`) to correct the payload.
* **Exact Files to Change**:
  * **[NEW]** `backend/app/services/extractor.py`: Integrate Pydantic validation. Add a retry loop (e.g., up to 3 attempts) that passes the invalid JSON and error logs back to the LLM to get a corrected response.
  * [`backend/requirements.txt`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/requirements.txt): Add helper packages if needed (e.g., `json-repair`).

---

### 5. Multiple CV batch processing and merge logic
* **Status**: **COMPLETED**
* **Current State**: Users can upload multiple PDF resumes simultaneously using both file dialog multi-selection and drag-and-drop.
* **Implementation**:
  * Added `POST /api/cv/upload/batch` endpoint accepting a list of file uploads. Uses nested transaction savepoints so if one file fails, only its changes roll back and the others persist.
  * Added UI elements displaying file name, progress bars, and status transitions (`Uploading` -> `Parsing` -> `Indexing` -> `Completed`/`Failed`).
* **Proven Files**:
  * [`backend/app/api/cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py#L318-L391)
  * [`frontend/src/components/CVUpload.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVUpload.tsx)

---

### 6. Store extracted structured JSON
* **Status**: **MISSING**
* **Current State**: The `Resume` database model only contains `filename` and `parsed_text`.
* **Gap**: Add a column to store the final validated structured JSON object.
* **Exact Files to Change**:
  * [`backend/app/models/resume.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/models/resume.py): Add an `extracted_json` column of type `JSON` or `JSONB` to the `Resume` model.
  * [`backend/app/api/cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py): Write the validated JSON output from the extractor to the database record.

---

### 7. RAG chat with retrieval and citations
* **Status**: **PARTIALLY COMPLETED**
* **Current State**: The RAG retrieval is implemented using in-memory cosine similarity over the chunks of a single selected resume. However, the system does not support returning citation coordinates (e.g., page numbers, source snippet matches, chunk indexes) in the API output or showing them in the UI.
* **Gap**: Modify the LLM prompt to include inline citations (e.g. `[1]`, `[2]`), and return structured citation objects along with the response.
* **Exact Files to Change**:
  * [`backend/app/services/openai_service.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/services/openai_service.py): Instruct the model to cite specific context indexes and output inline citation marks.
  * [`backend/app/api/cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py): Update the `QueryResponse` model to return an array of citations (text snippet, index, similarity score) alongside the textual answer.
  * [`frontend/src/components/CVChat.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVChat.tsx): Update UI bubble renderer to parse the citation brackets and display clickable citation chips that reveal the source snippet.

---

### 8. Streaming chat responses
* **Status**: **MISSING**
* **Current State**: The chat response is resolved synchronously as a blocking JSON object.
* **Gap**: Transition the chat endpoint to a streaming model using Server-Sent Events (SSE).
* **Exact Files to Change**:
  * [`backend/app/services/openai_service.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/services/openai_service.py): Update LLM call to stream chunks using generator syntax.
  * [`backend/app/api/cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py): Implement `/cv/query/stream` endpoint returning a FastAPI `StreamingResponse`.
  * [`frontend/src/components/CVChat.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVChat.tsx): Modify the submit handler to process ReadableStream chunks and update the AI message bubble dynamically.

---

### 9. JSON View and Formatted CV View in the frontend
* **Status**: **COMPLETED**
* **Current State**: The workspace has been upgraded to a tabbed navigation system that dynamically loads the fixed CV extraction.
* **Implementation**:
  1. *RAG Chat*: The interactive context-backed conversation console.
  2. *Structured Profile*: Formatted cards displaying parsed contact information, technical skills tags, work experience timeline, academic history, projects, and certifications.
  3. *Raw JSON*: Pre-formatted JSON codeblock rendering the parsed candidate schema objects with syntax styling.
* **Proven Files**:
  * [`frontend/src/components/CVChat.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVChat.tsx)
  * [`frontend/src/index.css`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/index.css#L1094-L1439)

---

### 10. Processing statuses: queued, extracting, validated, indexing, rag_ready, failed, degraded
* **Status**: **MISSING**
* **Current State**: Uploads are processed synchronously in one block. There is no stage-level status tracking or database tracking of progress.
* **Gap**: Maintain state machine stages (`queued` -> `extracting` -> `validated` -> `indexing` -> `rag_ready`), with error handling transitions to `failed` or `degraded` (e.g., if LLM JSON extraction fails but vector indexing succeeds).
* **Exact Files to Change**:
  * [`backend/app/models/resume.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/models/resume.py): Add `status` (string/enum) and `error_message` fields to the `Resume` model.
  * [`backend/app/api/cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py): offload the ingestion pipeline to background threads/tasks, immediately returning the queued resume. Add polling endpoints.
  * [`frontend/src/components/CVList.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVList.tsx): Render status-colored badges on items in the resume sidebar.
  * [`frontend/src/components/CVUpload.tsx`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/frontend/src/components/CVUpload.tsx): Show details about the active pipeline phase during processing.

---

### 11. Request/trace IDs and stage-level timing
* **Status**: **MISSING**
* **Current State**: Timing metrics are not captured or stored.
* **Gap**: Generate a unique trace ID per CV ingestion run. Measure and persist the execution time (in milliseconds) for each stage (PDF extraction, JSON parsing, validation, embedding generation, verification).
* **Exact Files to Change**:
  * [`backend/app/models/resume.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/models/resume.py): Add columns for `trace_id` and timing fields (`pdf_extract_ms`, `json_extract_ms`, `validation_ms`, `indexing_ms`, `verification_ms`).
  * [`backend/app/api/cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py): Generate UUID, calculate elapsed durations using `time.perf_counter()`, and log timing traces. Return metrics to client.

---

### 12. RAG-ready verification after successful vector indexing and retrieval
* **Status**: **MISSING**
* **Current State**: The system saves embeddings to the DB and assumes the pipeline works without verification checks.
* **Gap**: Add a post-indexing verification step that runs a test semantic query against the newly indexed vector embeddings (e.g. searching for the candidate's name) and checks if the retrieved chunks match. If retrieval fails or returns similarity scores below a threshold, the system flags the status as degraded or failed.
* **Exact Files to Change**:
  * **[NEW]** `backend/app/services/verifier.py`: Create verification service containing query testing logic.
  * [`backend/app/api/cv.py`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/backend/app/api/cv.py): Trigger verification post-indexing and transition status to `rag_ready` upon success.

---

### 13. Benchmark at least 10 CVs with warm-path measurements
* **Status**: **MISSING**
* **Current State**: No benchmarking tools or measurement files are present.
* **Gap**: Write a backend test script that processes at least 10 CVs, discards initial run values to obtain warm-path measurements, and logs metrics.
* **Exact Files to Change**:
  * **[NEW]** `backend/scripts/run_benchmark.py`: Build a benchmarking harness that loads 10 test CVs, pushes them through the API pipeline, and logs all timing variables.

---

### 14. p50, p95, p99, min, max, and cold-start latency
* **Status**: **MISSING**
* **Current State**: No statistics collection or calculation code exists.
* **Gap**: Extend the benchmark script to process the timing outputs and calculate statistical percentiles (p50, p95, p99) along with minimum, maximum, and cold-start (the very first execution cycle) latency figures.
* **Exact Files to Change**:
  * **[NEW]** `backend/scripts/run_benchmark.py`: Integrate statistical analysis methods and generate a summary report.

---

### 15. samples/ folder with 3 sample CVs and expected JSON
* **Status**: **MISSING**
* **Current State**: No `samples/` directory is in the workspace.
* **Gap**: Add a sample directory holding 3 realistic candidate CV PDF files and 3 expected structured JSON files that mirror the schema.
* **Exact Files to Change**:
  * **[NEW]** `samples/cv_1.pdf` and `samples/cv_1_expected.json`
  * **[NEW]** `samples/cv_2.pdf` and `samples/cv_2_expected.json`
  * **[NEW]** `samples/cv_3.pdf` and `samples/cv_3_expected.json`

---

### 16. demo/ folder with screenshots or a short demo video
* **Status**: **MISSING**
* **Current State**: No `demo/` folder is present.
* **Gap**: Create a folder containing application screenshots displaying the new features (UI tab dashboard, status indicators, JSON and Formatted views, citations in chat).
* **Exact Files to Change**:
  * **[NEW]** `demo/` folder holding visual proof of the working RAG console.

---

### 17. README with architecture, serverless provider, cost model, deployment, setup, environment variables, API documentation, and benchmark results
* **Status**: **PARTIALLY COMPLETED**
* **Current State**: The `README.md` documents the project overview, folder layout, and local docker-compose commands.
* **Gap**: Update the documentation to cover:
  1. Serverless GPU architecture setup.
  2. A detailed cost model comparison (cost per CV, cold starts, and hosting alternatives).
  3. API endpoints documentation for batch processing and streaming queries.
  4. Benchmark results table displaying p50, p95, p99, min, max, and cold start durations.
* **Exact Files to Change**:
  * [`README.md`](file:///c:/Users/mehul/Desktop/cv-rag-system-final-assignment/cv-rag-system/README.md): Rewrite sections to include the updated specifications.
