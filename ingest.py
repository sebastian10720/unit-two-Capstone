from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


PROJECT_DIR = Path(__file__).resolve().parent
DOCUMENTS_DIR = PROJECT_DIR / "data" / "documents"
CHROMA_DIR = PROJECT_DIR / "data" / "chroma"
COLLECTION_NAME = "enterprise-docs"


def chunk_document(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    step = chunk_size - overlap
    return [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), step)
        if words[i:i + chunk_size]
    ]


def ingest_documents() -> None:
    text_files = sorted(DOCUMENTS_DIR.glob("*.txt"))

    if not text_files:
        raise FileNotFoundError(f"No .txt files found in {DOCUMENTS_DIR}")

    print("Loading embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")

    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    collection = chroma_client.get_or_create_collection(COLLECTION_NAME)

    total_chunks = 0

    for document_path in text_files:
        text = document_path.read_text(encoding="utf-8", errors="replace")
        chunks = chunk_document(text)

        if not chunks:
            print(f"Skipped empty document: {document_path.name}")
            continue

        embeddings = model.encode(chunks).tolist()
        ids = [f"{document_path.name}-{index}" for index in range(len(chunks))]
        metadata = [
            {"source": document_path.name, "chunk": index}
            for index in range(len(chunks))
        ]

        collection.upsert(
            documents=chunks,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadata,
        )

        total_chunks += len(chunks)
        print(f"Ingested {len(chunks)} chunks from {document_path.name}")

    print(f"Finished. Total chunks stored: {total_chunks}")
    print(f"ChromaDB location: {CHROMA_DIR}")


if __name__ == "__main__":
    ingest_documents()