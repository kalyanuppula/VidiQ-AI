
import re
from pathlib import Path

import chromadb
from rank_bm25 import BM25Okapi

from app.services.rag.embedding_service import generate_embeddings
from app.services.rag.vector_store import COLLECTION_NAME, DATABASE_PATH


TRANSCRIPT_KEYWORDS = {
    "discuss", "discussed", "explain", "explained",
    "say", "said", "talk", "talked", "mention", "mentioned",
    "describe", "described", "why", "research", "prevent",
    "fatalities", "safety", "hazards", "risk", "risks",
    "worker", "workers", "robot", "robots",
    "what are the risks", "what hazards",
    "what safety hazards", "what procedures",
}

VISUAL_KEYWORDS = {
    "visible", "shown", "look", "looks", "appear", "appears",
    "wearing", "wear", "color", "colour", "equipment",
    "objects", "person", "people", "worker", "workers",
    "image", "frame", "scene", "button",
}


RRF_K = 60


def tokenize(text: str) -> list[str]:
    """Convert text into lowercase word tokens."""

    return re.findall(r"\b[a-z0-9]+\b", text.lower())


def classify_query(query: str) -> str:
    """Identify the likely evidence modality requested."""

    normalized_query = query.lower()

    transcript_score = sum(
        keyword in normalized_query
        for keyword in TRANSCRIPT_KEYWORDS
    )

    visual_score = sum(
        keyword in normalized_query
        for keyword in VISUAL_KEYWORDS
    )

    if transcript_score > visual_score:
        return "transcript"

    if visual_score > transcript_score:
        return "visual"

    return "both"


def reciprocal_rank_fusion(
    rankings: list[list[dict]],
) -> list[dict]:
    """Combine multiple ranked lists using RRF."""

    fused = {}

    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            evidence_id = item["evidence_id"]

            if evidence_id not in fused:
                fused[evidence_id] = {
                    **item,
                    "rrf_score": 0.0,
                }

            fused[evidence_id]["rrf_score"] += (
                1.0 / (RRF_K + rank)
            )

    return sorted(
        fused.values(),
        key=lambda item: item["rrf_score"],
        reverse=True,
    )


def search_evidence(
    query: str,
    top_k: int = 5,
    video_id: str | None = None,
) -> list[dict]:
    """
    Retrieve evidence using semantic search, BM25 and RRF.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must not be empty.")

    if isinstance(top_k, bool) or not isinstance(top_k, int) or top_k < 1:
        raise ValueError("top_k must be a positive integer.")

    database_path = Path(DATABASE_PATH)

    if not database_path.is_dir():
        raise FileNotFoundError(
            "ChromaDB database not found. Index evidence first."
        )

    client = chromadb.PersistentClient(
        path=str(database_path)
    )

    try:
        collection = client.get_collection(
            name=COLLECTION_NAME
        )
    except Exception as exc:
        raise RuntimeError(
            "VidiQ evidence collection was not found."
        ) from exc

    preferred_type = classify_query(query)
    query_embedding = generate_embeddings([query])[0]

    modality_rankings = {}

    candidate_limit = max(top_k * 3, 10)

    for evidence_type in ["transcript", "visual"]:

        where = {"evidence_type": evidence_type}

        if video_id:
            where = {
                "$and": [
                    {"evidence_type": evidence_type},
                    {"video_id": video_id},
                ]
            }

        records = collection.get(
            where=where,
            include=["documents", "metadatas"],
        )

        ids = records["ids"]
        documents = records["documents"]
        metadatas = records["metadatas"]

        if not ids:
            modality_rankings[evidence_type] = []
            continue

        # Build records with their original metadata.
        evidence_records = []

        for index, evidence_id in enumerate(ids):
            metadata = metadatas[index]

            evidence_records.append({
                "evidence_id": evidence_id,
                "video_id": metadata["video_id"],
                "evidence_type": metadata["evidence_type"],
                "start_seconds": metadata["start_seconds"],
                "end_seconds": metadata["end_seconds"],
                "timestamp": metadata["timestamp"],
                "text": documents[index],
            })

        # 1. Semantic search.
        semantic_results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(candidate_limit, len(ids)),
            where=where,
            include=["distances"],
        )

        semantic_ranking = []

        for rank, evidence_id in enumerate(
            semantic_results["ids"][0]
        ):
            record = next(
                item for item in evidence_records
                if item["evidence_id"] == evidence_id
            )

            record = record.copy()
            record["distance"] = (
                semantic_results["distances"][0][rank]
            )

            semantic_ranking.append(record)

        # 2. BM25 keyword search.
        tokenized_documents = [
            tokenize(item["text"])
            for item in evidence_records
        ]

        query_tokens = tokenize(query)

        if query_tokens and any(tokenized_documents):
            bm25 = BM25Okapi(tokenized_documents)
            scores = bm25.get_scores(query_tokens)

            bm25_order = sorted(
                range(len(scores)),
                key=lambda index: scores[index],
                reverse=True,
            )

            bm25_ranking = []

            for index in bm25_order[:candidate_limit]:
                record = evidence_records[index].copy()
                record["bm25_score"] = float(scores[index])
                bm25_ranking.append(record)

        else:
            bm25_ranking = []

        # 3. Fuse semantic and keyword rankings.
        modality_rankings[evidence_type] = (
            reciprocal_rank_fusion([
                semantic_ranking,
                bm25_ranking,
            ])
        )

    transcript_results = modality_rankings["transcript"]
    visual_results = modality_rankings["visual"]

    if preferred_type == "transcript":
        primary = transcript_results
        secondary = visual_results

    elif preferred_type == "visual":
        primary = visual_results
        secondary = transcript_results

    else:
        transcript_count = (top_k + 1) // 2
        visual_count = top_k // 2

        return (
            transcript_results[:transcript_count]
            + visual_results[:visual_count]
        )[:top_k]

    primary_count = max(1, top_k - 1)
    secondary_count = top_k - primary_count

    return (
        primary[:primary_count]
        + secondary[:secondary_count]
    )[:top_k]
