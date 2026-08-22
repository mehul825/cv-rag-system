from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.models.resume import Resume, ResumeChunk
from app.services.pdf_parser import extract_text_from_pdf, chunk_text
from app.services.openai_service import generate_embeddings_batch, ask_question_with_context
from app.services.rag_service import retrieve_relevant_chunks

router = APIRouter(prefix="/cv", tags=["CV RAG"])

# Pydantic Schemas
class ResumeResponse(BaseModel):
    id: int
    filename: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class QueryRequest(BaseModel):
    resume_id: int
    question: str

class QueryResponse(BaseModel):
    answer: str

@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_cv(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """
    Uploads a CV PDF, parses its text, chunks it, generates embeddings, and saves to database.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only PDF files are supported."
        )
    
    try:
        # Read file contents
        content = await file.read()
        
        # 1. Parse text from PDF
        parsed_text = extract_text_from_pdf(content)
        if not parsed_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to extract text from the provided PDF."
            )
        
        # 2. Chunk text
        chunks = chunk_text(parsed_text, chunk_size=800, chunk_overlap=150)
        if not chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The PDF contains insufficient text to chunk."
            )
            
        # 3. Generate embeddings for chunks in a single batch
        embeddings = generate_embeddings_batch(chunks)
        
        # 4. Save Resume & Chunks to Database
        db_resume = Resume(
            filename=file.filename,
            parsed_text=parsed_text
        )
        db.add(db_resume)
        await db.flush() # Fetch the resume id
        
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
        await db.commit()
        await db.refresh(db_resume)
        
        return db_resume
        
    except ValueError as ve:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(ve)
        )
    except Exception as e:
        await db.rollback()
        import traceback
        from app.core.config import settings
        print("--- DEBUG INFO ---")
        print("OPENAI_API_KEY configured (bool):", bool(settings.OPENAI_API_KEY))
        if settings.OPENAI_API_KEY:
            print("OPENAI_API_KEY length:", len(settings.OPENAI_API_KEY))
        traceback.print_exc()
        print("------------------")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while processing the CV: {str(e)}"
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
    Retrieves relevant resume chunks and queries OpenAI GPT model to answer a question.
    """
    # 1. Fetch resume
    stmt = select(Resume).where(Resume.id == request.resume_id)
    result = await db.execute(stmt)
    resume = result.scalar_one_or_none()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Resume with ID {request.resume_id} not found."
        )
        
    try:
        # 2. Retrieve relevant chunks
        matched_chunks = await retrieve_relevant_chunks(
            db=db,
            resume_id=request.resume_id,
            query_text=request.question,
            top_k=5
        )
        
        if not matched_chunks:
            return QueryResponse(
                answer="No relevant content found in the resume. Try asking a different question."
            )
            
        chunk_texts = [c.chunk_text for c in matched_chunks]
        
        # 3. Call OpenAI model to generate response
        answer = ask_question_with_context(
            question=request.question,
            context_chunks=chunk_texts,
            filename=resume.filename
        )
        
        return QueryResponse(answer=answer)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate response: {str(e)}"
        )
