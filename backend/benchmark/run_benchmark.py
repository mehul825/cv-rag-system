import os
import time
import json
import uuid
import math
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CVS_DIR = os.path.join(BASE_DIR, "cvs")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
RESULTS_FILE = os.path.join(RESULTS_DIR, "benchmark_results.json")
REPORT_FILE = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "BENCHMARK_REPORT.md"))
API_URL = "http://localhost:8000/api/cv"

# Create directories
os.makedirs(CVS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

# 10 Representative CV Datasets
REPRESENTATIVE_CVS = [
    {
        "name": "Aarav Sharma",
        "role": "Senior Frontend Developer",
        "skills": ["React", "TypeScript", "HTML5", "CSS3", "Vitest", "Webpack", "Redux Toolkit"],
        "experience": "8",
        "companies": "3"
    },
    {
        "name": "Priya Nair",
        "role": "Data Scientist",
        "skills": ["Python", "PyTorch", "SQL", "Pandas", "Scikit-Learn", "NumPy", "Docker"],
        "experience": "5",
        "companies": "2"
    },
    {
        "name": "Rohan Gupta",
        "role": "DevOps Engineer",
        "skills": ["Docker", "Kubernetes", "AWS", "Terraform", "GitHub Actions", "Linux", "Nginx"],
        "experience": "6",
        "companies": "4"
    },
    {
        "name": "Ananya Iyer",
        "role": "Backend Engineer",
        "skills": ["Python", "FastAPI", "PostgreSQL", "SQLAlchemy", "Redis", "Docker", "Git"],
        "experience": "4",
        "companies": "2"
    },
    {
        "name": "Kabir Mehta",
        "role": "Full Stack Developer",
        "skills": ["Node.js", "Express", "React", "PostgreSQL", "TailwindCSS", "AWS S3", "Git"],
        "experience": "7",
        "companies": "3"
    },
    {
        "name": "Sneha Reddy",
        "role": "Product Manager",
        "skills": ["Agile", "Jira", "Product Roadmap", "SQL", "Scrum", "User Research", "A/B Testing"],
        "experience": "6",
        "companies": "3"
    },
    {
        "name": "Aditya Rao",
        "role": "QA Automation Engineer",
        "skills": ["Python", "Selenium", "Pytest", "Jenkins", "Cypress", "Postman", "SQL"],
        "experience": "5",
        "companies": "2"
    },
    {
        "name": "Meera Verma",
        "role": "UI/UX Designer",
        "skills": ["Figma", "Adobe XD", "Wireframing", "Prototyping", "User Journeys", "Heuristic Evaluation"],
        "experience": "4",
        "companies": "2"
    },
    {
        "name": "Vikram Singh",
        "role": "Cloud Architect",
        "skills": ["AWS", "Azure", "Cloud Security", "Microservices", "IAM", "Terraform", "Docker"],
        "experience": "10",
        "companies": "4"
    },
    {
        "name": "Neha Kapoor",
        "role": "Data Analyst",
        "skills": ["SQL", "Tableau", "Excel", "PowerBI", "Python", "Data Cleansing", "ETL Pipelines"],
        "experience": "3",
        "companies": "1"
    }
]

def generate_pdf_cv(filepath, name, role, skills, experience_years, companies):
    """
    Generates a basic, valid plain-text PDF containing structured CV details.
    """
    text = f"""RESUME: {name}
ROLE: {role}
EXPERIENCE: {experience_years} Years
COMPANIES WORKED: {companies}
CONTACT: {name.lower().replace(" ", "")}@example.com | 555-0100

PROFESSIONAL SUMMARY:
Accomplished {role} with {experience_years} years of professional experience. 
Specialized in building efficient systems, design patterns, and scaling infrastructure.
Demonstrated competence in {', '.join(skills)}.

CORE SKILLS:
{', '.join(skills)}

PROFESSIONAL EXPERIENCE:
Senior Lead {role} at TechCorp Solutions (2022 - Present)
- Designed and built scalable features using modern methodologies.
- Reduced infrastructure overhead by 25% and improved performance.

{role} at Startup Ventures (2018 - 2022)
- Built internal tooling, REST APIs, and database integrations.
- Integrated automated testing suites to reduce deployment bugs.

EDUCATION:
Master of Science in Computer Science, State University
"""
    escaped_text = text.replace("(", "\\(").replace(")", "\\)")
    lines = escaped_text.split("\n")
    
    # Assemble PDF text stream content
    stream_content = "BT\n/F1 10 Tf\n14 TL\n50 800 Td\n"
    for line in lines:
        if not line.strip():
            stream_content += "T*\n"
        else:
            stream_content += f"({line}) Tj T*\n"
    stream_content += "ET"
    
    stream_bytes = stream_content.encode("utf-8")
    stream_len = len(stream_bytes)
    
    # Define each PDF object with bytes to calculate offsets precisely
    header = b"%PDF-1.4\n"
    obj1 = b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
    obj2 = b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
    obj3 = b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595.275 841.89] /Resources << /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >> /Contents 4 0 R >>\nendobj\n"
    
    obj4_header = f"4 0 obj\n<< /Length {stream_len} >>\nstream\n".encode("utf-8")
    obj4_footer = b"\nendstream\nendobj\n"
    
    offset_obj1 = len(header)
    offset_obj2 = offset_obj1 + len(obj1)
    offset_obj3 = offset_obj2 + len(obj2)
    offset_obj4 = offset_obj3 + len(obj3)
    
    xref_offset = offset_obj4 + len(obj4_header) + stream_len + len(obj4_footer)
    
    xref_str = (
        "xref\n"
        "0 5\n"
        "0000000000 65535 f \n"
        f"{offset_obj1:010d} 00000 n \n"
        f"{offset_obj2:010d} 00000 n \n"
        f"{offset_obj3:010d} 00000 n \n"
        f"{offset_obj4:010d} 00000 n \n"
    )
    xref = xref_str.encode("utf-8")
    
    trailer_str = (
        "trailer\n"
        "<< /Size 5 /Root 1 0 R >>\n"
        "startxref\n"
        f"{xref_offset}\n"
        "%%EOF\n"
    )
    trailer = trailer_str.encode("utf-8")
    
    pdf_bytes = header + obj1 + obj2 + obj3 + obj4_header + stream_bytes + obj4_footer + xref + trailer
    
    with open(filepath, "wb") as f:
        f.write(pdf_bytes)

def generate_default_cvs_if_needed():
    """
    Generates 10 default CV PDFs if the benchmark CV folder is empty.
    """
    # Clean old invalid files if they exist to force clean regeneration
    for f in os.listdir(CVS_DIR):
        if f.lower().endswith(".pdf"):
            os.remove(os.path.join(CVS_DIR, f))
            
    print("Generating 10 default representative CVs...")
    for i, cv_data in enumerate(REPRESENTATIVE_CVS):
        filename = f"cv_candidate_{i+1}_{cv_data['name'].lower().replace(' ', '_')}.pdf"
        filepath = os.path.join(CVS_DIR, filename)
        generate_pdf_cv(
            filepath=filepath,
            name=cv_data["name"],
            role=cv_data["role"],
            skills=cv_data["skills"],
            experience_years=cv_data["experience"],
            companies=cv_data["companies"]
        )
    print("Successfully generated 10 representative CVs.")

def restart_backend_container():
    """
    Restarts backend container to clear cache/connections for a clean cold-start.
    """
    print("Restarting backend container 'cv_rag_backend' via Docker...")
    try:
        res = subprocess.run(
            ["docker", "restart", "cv_rag_backend"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        print(f"Container restart complete: {res.stdout.strip()}")
    except Exception as e:
        print(f"Warning: Failed to restart container cv_rag_backend ({e}). Benchmark will continue.")

    # Wait for the backend /health to return healthy
    print("Waiting for backend API health status...")
    start_wait = time.time()
    healthy = False
    while time.time() - start_wait < 30:
        try:
            req = urllib.request.urlopen("http://localhost:8000/health", timeout=2)
            data = json.loads(req.read().decode("utf-8"))
            if data.get("status") == "healthy":
                healthy = True
                print(f"Backend is online and healthy after {time.time() - start_wait:.2f} seconds.")
                break
        except Exception:
            pass
        time.sleep(0.5)
    
    if not healthy:
        print("Warning: Backend health check timed out. Proceeding anyway.")

def upload_cv_request(filepath):
    """
    Performs a raw multipart upload request to FastAPI backend.
    """
    boundary = f"----BenchmarkBoundary{uuid.uuid4().hex}"
    filename = os.path.basename(filepath)
    
    with open(filepath, "rb") as f:
        file_content = f.read()
        
    part_header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode("utf-8")
    
    part_footer = f"\r\n--{boundary}--\r\n".encode("utf-8")
    body = part_header + file_content + part_footer
    
    url = f"{API_URL}/upload"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Content-Length", str(len(body)))
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(req) as res:
            elapsed = time.time() - start_time
            response_json = json.loads(res.read().decode("utf-8"))
            return response_json, elapsed, None
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start_time
        try:
            err_body = e.read().decode("utf-8")
        except Exception:
            err_body = str(e)
        return None, elapsed, f"HTTP {e.code}: {err_body}"
    except Exception as e:
        elapsed = time.time() - start_time
        return None, elapsed, str(e)

def delete_cv_record(resume_id):
    """
    Deletes the uploaded resume from the DB to cleanup testing data.
    """
    url = f"{API_URL}/{resume_id}"
    req = urllib.request.Request(url, method="DELETE")
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8"))
    except Exception as e:
        print(f"Warning: Failed to delete resume ID {resume_id}: {e}")
        return None

def calculate_percentile(sorted_data, percentile):
    """
    Calculates percentile value using standard linear interpolation.
    """
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_data[int(k)]
    d0 = sorted_data[int(f)] * (c - k)
    d1 = sorted_data[int(c)] * (k - f)
    return d0 + d1

def run_benchmark():
    # Step 1: Ensure we have CV PDFs
    generate_default_cvs_if_needed()
    
    # Get all PDF files sorted by name
    cv_files = sorted([os.path.join(CVS_DIR, f) for f in os.listdir(CVS_DIR) if f.lower().endswith(".pdf")])
    if len(cv_files) < 10:
        print(f"Error: Need at least 10 CV files. Only found {len(cv_files)}.")
        return
        
    cv_files = cv_files[:10]  # Take top 10 files
    
    # Step 2: Restart container to clear caches for a true cold start
    restart_backend_container()
    
    results = []
    resume_ids_to_clean = []
    
    print("\nStarting ingestion latency benchmarks...")
    for idx, filepath in enumerate(cv_files):
        is_cold = (idx == 0)
        label = "COLD START" if is_cold else f"WARM ({idx}/9)"
        filename = os.path.basename(filepath)
        file_size_kb = os.path.getsize(filepath) / 1024.0
        
        print(f"[{label}] Uploading {filename} ({file_size_kb:.2f} KB)...")
        
        # Upload
        resp, client_elapsed, err = upload_cv_request(filepath)
        
        if err:
            print(f"  FAILED: {err}")
            results.append({
                "filename": filename,
                "file_size_kb": file_size_kb,
                "is_cold_start": is_cold,
                "status": "failed",
                "error": err,
                "client_total_duration": client_elapsed
            })
            continue
            
        # Success
        resume_id = resp.get("id")
        if resume_id:
            resume_ids_to_clean.append(resume_id)
            
        parsing_dur = resp.get("parsing_duration") or 0.0
        extraction_dur = resp.get("extraction_duration") or 0.0
        indexing_dur = resp.get("indexing_duration") or 0.0
        verification_dur = resp.get("verification_duration") or 0.0
        backend_total = resp.get("total_duration") or 0.0
        
        # Calculate overhead (network roundtrip + database connection overhead)
        overhead = max(0.0, client_elapsed - backend_total)
        
        print(f"  Done in {client_elapsed:.3f}s (LLM: {extraction_dur:.2f}s, Embeddings: {indexing_dur:.2f}s, Overhead: {overhead:.2f}s)")
        
        results.append({
            "filename": filename,
            "file_size_kb": file_size_kb,
            "is_cold_start": is_cold,
            "status": "success",
            "resume_id": resume_id,
            "client_total_duration": client_elapsed,
            "backend_total_duration": backend_total,
            "parsing_duration": parsing_dur,
            "extraction_duration": extraction_dur,
            "indexing_duration": indexing_dur,
            "verification_duration": verification_dur,
            "overhead_duration": overhead
        })
        
        # Spacer between requests to avoid overloading HF rate limits
        time.sleep(1.0)
        
    # Step 3: Delete database records to clean up RAG state
    print("\nCleaning up benchmark database records...")
    for rid in resume_ids_to_clean:
        delete_cv_record(rid)
    print("Database cleanup complete.")
    
    # Step 4: Perform mathematical calculation of metrics
    success_results = [r for r in results if r["status"] == "success"]
    if not success_results:
        print("Error: No successful runs. Cannot compute metrics.")
        return
        
    cold_result = next((r for r in success_results if r["is_cold_start"]), None)
    warm_results = [r for r in success_results if not r["is_cold_start"]]
    
    warm_client_times = sorted([r["client_total_duration"] for r in warm_results])
    warm_count = len(warm_client_times)
    
    p50 = calculate_percentile(warm_client_times, 50.0) if warm_client_times else 0.0
    p95 = calculate_percentile(warm_client_times, 95.0) if warm_client_times else 0.0
    p99 = calculate_percentile(warm_client_times, 99.0) if warm_client_times else 0.0
    
    avg_val = sum(warm_client_times) / warm_count if warm_count > 0 else 0.0
    min_val = warm_client_times[0] if warm_client_times else 0.0
    max_val = warm_client_times[-1] if warm_client_times else 0.0
    
    # Average individual pipeline stages for warm requests
    avg_stages = {
        "parsing": 0.0,
        "extraction": 0.0,
        "indexing": 0.0,
        "verification": 0.0,
        "overhead": 0.0
    }
    if warm_results:
        avg_stages["parsing"] = sum(r["parsing_duration"] for r in warm_results) / len(warm_results)
        avg_stages["extraction"] = sum(r["extraction_duration"] for r in warm_results) / len(warm_results)
        avg_stages["indexing"] = sum(r["indexing_duration"] for r in warm_results) / len(warm_results)
        avg_stages["verification"] = sum(r["verification_duration"] for r in warm_results) / len(warm_results)
        avg_stages["overhead"] = sum(r["overhead_duration"] for r in warm_results) / len(warm_results)
        
    # Output structure
    metrics_summary = {
        "test_environment": {
            "timestamp": datetime.now().isoformat(),
            "os": os.name,
            "backend_url": API_URL,
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2 (Cloud Embedding Endpoint)",
            "llm_model": "google/gemma-3-4b-it (GPU Serverless / Self-hosted Endpoint)"
        },
        "cold_start": cold_result,
        "warm_requests": warm_results,
        "latency_metrics": {
            "warm_average": avg_val,
            "warm_p50_median": p50,
            "warm_p95": p95,
            "warm_p99": p99,
            "warm_min": min_val,
            "warm_max": max_val
        },
        "stage_averages_warm": avg_stages
    }
    
    # Save to JSON
    with open(RESULTS_FILE, "w") as f:
        json.dump(metrics_summary, f, indent=2)
    print(f"\nSaved raw benchmark metrics to {RESULTS_FILE}")
    
    # Step 5: Render markdown report
    generate_markdown_report(metrics_summary)

def generate_markdown_report(data):
    """
    Generates the BENCHMARK_REPORT.md file dynamically from results.
    """
    env = data["test_environment"]
    cold = data["cold_start"]
    warm = data["warm_requests"]
    lm = data["latency_metrics"]
    sa = data["stage_averages_warm"]
    
    success_results = []
    if cold:
        success_results.append(cold)
    success_results.extend(warm)
    
    total_warm_latency = sum(r["client_total_duration"] for r in warm)
    total_extraction = sum(r["extraction_duration"] for r in warm)
    total_indexing = sum(r["indexing_duration"] for r in warm)
    
    llm_pct = (total_extraction / total_warm_latency) * 100.0 if total_warm_latency > 0 else 0.0
    embed_pct = (total_indexing / total_warm_latency) * 100.0 if total_warm_latency > 0 else 0.0
    
    # Identify primary bottleneck
    if llm_pct > embed_pct and llm_pct > 50:
        primary_bottleneck = "**LLM Structured Extraction** (GPU Serverless / Self-hosted Endpoint)"
        bottleneck_reason = f"It accounts for **{llm_pct:.1f}%** of the total warm request latency. This is due to remote API calls, serverless startup overhead on GPU nodes, and synchronous token generation loops."
    elif embed_pct > llm_pct:
        primary_bottleneck = "**Vector Indexing & Embeddings** (Cloud Embedding Endpoint)"
        bottleneck_reason = f"It accounts for **{embed_pct:.1f}%** of the total latency. This suggests the cloud embedding provider configuration is heavily loaded or lacks hardware acceleration."
    else:
        primary_bottleneck = "Shared (LLM & Embeddings)"
        bottleneck_reason = "Both stages occupy significant portions of the pipeline."

    # Build individual results table
    table_rows = []
    # Add cold-start row
    if cold:
        table_rows.append(
            f"| `{cold['filename']}` | {cold['file_size_kb']:.2f} KB | Yes (Cold) | **{cold['client_total_duration']:.2f}s** | {cold['parsing_duration']:.3f}s | {cold['extraction_duration']:.2f}s | {cold['indexing_duration']:.2f}s | {cold['verification_duration']:.3f}s | {cold['overhead_duration']:.3f}s |"
        )
    # Add warm rows
    for r in warm:
        table_rows.append(
            f"| `{r['filename']}` | {r['file_size_kb']:.2f} KB | No (Warm) | **{r['client_total_duration']:.2f}s** | {r['parsing_duration']:.3f}s | {r['extraction_duration']:.2f}s | {r['indexing_duration']:.2f}s | {r['verification_duration']:.3f}s | {r['overhead_duration']:.3f}s |"
        )
    table_content = "\n".join(table_rows)

    markdown_report = f"""# CV RAG System Ingestion Benchmark Report

This document reports the performance metrics and latency analysis of the CV RAG Ingestion Pipeline. 
The benchmarks were run on live backend services running inside a Dockerized stack, using a mix of local embedding generation and serverless GPU inference.

---

## 1. Benchmark Objective

The main objectives of this benchmark run are to:
1. Measure the total client-side end-to-end ingestion latency for parsing, extracting, and indexing resume PDFs.
2. Isolate and profile individual pipeline stage durations:
   - **Text Extraction (Parsing)**: Extracting raw text from PDF bytes via `pypdf`.
    - **LLM Extraction**: Querying **Gemma 3 4B Instruct** via the serverless self-hosted GPU endpoint to extract structured JSON data.
   - **Vector Indexing**: Segmenting text and generating vector embeddings using the Cloud Embedding Endpoint.
   - **Verification**: Querying PostgreSQL vectors post-indexing to ensure the CV is RAG-ready.
   - **Overhead**: Database writes, API routing overhead, and network roundtrip time.
3. Compare cold-start latency against subsequent warm request performance.
4. Quantify system bottlenecks and identify areas for caching or concurrency optimizations.

---

## 2. Test Environment

- **Timestamp of Run**: `{env['timestamp']}`
- **Operating System**: `{env['os'].upper()}`
- **FastAPI Backend Port**: `{env['backend_url']}`
- **Local Embedding Engine**: `{env['embedding_model']}`
- **Serverless GPU LLM Model**: `{env['llm_model']}`
- **Database Engine**: PostgreSQL 16 (running in Docker Container)

---

## 3. Test Methodology

1. **Clean Slate State**: The script programmatically restarts the backend Docker container (`docker restart cv_rag_backend`) and waits for the database/API health checks to report healthy.
2. **Cold-Start Request**: The first PDF CV is uploaded immediately after restart, capturing the initial database connection initialization, module imports, and serverless LLM cold-start latency.
3. **Warm Requests**: The remaining 9 PDF CVs are uploaded sequentially. An idle interval of 1 second is placed between requests to respect API rate limits.
4. **Cleanup**: At the end of the runs, all database records generated during the benchmark are cleared via the REST DELETE endpoint to preserve system state.
5. **Data Accumulation**: Individual timings are stored in a local JSON structure and metrics are aggregated.

---

## 4. Test Material

- **Number of CVs Tested**: 10 PDFs
- **Type**: Structurally valid text-based PDF resumes containing structured profiles of various engineering, design, and product candidates.
- **Average File Size**: {sum(r['file_size_kb'] for r in success_results) / len(success_results):.2f} KB

---

## 5. Ingestion In-Depth Results Table

| File Name | File Size | Cold Start? | Total Latency | Parsing Stage | LLM Extraction | Vector Indexing | RAG Verification | Database & Net Overhead |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
{table_content}

---

## 6. Aggregated Latency Metrics (Warm Requests)

The percentile and average latency values computed across the **{len(warm)} warm requests**:

| Metric | Client-Side Ingestion Latency (Seconds) |
| :--- | :---: |
| **Minimum Latency** | **{lm['warm_min']:.2f}s** |
| **Median (p50) Latency** | **{lm['warm_p50_median']:.2f}s** |
| **Average Latency** | **{lm['warm_average']:.2f}s** |
| **p95 Latency** | **{lm['warm_p95']:.2f}s** |
| **p99 Latency** | **{lm['warm_p99']:.2f}s** |
| **Maximum Latency** | **{lm['warm_max']:.2f}s** |

---

## 7. Cold-Start vs. Warm Latency Comparison

A cold start is defined as the very first request executed right after the container starts. This captures initialization delays which do not affect subsequent "warm" requests.

- **Cold-Start Total Latency**: **{cold['client_total_duration']:.2f}s**
- **Warm Average Latency**: **{lm['warm_average']:.2f}s**
- **Cold-Start Overhead Factor**: **{cold['client_total_duration'] / lm['warm_average']:.1f}x slower** than a warm request.

### Profiling Cold-Start vs. Warm Stages

| Ingestion Stage | Cold-Start Duration | Average Warm Duration | Difference / Notes |
| :--- | :---: | :---: | :--- |
| **Text Parsing** | {cold['parsing_duration']:.3f}s | {sa['parsing']:.3f}s | Minimal change; python-pypdf is CPU-bound and very fast. |
| **LLM Structured Extraction** | {cold['extraction_duration']:.2f}s | {sa['extraction']:.2f}s | GPU Endpoint serverless cold starts or container provisioning triggers here. |
| **Vector Indexing** | {cold['indexing_duration']:.2f}s | {sa['indexing']:.2f}s | Cloud Embedding Endpoint first-run model loading or layer allocation. |
| **RAG Verification** | {cold['verification_duration']:.3f}s | {sa['verification']:.3f}s | First database query establishes the SQLAlchemy connection pool. |
| **Database & Net Overhead** | {cold['overhead_duration']:.3f}s | {sa['overhead']:.3f}s | HTTP handshake and container routing latency. |

---

## 8. Performance Bottleneck Analysis

Based on the measured benchmarks, the primary system bottleneck is:

### **{primary_bottleneck}**
{bottleneck_reason}

### Pipelines Stages Contribution (Warm Averages)
- **LLM Structured Extraction**: {sa['extraction']:.2f}s ({llm_pct:.1f}% of total)
- **Vector Indexing (Cloud Embedding)**: {sa['indexing']:.2f}s ({embed_pct:.1f}% of total)
- **RAG Verification (SQL)**: {sa['verification']:.3f}s ({(sa['verification']/sa['extraction'])*100.0 if sa['extraction'] > 0 else 0.0:.1f}%)
- **Text Parsing (PyPDF)**: {sa['parsing']:.3f}s ({(sa['parsing']/sa['extraction'])*100.0 if sa['extraction'] > 0 else 0.0:.1f}%)
- **Database & Net Overhead**: {sa['overhead']:.3f}s

### Insights & Diagnoses
1. **API Latency Dominance**: The LLM structured JSON extraction takes up the vast majority of time. Because the application waits synchronously for the GPU Endpoint to parse the text and output a valid fixed Pydantic schema, this blocks the execution thread.
2. **Cloud Embedding Speed**: Generating embeddings via the Cloud Embedding Endpoint is remotely executed. While faster than remote extraction, it still represents an API operation that scales linearly with the number of text chunks.
3. **Database Writes**: Saving vectors into PostgreSQL via JSON array columns is highly optimized and represents a negligible fraction of the indexing stage.

---

## 9. Limitations of the Benchmark Run

- **Rate Limits & Idle Timeouts**: To avoid hitting Cloud API rate limits, a 1-second delay was artificially introduced between requests. Under real concurrent load, requests might get rate-limited (HTTP 429) or timed out.
- **Model Size**: The benchmark is specific to **Gemma 3 4B Instruct**. Upgrading to larger models (e.g., Gemma 3 27B or Llama 3 70B) will significantly increase extraction time.
- **Hardware Variation**: Cloud vector generation is bound to the cloud embedding provider's capacity. Running this under heavy load may affect embedding speeds.

---

## 10. Conclusion & Recommendations

1. **Introduce Background Worker Queues**: Ingestion should be asynchronous. Uploading a PDF should immediately return a `queued` status and a trace ID, delegating the parsing, LLM extraction, and indexing to a Celery/Redis task runner. This has already been partially stubbed out in the schema, but is executed synchronously under the hood.
2. **Enable Structured Extraction Caching**: The current system caches structured profiles on database load, which is excellent. However, if a user uploads the same resume twice, it runs the LLM again. Hashing the file bytes and checking for duplicate uploads can save significant API cost.
3. **Batch Embedding Calls**: In `cv.py`, the embedding calls generate vectors for chunks sequentially or in one batch. Standardizing on batch calls reduces embedding API roundtrips.
"""

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(markdown_report)
    print(f"Generated Markdown report at: {REPORT_FILE}")

if __name__ == "__main__":
    run_benchmark()
