from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


project_dir = Path(__file__).resolve().parent
chroma_dir = project_dir / "data" / "chroma"

client = chromadb.PersistentClient(path=str(chroma_dir))
collection = client.get_collection("enterprise-docs")
model = SentenceTransformer("all-MiniLM-L6-v2")

question = input("Ask a question: ")
embedding = model.encode([question]).tolist()
results = collection.query(query_embeddings=embedding, n_results=3)

documents = results["documents"][0]
metadatas = results["metadatas"][0]

for number, (document, metadata) in enumerate(zip(documents, metadatas), start=1):
    print(f"\nResult {number}")
    print(f"Source: {metadata['source']}")
    print(document[:700])