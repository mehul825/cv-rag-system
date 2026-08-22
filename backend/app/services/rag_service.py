import math
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.resume import ResumeChunk
from app.services.openai_service import generate_embedding

def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    """
    Calculates cosine similarity between two vectors.
    """
    dot = sum(x * y for x, y in zip(v1, v2))
    norm1 = math.sqrt(sum(x * x for x in v1))
    norm2 = math.sqrt(sum(y * y for y in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)

async def retrieve_relevant_chunks(
    db: AsyncSession, 
    resume_id: int, 
    query_text: str, 
    top_k: int = 5
) -> list[ResumeChunk]:
    """
    Retrieves the top K most relevant text chunks from the database for a query and resume.
    """
    # Generate vector embedding for the search query
    query_emb = generate_embedding(query_text)
    
    # Retrieve all chunks associated with this resume
    stmt = select(ResumeChunk).where(ResumeChunk.resume_id == resume_id)
    result = await db.execute(stmt)
    chunks = result.scalars().all()
    
    if not chunks:
        return []
        
    # Rank chunks by their cosine similarity to the query
    scored_chunks = []
    for chunk in chunks:
        # chunk.embedding is stored as a JSON array of floats in database
        score = cosine_similarity(query_emb, chunk.embedding)
        scored_chunks.append((score, chunk))
        
    # Sort descending by score
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    
    # Return top K chunks
    return [chunk for score, chunk in scored_chunks[:top_k]]
