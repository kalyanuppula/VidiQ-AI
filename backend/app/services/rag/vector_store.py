from pathlib import Path

import chromadb

from app.services.rag.embedding_service import generate_embeddings


COLLECTION_NAME = "vidiq_video_evidence"
DATABASE_PATH = Path("data/chroma_db")


def get_chroma_client():
    """Create a persistent ChromaDB client."""

    DATABASE_PATH.mkdir(parents=True, exist_ok=True)

    return chromadb.PersistentClient(
        path=str(DATABASE_PATH)
    )


def index_evidence(
    evidence_path: str | Path,
) -> dict:
    """
    Generate embeddings and store video evidence
    in a persistent ChromaDB collection.
    """

    evidence_path = Path(evidence_path)

    if not evidence_path.is_file():
        raise FileNotFoundError(
            f"Evidence file not found: {evidence_path}"
        )

    import json

    with evidence_path.open(encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data.get("evidence"), list):
        raise ValueError("Invalid evidence dataset.")

    records = data["evidence"]

    if not records:
        raise ValueError("No evidence records to index.")

    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [record["text"] for record in records]
    embeddings = generate_embeddings(texts)

    collection.upsert(
        ids=[record["evidence_id"] for record in records],
        embeddings=embeddings,
        documents=texts,
        metadatas=[
            {
                "video_id": record["video_id"],
                "evidence_type": record["evidence_type"],
                "start_seconds": record["start_seconds"],
                "end_seconds": record["end_seconds"],
                "timestamp": record["timestamp"],
                "source": record["source"],
            }
            for record in records
        ],
    )

    return {
        "status": "completed",
        "collection": COLLECTION_NAME,
        "indexed_records": len(records),
        "collection_total": collection.count(),
    }