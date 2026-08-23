# CV RAG System Ingestion Benchmark Report

This document reports the performance metrics and latency analysis of the CV RAG Ingestion Pipeline. 
The benchmarks were run on live backend services running inside a Dockerized stack, using a mix of local embedding generation and serverless GPU inference.

---

## 1. Benchmark Objective

The main objectives of this benchmark run are to:
1. Measure the total client-side end-to-end ingestion latency for parsing, extracting, and indexing resume PDFs.
2. Isolate and profile individual pipeline stage durations:
   - **Text Extraction (Parsing)**: Extracting raw text from PDF bytes via `pypdf`.
   - **LLM Extraction**: Querying **Gemma 3 4B Instruct** via Hugging Face serverless inference to extract structured JSON data.
   - **Vector Indexing**: Segmenting text and generating vector embeddings using the local **Ollama** instance (`nomic-embed-text`).
   - **Verification**: Querying PostgreSQL vectors post-indexing to ensure the CV is RAG-ready.
   - **Overhead**: Database writes, API routing overhead, and network roundtrip time.
3. Compare cold-start latency against subsequent warm request performance.
4. Quantify system bottlenecks and identify areas for caching or concurrency optimizations.

---

## 2. Test Environment

- **Timestamp of Run**: `2026-08-23T06:29:20.889845`
- **Operating System**: `NT`
- **FastAPI Backend Port**: `http://localhost:8000/api/cv`
- **Local Embedding Engine**: `nomic-embed-text (local via Ollama)`
- **Serverless GPU LLM Model**: `google/gemma-3-4b-it (serverless via Hugging Face)`
- **Database Engine**: PostgreSQL 16 (running in Docker Container)

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
| `cv_candidate_10_neha_kapoor.pdf` | 1.63 KB | Yes (Cold) | **58.13s** | 0.005s | 53.00s | 4.72s | 0.150s | 0.113s |
| `cv_candidate_1_aarav_sharma.pdf` | 1.67 KB | No (Warm) | **48.60s** | 0.004s | 47.18s | 1.15s | 0.145s | 0.039s |
| `cv_candidate_2_priya_nair.pdf` | 1.62 KB | No (Warm) | **99.23s** | 0.007s | 97.70s | 1.19s | 0.147s | 0.041s |
| `cv_candidate_3_rohan_gupta.pdf` | 1.64 KB | No (Warm) | **57.87s** | 0.005s | 56.44s | 1.13s | 0.153s | 0.038s |
| `cv_candidate_4_ananya_iyer.pdf` | 1.63 KB | No (Warm) | **55.27s** | 0.002s | 53.85s | 1.17s | 0.153s | 0.031s |
| `cv_candidate_5_kabir_mehta.pdf` | 1.65 KB | No (Warm) | **43.61s** | 0.003s | 42.14s | 1.17s | 0.169s | 0.036s |
| `cv_candidate_6_sneha_reddy.pdf` | 1.64 KB | No (Warm) | **48.58s** | 0.002s | 47.18s | 1.18s | 0.135s | 0.011s |
| `cv_candidate_7_aditya_rao.pdf` | 1.65 KB | No (Warm) | **41.00s** | 0.004s | 39.57s | 1.14s | 0.156s | 0.039s |
| `cv_candidate_8_meera_verma.pdf` | 1.66 KB | No (Warm) | **42.33s** | 0.003s | 40.93s | 1.16s | 0.164s | 0.014s |
| `cv_candidate_9_vikram_singh.pdf` | 1.64 KB | No (Warm) | **37.26s** | 0.006s | 35.81s | 1.15s | 0.182s | 0.025s |

---

## 6. Aggregated Latency Metrics (Warm Requests)

The percentile and average latency values computed across the **9 warm requests**:

| Metric | Client-Side Ingestion Latency (Seconds) |
| :--- | :---: |
| **Minimum Latency** | **37.26s** |
| **Median (p50) Latency** | **48.58s** |
| **Average Latency** | **52.64s** |
| **p95 Latency** | **82.69s** |
| **p99 Latency** | **95.92s** |
| **Maximum Latency** | **99.23s** |

---

## 7. Cold-Start vs. Warm Latency Comparison

A cold start is defined as the very first request executed right after the container starts. This captures initialization delays which do not affect subsequent "warm" requests.

- **Cold-Start Total Latency**: **58.13s**
- **Warm Average Latency**: **52.64s**
- **Cold-Start Overhead Factor**: **1.1x slower** than a warm request.

### Profiling Cold-Start vs. Warm Stages

| Ingestion Stage | Cold-Start Duration | Average Warm Duration | Difference / Notes |
| :--- | :---: | :---: | :--- |
| **Text Parsing** | 0.005s | 0.004s | Minimal change; python-pypdf is CPU-bound and very fast. |
| **LLM Structured Extraction** | 53.00s | 51.20s | Serverless Hugging Face cold starts or container provisioning triggers here. |
| **Vector Indexing** | 4.72s | 1.16s | Local Ollama first-run model loading or layer allocation. |
| **RAG Verification** | 0.150s | 0.156s | First database query establishes the SQLAlchemy connection pool. |
| **Database & Net Overhead** | 0.113s | 0.030s | HTTP handshake and container routing latency. |

---

## 8. Performance Bottleneck Analysis

Based on the measured benchmarks, the primary system bottleneck is:

### ****LLM Structured Extraction** (Serverless Hugging Face Inference API)**
It accounts for **97.3%** of the total warm request latency. This is due to remote API calls, serverless startup overhead on Hugging Face GPU nodes, and synchronous token generation loops.

### Pipelines Stages Contribution (Warm Averages)
- **LLM Structured Extraction**: 51.20s (97.3% of total)
- **Vector Indexing (Ollama)**: 1.16s (2.2% of total)
- **RAG Verification (SQL)**: 0.156s (0.3%)
- **Text Parsing (PyPDF)**: 0.004s (0.0%)
- **Database & Net Overhead**: 0.030s

### Insights & Diagnoses
1. **API Latency Dominance**: The LLM structured JSON extraction takes up the vast majority of time. Because the application waits synchronously for Hugging Face to parse the text and output a valid fixed Pydantic schema, this blocks the execution thread.
2. **Local Embedding Speed**: Generating embeddings via Ollama `nomic-embed-text` is locally executed. While faster than remote extraction, it still represents a CPU/GPU intensive operation that scales linearly with the number of text chunks.
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
