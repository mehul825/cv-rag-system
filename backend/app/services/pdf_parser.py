import io
from typing import List
import pypdf

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts all readable text from a PDF file byte stream.
    """
    pdf_file = io.BytesIO(file_bytes)
    reader = pypdf.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

def chunk_text(text: str, chunk_size: int = 800, chunk_overlap: int = 150) -> List[str]:
    """
    Chunks text into small segments with overlap, ensuring words are not split in half.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        # Determine initial end of chunk
        end = min(start + chunk_size, text_len)
        
        # If not at the absolute end, search for a clean boundary (newline or space)
        if end < text_len:
            # Look back up to 80 characters for a line break or space
            last_space = text.rfind(" ", end - 80, end)
            last_newline = text.rfind("\n", end - 80, end)
            clean_break = max(last_space, last_newline)
            if clean_break > start:
                end = clean_break
                
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
            
        # Move the cursor forward by stepping to end and sliding back overlap
        next_start = end - chunk_overlap
        if next_start <= start:
            start = end # Step to end to guarantee progress and terminate the loop
        else:
            start = next_start
            
    return chunks
