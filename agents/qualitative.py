import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

load_dotenv()

PROJECT_DIR = Path(__file__).resolve().parents[1]
CHROMA_DIR = PROJECT_DIR / "data" / "chroma"
COLLECTION_NAME = "enterprise-docs"
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")


def retrieve(query: str, top_k: int = 5) -> list[dict]:
    chroma = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma.get_collection(COLLECTION_NAME)
    embedding = embedding_model.encode([query]).tolist()
    results = collection.query(query_embeddings=embedding, n_results=top_k)

    return [
        {
            "content": document,
            "source": metadata["source"],
            "chunk": metadata["chunk"],
        }
        for document, metadata in zip(
            results["documents"][0], results["metadatas"][0]
        )
    ]


def build_prompt(query: str, chunks: list[dict]) -> str:
    context = "\n\n".join(
        f"[Source {index}: {chunk['source']}, chunk {chunk['chunk']}]\n"
        f"{chunk['content']}"
        for index, chunk in enumerate(chunks, start=1)
    )

    return f"""You are an enterprise documentation assistant.

Use ONLY the provided context to answer the question.
Do not use outside knowledge or make unsupported assumptions.
If the answer is not in the context, say exactly:
"I cannot find this information in the provided documents."
Cite every factual statement with [Source number].

CONTEXT:
{context}

QUESTION:
{query}

ANSWER:"""


def run(query: str) -> dict:
    chunks = retrieve(query)
    prompt = build_prompt(query, chunks)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=700,
    )

    usage = response.usage
    return {
        "answer": response.choices[0].message.content,
        "chunks": chunks,
        "input_tokens": usage.prompt_tokens if usage else 0,
        "output_tokens": usage.completion_tokens if usage else 0,
    }