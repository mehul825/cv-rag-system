import json
import urllib.request
from openai import OpenAI
from app.core.config import settings

def get_gpu_client() -> OpenAI:
    """
    Helper to initialize the OpenAI client pointing to the serverless GPU endpoint.
    """
    api_key = settings.GPU_API_KEY or settings.OPENAI_API_KEY
    return OpenAI(
        base_url=settings.GPU_ENDPOINT_URL,
        api_key=api_key
    )

def get_embedding_client() -> OpenAI:
    """
    Helper to initialize the OpenAI client pointing to the cloud embedding endpoint.
    """
    api_key = settings.CLOUD_EMBEDDING_KEY or settings.GPU_API_KEY or settings.OPENAI_API_KEY
    return OpenAI(
        base_url=settings.CLOUD_EMBEDDING_URL,
        api_key=api_key
    )

def generate_embedding(text: str) -> list[float]:
    """
    Generates a vector embedding for the input text using the cloud embedding model.
    """
    embeddings = generate_embeddings_batch([text])
    if not embeddings:
        raise RuntimeError("Failed to generate embedding: empty response from provider")
    return embeddings[0]

def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generates vector embeddings for a list of texts in a single batch API call
    using the Hugging Face Inference API.
    """
    if not texts:
        return []
        
    # Construct correct Hugging Face Inference API URL using the router
    base_url = settings.CLOUD_EMBEDDING_URL
    if base_url.endswith("/v1"):
        base_url = base_url[:-3] + "/hf-inference"
    elif base_url.endswith("/v1/"):
        base_url = base_url[:-4] + "/hf-inference"
        
    url = f"{base_url}/models/{settings.CLOUD_EMBEDDING_MODEL}"
    
    payload = {"inputs": [t.replace("\n", " ") for t in texts]}
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.CLOUD_EMBEDDING_KEY or settings.GPU_API_KEY or settings.OPENAI_API_KEY}"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req) as res:
            response_data = json.loads(res.read().decode("utf-8"))
            
            # Hugging Face Feature Extraction API returns a list of floats (if 1 input) 
            # or list of list of floats (if multiple inputs).
            if isinstance(response_data, list):
                if len(response_data) > 0 and isinstance(response_data[0], float):
                    return [response_data]
                return response_data
            raise ValueError(f"Unexpected response format from Hugging Face: {type(response_data)}")
            
    except Exception as e:
        status_code = getattr(e, "code", "Unknown")
        response_body = "Unknown Error"
        if hasattr(e, "read"):
            try:
                response_body = e.read().decode("utf-8")
            except Exception:
                pass
        
        # Log clear backend error details
        error_msg = (
            f"--- EMBEDDING SERVICE FAILURE DETAILS ---\n"
            f"Service: Hugging Face Inference API (feature-extraction)\n"
            f"Requested URL: {url}\n"
            f"HTTP Status Code: {status_code}\n"
            f"Error message: {str(e)}\n"
            f"Response body: {response_body}\n"
            f"----------------------------------------"
        )
        print(error_msg, flush=True)
        raise RuntimeError(f"Hugging Face embedding extraction failed: {response_body or str(e)}")

def ask_question_with_context(question: str, context_chunks: list[str], filename: str) -> str:
    """
    Queries the LLM with matching resume chunks as context.
    Uses the serverless self-hosted GPU endpoint.
    """
    client = get_gpu_client()
    model_name = settings.GPU_MODEL_NAME
    
    # Format context with chunk indices [1], [2], etc.
    formatted_chunks = []
    for idx, chunk in enumerate(context_chunks, 1):
        formatted_chunks.append(f"[{idx}] {chunk}")
        
    context_text = "\n\n---\n\n".join(formatted_chunks)
    
    system_prompt = (
        "You are an expert recruiter and CV analyst.\n"
        f"You are answering a user's question about the CV/Resume file: '{filename}'.\n"
        "Use ONLY the following numbered context blocks extracted from the CV to answer the question. "
        "Cite the sources you use in your response by appending their corresponding index numbers (e.g. [1], [2]) "
        "at the end of sentences that use facts from those blocks. "
        "If you do not know the answer or if the context does not contain the answer, say so "
        "honestly, and clearly state that no strong source was found. Do not invent any citations or facts.\n"
        "Keep your answer professional, clear, and concise.\n\n"
        "Context extracted from CV:\n"
        f"{context_text}"
    )
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question}
        ],
        temperature=0.2
    )
    
    return response.choices[0].message.content
