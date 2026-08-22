from openai import OpenAI
from app.core.config import settings

def get_openai_client() -> OpenAI:
    """
    Helper to initialize the OpenAI client pointing to Ollama's local endpoint.
    """
    return OpenAI(
        base_url=settings.OLLAMA_BASE_URL,
        api_key="ollama"  # Ollama compatibility endpoint requires a dummy key
    )

def generate_embedding(text: str) -> list[float]:
    """
    Generates a vector embedding for the input text using the local embedding model.
    """
    client = get_openai_client()
    response = client.embeddings.create(
        input=[text.replace("\n", " ")],
        model=settings.OLLAMA_EMBEDDING_MODEL
    )
    return response.data[0].embedding

def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generates vector embeddings for a list of texts in a single batch API call.
    """
    if not texts:
        return []
    client = get_openai_client()
    processed_texts = [t.replace("\n", " ") for t in texts]
    response = client.embeddings.create(
        input=processed_texts,
        model=settings.OLLAMA_EMBEDDING_MODEL
    )
    return [item.embedding for item in response.data]

def ask_question_with_context(question: str, context_chunks: list[str], filename: str) -> str:
    """
    Queries the local Ollama LLM with matching resume chunks as context.
    """
    client = get_openai_client()
    
    context_text = "\n\n---\n\n".join(context_chunks)
    
    system_prompt = (
        "You are an expert recruiter and CV analyst.\n"
        f"You are answering a user's question about the CV/Resume file: '{filename}'.\n"
        "Use ONLY the following context extracted from the CV to answer the question. "
        "If you do not know the answer or if the context does not contain the answer, say so "
        "honestly. Do not make up any facts or information.\n"
        "Keep your answer professional, clear, and concise.\n\n"
        "Context extracted from CV:\n"
        f"{context_text}"
    )
    
    response = client.chat.completions.create(
        model=settings.OLLAMA_CHAT_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.2
    )
    
    return response.choices[0].message.content

