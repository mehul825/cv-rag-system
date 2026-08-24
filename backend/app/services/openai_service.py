import json
import urllib.request
import urllib.error

from openai import OpenAI
from app.core.config import settings


def get_gpu_client() -> OpenAI:
    """
    Initialize the OpenAI client for the serverless GPU endpoint.
    """
    api_key = settings.GPU_API_KEY or settings.OPENAI_API_KEY

    return OpenAI(
        base_url=settings.GPU_ENDPOINT_URL,
        api_key=api_key,
    )


def get_embedding_client() -> OpenAI:
    """
    Initialize the OpenAI client for the cloud embedding endpoint.
    """
    api_key = settings.CLOUD_EMBEDDING_KEY

    return OpenAI(
        base_url=settings.CLOUD_EMBEDDING_URL,
        api_key=api_key,
    )


def generate_embedding(text: str) -> list[float]:
    """
    Generate an embedding vector for one text.
    """
    embeddings = generate_embeddings_batch([text])

    if not embeddings:
        raise RuntimeError(
            "Failed to generate embedding: empty response from provider"
        )

    return embeddings[0]


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings for multiple texts using Hugging Face Inference API.
    """

    if not texts:
        return []

    # Get the Hugging Face API base URL
    base_url = settings.CLOUD_EMBEDDING_URL.rstrip("/")

    # If URL ends with /v1, convert it to the hf-inference endpoint
    if base_url.endswith("/v1"):
        base_url = base_url[:-3] + "/hf-inference"

    # Final Hugging Face model URL
    url = f"{base_url}/models/{settings.CLOUD_EMBEDDING_MODEL}"

    # Clean input text
    payload = {
        "inputs": [
            text.replace("\n", " ")
            for text in texts
        ]
    }

    # IMPORTANT:
    # CLOUD_EMBEDDING_KEY must contain your Hugging Face token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.CLOUD_EMBEDDING_KEY}",
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            response_body = response.read().decode("utf-8")
            response_data = json.loads(response_body)

            # Hugging Face error response
            if isinstance(response_data, dict):
                raise RuntimeError(
                    f"Unexpected response from Hugging Face: {response_data}"
                )

            # Single embedding returned as:
            # [0.123, 0.456, ...]
            if (
                isinstance(response_data, list)
                and len(response_data) > 0
                and isinstance(response_data[0], (float, int))
            ):
                return [
                    [float(value) for value in response_data]
                ]

            # Multiple embeddings returned as:
            # [[0.123, ...], [0.456, ...]]
            if isinstance(response_data, list):
                return response_data

            raise ValueError(
                f"Unexpected response format from Hugging Face: "
                f"{type(response_data)}"
            )

    except urllib.error.HTTPError as e:
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            error_body = str(e)

        print(
            f"""
--- EMBEDDING SERVICE FAILURE ---
URL: {url}
HTTP STATUS: {e.code}
ERROR: {error_body}
---------------------------------
""",
            flush=True,
        )

        raise RuntimeError(
            f"Hugging Face embedding extraction failed: {error_body}"
        )

    except Exception as e:
        print(
            f"""
--- EMBEDDING SERVICE FAILURE ---
URL: {url}
ERROR: {str(e)}
---------------------------------
""",
            flush=True,
        )

        raise RuntimeError(
            f"Hugging Face embedding extraction failed: {str(e)}"
        )


def ask_question_with_context(
    question: str,
    context_chunks: list[str],
    filename: str,
) -> str:
    """
    Query the LLM using the matching CV chunks as context.
    """

    client = get_gpu_client()
    model_name = settings.GPU_MODEL_NAME

    # Format context chunks with source numbers
    formatted_chunks = []

    for index, chunk in enumerate(context_chunks, start=1):
        formatted_chunks.append(
            f"[{index}] {chunk}"
        )

    context_text = "\n\n---\n\n".join(formatted_chunks)

    system_prompt = (
        "You are an expert recruiter and CV analyst.\n"
        f"You are answering a user's question about the CV/Resume file: "
        f"'{filename}'.\n\n"
        "Use ONLY the following numbered context blocks extracted from "
        "the CV to answer the question.\n\n"
        "Cite the sources you use by appending their corresponding index "
        "numbers, for example [1] or [2], at the end of the sentence.\n\n"
        "If the answer is not present in the provided context, say so "
        "honestly and clearly. Do not invent facts or citations.\n\n"
        "Keep your answer professional, clear, and concise.\n\n"
        "Context extracted from CV:\n"
        f"{context_text}"
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content