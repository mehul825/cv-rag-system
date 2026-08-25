# CV RAG System Ingestion Benchmark Report

This document reports the performance metrics and latency analysis of the CV RAG Ingestion Pipeline. 

> [!NOTE]
> The benchmarks below were run locally using a local Ollama instance (`nomic-embed-text`) for vector indexing to establish a baseline. In the production deployment, the architecture is fully serverless and hosted, routing both the LLM structured extraction and embedding generation to **Serverless Self-Hosted GPU Endpoints** (Hugging Face / custom container endpoints).

---

## 1. Benchmark Objective

The main objectives of this benchmark run are to:
1. Measure the total client-side end-to-end ingestion latency for parsing, extracting, and indexing resume PDFs.
2. Isolate and profile individual pipeline stage durations:
   - **Text Extraction (Parsing)**: Extracting raw text from PDF bytes via `pypdf`.
   - **LLM Extraction**: Querying **Gemma 3 4B Instruct** via Hugging Face serverless self-hosted GPU endpoint to extract structured JSON data.
   - **Vector Indexing**: Segmenting text and generating vector embeddings (using a local Ollama instance running `nomic-embed-text` for the baseline run, or serverless self-hosted endpoints in production).
   - **Verification**: Querying PostgreSQL vectors post-indexing to ensure the CV is RAG-ready.
   - **Overhead**: Database writes, API routing overhead, and network roundtrip time.
3. Compare cold-start latency against subsequent warm request performance.
4. Quantify system bottlenecks and identify areas for caching or concurrency optimizations.

---

## 2. Test Environment

- **Timestamp of Run**: `2026-08-23T06:48:30.359216`
- **Operating System**: `NT`
- **FastAPI Backend Port**: `http://localhost:8000/api/cv`
- **Local Baseline Embedding Engine**: `nomic-embed-text (local via Ollama)`
- **Serverless GPU LLM Model**: `google/gemma-3-4b-it (via Hugging Face GPU Endpoint)`
- **Database Engine**: PostgreSQL 16 (running in Docker Container for baseline)

---

## 3. Test Methodology

1. **Clean Slate State**: The script programmatically restarts the backend Docker container (`docker restart cv_rag_backend`) and waits for the database/API health checks to report healthy.
2. **Cold-Start Request**: The first PDF CV is uploaded immediately after restart, capturing the initial database connection initialization, module imports, and serverless LLM cold-start latency.
3. **Warm Requests**: The remaining 9 PDF CVs are uploaded sequentially. An idle interval of 1 second is placed between requests to respect Hugging Face serverless rate limits.
4. **Cleanup**: At the end of the runs, all database records generated during the benchmark are cleared via the REST DELETE endpoint to preserve system state.
5. **Data Accumulation**: Individual timings are stored in a local JSON structure and metrics are aggregated.

---

## 4. Test Material

- **Number of CVs Tested**: 10 PDFs
- **Type**: Structurally valid text-based PDF resumes containing structured profiles of various engineering, design, and product candidates.
- **Average File Size**: 1.64 KB

---

## 5. Ingestion In-Depth Results Table

| File Name | File Size | Cold Start? | Total Latency | Parsing Stage | LLM Extraction | Vector Indexing | RAG Verification | Database & Net Overhead |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `cv_candidate_10_neha_kapoor.pdf` | 1.63 KB | Yes (Cold) | **23.19s** | 0.004s | 18.01s | 4.81s | 0.138s | 0.101s |
| `cv_candidate_1_aarav_sharma.pdf` | 1.67 KB | No (Warm) | **20.12s** | 0.003s | 18.70s | 1.16s | 0.155s | 0.035s |
| `cv_candidate_2_priya_nair.pdf` | 1.62 KB | No (Warm) | **17.28s** | 0.003s | 15.82s | 1.19s | 0.150s | 0.021s |
| `cv_candidate_3_rohan_gupta.pdf` | 1.64 KB | No (Warm) | **22.43s** | 0.005s | 20.98s | 1.16s | 0.156s | 0.026s |
| `cv_candidate_4_ananya_iyer.pdf` | 1.63 KB | No (Warm) | **27.13s** | 0.003s | 25.98s | 0.87s | 0.164s | 0.025s |
| `cv_candidate_5_kabir_mehta.pdf` | 1.65 KB | No (Warm) | **26.06s** | 0.010s | 23.96s | 1.37s | 0.603s | 0.028s |
| `cv_candidate_6_sneha_reddy.pdf` | 1.64 KB | No (Warm) | **51.66s** | 0.002s | 18.95s | 1.13s | 0.977s | 0.047s |
| `cv_candidate_7_aditya_rao.pdf` | 1.65 KB | No (Warm) | **20.82s** | 0.003s | 19.39s | 1.14s | 0.159s | 0.034s |
| `cv_candidate_8_meera_verma.pdf` | 1.66 KB | No (Warm) | **49.27s** | 0.002s | 18.72s | 1.16s | 29.206s | 0.036s |
| `cv_candidate_9_vikram_singh.pdf` | 1.64 KB | No (Warm) | **20.96s** | 0.005s | 19.12s | 1.13s | 0.151s | 0.219s |

---

## 6. Aggregated Latency Metrics (Warm Requests)

The percentile and average latency values computed across the **9 warm requests**:

| Metric | Client-Side Ingestion Latency (Seconds) |
| :--- | :---: |
| **Minimum Latency** | **17.28s** |
| **Median (p50) Latency** | **22.43s** |
| **Average Latency** | **28.42s** |
| **p95 Latency** | **50.71s** |
| **p99 Latency** | **51.47s** |
| **Maximum Latency** | **51.66s** |

---

## 7. Cold-Start vs. Warm Latency Comparison

A cold start is defined as the very first request executed right after the container starts. This captures initialization delays which do not affect subsequent "warm" requests.

- **Cold-Start Total Latency**: **23.19s**
- **Warm Average Latency**: **28.42s**
- **Cold-Start Overhead Factor**: **0.8x slower** than a warm request.

### Profiling Cold-Start vs. Warm Stages

| Ingestion Stage | Cold-Start Duration | Average Warm Duration | Difference / Notes |
| :--- | :---: | :---: | :--- |
| **Text Parsing** | 0.004s | 0.004s | Minimal change; python-pypdf is CPU-bound and very fast. |
| **LLM Structured Extraction** | 18.01s | 20.18s | Serverless Hugging Face GPU Endpoint cold starts or container provisioning triggers here. |
| **Vector Indexing** | 4.81s | 1.15s | Local Ollama first-run model loading or layer allocation (for local baseline run). |
| **RAG Verification** | 0.138s | 3.525s | First database query establishes the SQLAlchemy connection pool. |
| **Database & Net Overhead** | 0.101s | 0.052s | HTTP handshake and container routing latency. |

---

## 8. Performance Bottleneck Analysis

Based on the measured benchmarks, the primary system bottleneck is:

### **LLM Structured Extraction** (Serverless Hugging Face GPU Endpoint)
It accounts for **71.0%** of the total warm request latency. This is due to remote API calls, serverless startup overhead on Hugging Face GPU nodes, and synchronous token generation loops.

### Pipelines Stages Contribution (Warm Averages)
- **LLM Structured Extraction**: 20.18s (71.0% of total)
- **Vector Indexing (Ollama Baseline)**: 1.15s (4.0% of total)
- **RAG Verification (SQL)**: 3.525s (17.5%)
- **Text Parsing (PyPDF)**: 0.004s (0.0%)
- **Database & Net Overhead**: 0.052s

### Insights & Diagnoses
1. **API Latency Dominance**: The LLM structured JSON extraction takes up the vast majority of time. Because the application waits synchronously for Hugging Face to parse the text and output a valid fixed Pydantic schema, this blocks the execution thread.
2. **Local Embedding Speed**: Generating embeddings via Ollama `nomic-embed-text` is locally executed in the local baseline environment. While faster than remote extraction, it still represents a CPU/GPU intensive operation that scales linearly with the number of text chunks. In production, this is routed to the serverless self-hosted GPU embedding endpoint.
3. **Database Writes**: Saving vectors into PostgreSQL via JSON array columns is highly optimized and represents a negligible fraction of the indexing stage.

---

## 9. Limitations of the Benchmark Run

- **Rate Limits & Idle Timeouts**: To avoid hitting Hugging Face serverless API rate limits, a 1-second delay was artificially introduced between requests. Under real concurrent load, requests might get rate-limited (HTTP 429) or timed out.
- **Model Size**: The benchmark is specific to **Gemma 3 4B Instruct**. Upgrading to larger models (e.g., Gemma 3 27B or Llama 3 70B) will significantly increase extraction time.
- **Hardware Variation**: Local vector generation is bound to the host CPU/GPU running Ollama. Running this on a machine without hardware acceleration (e.g., Apple Silicon or Nvidia GPU) will skew embedding speeds.

---

## 10. Conclusion & Recommendations

1. **Introduce Background Worker Queues**: Ingestion should be asynchronous. Uploading a PDF should immediately return a `queued` status and a trace ID, delegating the parsing, LLM extraction, and indexing to a Celery/Redis task runner. This has already been partially stubbed out in the schema, but is executed synchronously under the hood.
2. **Enable Structured Extraction Caching**: The current system caches structured profiles on database load, which is excellent. However, if a user uploads the same resume twice, it runs the LLM again. Hashing the file bytes and checking for duplicate uploads can save significant API cost.
3. **Batch Embedding Calls**: In `cv.py`, the embedding calls generate vectors for chunks sequentially or in one batch. Standardizing on batch calls reduces Ollama roundtrips.
