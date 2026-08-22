from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
import json
import time
import uuid

from app.core.database import get_db
from app.models.resume import Resume, ResumeChunk
from app.services.pdf_parser import extract_text_from_pdf, chunk_text
from app.services.openai_service import generate_embeddings_batch, ask_question_with_context
from app.services.rag_service import retrieve_relevant_chunks
from app.schemas.cv_schema import CVFixedSchema, DynamicExtractionRequest, DynamicExtractionResponse
from app.services.extractor import extract_cv_fixed, extract_cv_dynamic

router = APIRouter(prefix="/cv", tags=["CV RAG"])

# Pydantic Schemas
class ResumeResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime
    status: str
    error_message: Optional[str] = None
    trace_id: Optional[str] = None
    parsing_duration: Optional[float] = None
    extraction_duration: Optional[float] = None
    indexing_duration: Optional[float] = None
    verification_duration: Optional[float] = None
    total_duration: Optional[float] = None

    class Config:
        from_attributes = True

class BatchUploadResult(BaseModel):
    filename: str
    status: str
    resume_id: Optional[int] = None
    error: Optional[str] = None
    trace_id: Optional[str] = None

class Citation(BaseModel):
    resume_id: int
    filename: str
    chunk_index: int
    text_snippet: str

class QueryRequest(BaseModel):
    resume_id: int
    question: str

class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation] = []

@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_cv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Uploads a CV PDF, parses its text, chunks it, generates embeddings, and saves to database.
    Tracks status, trace ID, and duration metrics.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported."
        )
    
    trace_id = str(uuid.uuid4())
    start_time = time.time()
    
    # 0. Initial queued entry
    db_resume = Resume(
        filename=file.filename,
        status="queued",
        trace_id=trace_id
    )
    db.add(db_resume)
    await db.commit()
    await db.refresh(db_resume)
    
    parsing_duration = 0.0
    extraction_duration = 0.0
    indexing_duration = 0.0
    verification_duration = 0.0
    
    try:
        # Read file contents
        content = await file.read()
        
        # 1. Parsing stage
        db_resume.status = "parsing"
        await db.commit()
        
        parsing_start = time.time()
        parsed_text = extract_text_from_pdf(content)
        parsing_duration = time.time() - parsing_start
        
        if not parsed_text:
            raise ValueError("Unable to extract text from the provided PDF.")
            
        db_resume.parsed_text = parsed_text
        db_resume.parsing_duration = parsing_duration
        await db.commit()
        
        # 2. Extraction stage
        db_resume.status = "extracting"
        await db.commit()
        
        extraction_start = time.time()
        extracted_data = {}
        try:
            extracted_data["fixed_extraction"] = extract_cv_fixed(parsed_text)
        except Exception as ex:
            print(f"[{trace_id}] Extraction failed: {ex}")
            extracted_data["fixed_extraction"] = None
        extraction_duration = time.time() - extraction_start
        
        db_resume.extracted_data = extracted_data
        db_resume.extraction_duration = extraction_duration
        await db.commit()
        
        # 3. Indexing stage
        db_resume.status = "indexing"
        await db.commit()
        
        indexing_start = time.time()
        chunks = chunk_text(parsed_text, chunk_size=800, chunk_overlap=150)
        if not chunks:
            raise ValueError("The PDF contains insufficient text to chunk.")
            
        embeddings = generate_embeddings_batch(chunks)
        
        db_chunks = []
        for i, (chunk_text_segment, emb) in enumerate(zip(chunks, embeddings)):
            db_chunk = ResumeChunk(
                resume_id=db_resume.id,
                chunk_text=chunk_text_segment,
                embedding=emb,
                chunk_index=i
            )
            db_chunks.append(db_chunk)
            
        db.add_all(db_chunks)
        indexing_duration = time.time() - indexing_start
        
        db_resume.indexing_duration = indexing_duration
        await db.commit()
        
        # 4. Post-indexing RAG verification stage
        verification_start = time.time()
        matched_chunks = await retrieve_relevant_chunks(
            db=db,
            resume_id=db_resume.id,
            query_text="experience skills education",
            top_k=1
        )
        verification_duration = time.time() - verification_start
        db_resume.verification_duration = verification_duration
        
        if matched_chunks and len(matched_chunks) > 0:
            db_resume.status = "rag_ready"
        else:
            raise ValueError("RAG verification failed: No relevant chunks could be retrieved after indexing.")
            
        db_resume.total_duration = time.time() - start_time
        await db.commit()
        await db.refresh(db_resume)
        return db_resume
        
    except Exception as e:
        await db.rollback()
        db_resume.status = "failed"
        db_resume.error_message = str(e)
        db_resume.parsing_duration = parsing_duration
        db_resume.extraction_duration = extraction_duration
        db_resume.indexing_duration = indexing_duration
        db_resume.verification_duration = verification_duration
        db_resume.total_duration = time.time() - start_time
        
        await db.commit()
        await db.refresh(db_resume)
        
        print(f"[{trace_id}] Upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/list", response_model=List[ResumeResponse])
async def list_cvs(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all uploaded resumes/CVs from the database.
    """
    stmt = select(Resume).order_by(Resume.uploaded_at.desc())
    result = await db.execute(stmt)
    resumes = result.scalars().all()
    return resumes

@router.delete("/{resume_id}", status_code=status.HTTP_200_OK)
async def delete_cv(resume_id: int, db: AsyncSession = Depends(get_db)):
    """
    Deletes a specific CV and all its associated text chunks from the database.
    """
    stmt = select(Resume).where(Resume.id == resume_id)
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )
        
    await db.delete(resume)
    await db.commit()
    return {"message": f"Successfully deleted CV '{resume.filename}' and its embeddings."}

@router.post("/query", response_model=QueryResponse)
async def query_cv(request: QueryRequest, db: AsyncSession = Depends(get_db)):
    """
    Retrieves relevant resume chunks and queries LLM to answer a question.
    Returns chunk citations along with the response.
    """
    stmt = select(Resume).where(Resume.id == request.resume_id)
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {request.resume_id} not found."
        )
        
    try:
        matched_chunks = await retrieve_relevant_chunks(
            db=db,
            resume_id=request.resume_id,
            query_text=request.question,
            top_k=5
        )
        
        if not matched_chunks:
            return QueryResponse(
                answer="No relevant content found in the resume. Try asking a different question.",
                citations=[]
            )
            
        chunk_texts = [c.chunk_text for c in matched_chunks]
        
        answer = ask_question_with_context(
            question=request.question,
            context_chunks=chunk_texts,
            filename=resume.filename
        )
        
        # Build structured citations list
        citations = []
        for c in matched_chunks:
            snippet = c.chunk_text[:120] + "..." if len(c.chunk_text) > 120 else c.chunk_text
            citations.append(Citation(
                resume_id=c.resume_id,
                filename=resume.filename,
                chunk_index=c.chunk_index,
                text_snippet=snippet
            ))
            
        return QueryResponse(answer=answer, citations=citations)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )

@router.post("/extract/fixed", response_model=CVFixedSchema)
async def extract_fixed_from_file(file: UploadFile = File(...)):
    """
    Parses an uploaded PDF resume and extracts structured data according to the fixed schema.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported."
        )
    try:
        content = await file.read()
        parsed_text = extract_text_from_pdf(content)
        if not parsed_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to extract text from the provided PDF."
            )
        extracted_data = extract_cv_fixed(parsed_text)
        return extracted_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )

@router.post("/extract/dynamic", response_model=DynamicExtractionResponse)
async def extract_dynamic_from_file(
    file: UploadFile = File(...), 
    fields: str = Form(..., description="JSON string of dynamic fields and descriptions")
):
    """
    Parses an uploaded PDF resume and extracts custom structured data according to user-defined fields.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported."
        )
    try:
        try:
            fields_dict = json.loads(fields)
            if not isinstance(fields_dict, dict):
                raise ValueError()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid fields JSON format. Must be a valid JSON dictionary mapping keys to descriptions."
            )
            
        content = await file.read()
        parsed_text = extract_text_from_pdf(content)
        if not parsed_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to extract text from the provided PDF."
            )
        extracted_data = extract_cv_dynamic(parsed_text, fields_dict)
        return DynamicExtractionResponse(extracted_data=extracted_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )

@router.post("/{resume_id}/extract/fixed", response_model=CVFixedSchema)
async def extract_fixed_from_db(resume_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves a resume from the database and extracts structured data according to the fixed schema.
    Reuses stored extraction results from PostgreSQL if present.
    """
    stmt = select(Resume).where(Resume.id == resume_id)
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )
        
    if not resume.parsed_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected resume contains no parsed text."
        )
        
    # Check cache in PostgreSQL
    ext_json = resume.extracted_data or {}
    if "fixed_extraction" in ext_json and ext_json["fixed_extraction"] is not None:
        print(f"Cache hit: returning stored fixed extraction for resume {resume_id}")
        return ext_json["fixed_extraction"]
        
    try:
        extracted_data = extract_cv_fixed(resume.parsed_text)
        
        # Save to database
        if not resume.extracted_data:
            resume.extracted_data = {}
            
        updated_json = dict(resume.extracted_data)
        updated_json["fixed_extraction"] = extracted_data
        resume.extracted_data = updated_json
        
        db.add(resume)
        await db.commit()
        
        return extracted_data
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )

@router.post("/{resume_id}/extract/dynamic", response_model=DynamicExtractionResponse)
async def extract_dynamic_from_db(
    resume_id: int, 
    request: DynamicExtractionRequest, 
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieves a resume from the database and extracts custom structured data according to user-defined fields.
    Reuses stored extraction results from PostgreSQL if present.
    """
    stmt = select(Resume).where(Resume.id == resume_id)
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )
        
    if not resume.parsed_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected resume contains no parsed text."
        )
        
    # Stable cache key for dynamic extraction config
    fields_key = json.dumps(request.fields, sort_keys=True)
    
    ext_json = resume.extracted_data or {}
    dynamic_cache = ext_json.get("dynamic_extractions", {})
    
    if fields_key in dynamic_cache:
        print(f"Cache hit: returning stored dynamic extraction for resume {resume_id}")
        return DynamicExtractionResponse(extracted_data=dynamic_cache[fields_key])
        
    try:
        extracted_data = extract_cv_dynamic(resume.parsed_text, request.fields)
        
        # Save to database
        if not resume.extracted_data:
            resume.extracted_data = {}
            
        updated_json = dict(resume.extracted_data)
        if "dynamic_extractions" not in updated_json:
            updated_json["dynamic_extractions"] = {}
            
        updated_dyn = dict(updated_json["dynamic_extractions"])
        updated_dyn[fields_key] = extracted_data
        updated_json["dynamic_extractions"] = updated_dyn
        
        resume.extracted_data = updated_json
        
        db.add(resume)
        await db.commit()
        
        return DynamicExtractionResponse(extracted_data=extracted_data)
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )

@router.get("/{resume_id}/structured", response_model=CVFixedSchema)
async def get_structured_cv(resume_id: int, db: AsyncSession = Depends(get_db)):
    """
    Retrieves the stored structured JSON for an existing CV from PostgreSQL.
    If not already extracted, runs the extraction dynamically and saves it.
    """
    stmt = select(Resume).where(Resume.id == resume_id)
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {resume_id} not found."
        )
        
    ext_json = resume.extracted_data or {}
    if "fixed_extraction" in ext_json and ext_json["fixed_extraction"] is not None:
        return ext_json["fixed_extraction"]
        
    if not resume.parsed_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The selected resume contains no parsed text to extract."
        )
        
    try:
        extracted_data = extract_cv_fixed(resume.parsed_text)
        
        if not resume.extracted_data:
            resume.extracted_data = {}
            
        updated_json = dict(resume.extracted_data)
        updated_json["fixed_extraction"] = extracted_data
        resume.extracted_data = updated_json
        
        db.add(resume)
        await db.commit()
        
        return extracted_data
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Extraction failed: {str(e)}"
        )

@router.post("/upload/batch", response_model=List[BatchUploadResult])
async def upload_cvs_batch(files: List[UploadFile] = File(...), db: AsyncSession = Depends(get_db)):
    """
    Accepts multiple PDF resume uploads, processes and indexes each individually.
    If one file fails, the others will still continue processing.
    """
    results = []
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            results.append(BatchUploadResult(
                filename=file.filename,
                status="failed",
                error="Invalid file format. Only PDF files are supported."
            ))
            continue
            
        trace_id = str(uuid.uuid4())
        start_time = time.time()
        
        # 0. Initial queued entry
        db_resume = Resume(
            filename=file.filename,
            status="queued",
            trace_id=trace_id
        )
        
        parsing_duration = 0.0
        extraction_duration = 0.0
        indexing_duration = 0.0
        verification_duration = 0.0
        
        try:
            db.add(db_resume)
            await db.commit()
            await db.refresh(db_resume)
            
            # Read file content
            content = await file.read()
            
            # 1. Parsing stage
            db_resume.status = "parsing"
            await db.commit()
            
            parsing_start = time.time()
            parsed_text = extract_text_from_pdf(content)
            parsing_duration = time.time() - parsing_start
            
            if not parsed_text:
                raise ValueError("Unable to extract text from PDF.")
                
            db_resume.parsed_text = parsed_text
            db_resume.parsing_duration = parsing_duration
            await db.commit()
            
            # 2. Extraction stage
            db_resume.status = "extracting"
            await db.commit()
            
            extraction_start = time.time()
            extracted_data = {}
            try:
                extracted_data["fixed_extraction"] = extract_cv_fixed(parsed_text)
            except Exception as ex:
                print(f"[{trace_id}] Extraction failed during batch: {ex}")
                extracted_data["fixed_extraction"] = None
            extraction_duration = time.time() - extraction_start
            
            db_resume.extracted_data = extracted_data
            db_resume.extraction_duration = extraction_duration
            await db.commit()
            
            # 3. Indexing stage
            db_resume.status = "indexing"
            await db.commit()
            
            indexing_start = time.time()
            chunks = chunk_text(parsed_text, chunk_size=800, chunk_overlap=150)
            if not chunks:
                raise ValueError("PDF has insufficient text to chunk.")
                
            embeddings = generate_embeddings_batch(chunks)
            
            # 4. Save to Database using nested transaction savepoint
            async with db.begin_nested():
                db_chunks = []
                for i, (chunk_text_seg, emb) in enumerate(zip(chunks, embeddings)):
                    db_chunk = ResumeChunk(
                        resume_id=db_resume.id,
                        chunk_text=chunk_text_seg,
                        embedding=emb,
                        chunk_index=i
                    )
                    db_chunks.append(db_chunk)
                db.add_all(db_chunks)
                
            indexing_duration = time.time() - indexing_start
            db_resume.indexing_duration = indexing_duration
            await db.commit()
            
            # 5. Post-indexing RAG verification stage
            verification_start = time.time()
            matched_chunks = await retrieve_relevant_chunks(
                db=db,
                resume_id=db_resume.id,
                query_text="experience skills education",
                top_k=1
            )
            verification_duration = time.time() - verification_start
            db_resume.verification_duration = verification_duration
            
            if matched_chunks and len(matched_chunks) > 0:
                db_resume.status = "rag_ready"
            else:
                raise ValueError("RAG verification failed: No relevant chunks could be retrieved.")
                
            db_resume.total_duration = time.time() - start_time
            await db.commit()
            
            results.append(BatchUploadResult(
                filename=file.filename,
                status="completed",
                resume_id=db_resume.id,
                trace_id=trace_id
            ))
            
        except Exception as e:
            await db.rollback()
            db_resume.status = "failed"
            db_resume.error_message = str(e)
            db_resume.parsing_duration = parsing_duration
            db_resume.extraction_duration = extraction_duration
            db_resume.indexing_duration = indexing_duration
            db_resume.verification_duration = verification_duration
            db_resume.total_duration = time.time() - start_time
            
            await db.commit()
            
            print(f"[{trace_id}] Batch item failed: {str(e)}")
            results.append(BatchUploadResult(
                filename=file.filename,
                status="failed",
                error=str(e),
                trace_id=trace_id
            ))
            
    return results
