
import json
import urllib.request
import urllib.error

from openai import OpenAI
from app.core.config import settings


def get_gpu_client() -> OpenAI:
    """
    Initialize the OpenAI-compatible client for the serverless GPU endpoint.
    """
    api_key = settings.GPU_API_KEY or settings.OPENAI_API_KEY

    return OpenAI(
        base_url=settings.GPU_ENDPOINT_URL,
        api_key=api_key,
    )


def get_embedding_client() -> OpenAI:
    """
    Retained for compatibility with existing code.
    Gemini embeddings are called through the REST API below.
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
            "Failed to generate embedding: empty response from Gemini."
        )

    return embeddings[0]


def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """
    Generate embeddings using Google's Gemini Embedding API.

    Uses CLOUD_EMBEDDING_KEY for the Google API key.
    Requests 768-dimensional vectors.
    """

    if not texts:
        return []

    api_key = settings.CLOUD_EMBEDDING_KEY

    if not api_key:
        raise RuntimeError(
            "Missing CLOUD_EMBEDDING_KEY. Add your Google Gemini API key "
            "to the backend environment variables."
        )

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        "models/gemini-embedding-2:embedContent"
    )

    embeddings: list[list[float]] = []

    for text in texts:
        payload = {
            "content": {
                "parts": [
                    {
                        "text": text.replace("\n", " ")
                    }
                ]
            },
            "output_dimensionality": 768,
        }

        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                response_data = json.loads(
                    response.read().decode("utf-8")
                )

            values = (
                response_data
                .get("embedding", {})
                .get("values")
            )

            if not values:
                raise RuntimeError(
                    f"Gemini returned no embedding: {response_data}"
                )

            embeddings.append(
                [float(value) for value in values]
            )

        except urllib.error.HTTPError as error:
            error_body = error.read().decode(
                "utf-8",
                errors="replace",
            )

            raise RuntimeError(
                f"Gemini embedding API failed (HTTP {error.code}): "
                f"{error_body}"
            ) from error

        except urllib.error.URLError as error:
            raise RuntimeError(
                f"Could not connect to Gemini embedding API: {error}"
            ) from error

    return embeddings


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

    answer = response.choices[0].message.content

    return answer or ""
