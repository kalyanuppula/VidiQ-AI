import re
from app.services.multimodal.visual_analyzer import (
    get_gemini_client,
    MODEL_NAME,
)


def generate_grounded_answer(
    query: str,
    evidence: list[dict],
) -> dict:
    """
    Generate an answer using retrieved video evidence.

    Answers must be grounded in the supplied evidence and
    cite supporting timestamps and evidence IDs.
    """

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must not be empty.")

    if not isinstance(evidence, list):
        raise TypeError("Evidence must be provided as a list.")

    if not evidence:
        return {
            "status": "insufficient_evidence",
            "answer": (
                "I couldn't find relevant evidence in the "
                "available video content to answer this question."
            ),
            "model": MODEL_NAME,
            "sources": [],
        }

    context_parts = []
    sources = []
    source_lookup = {}

    for item in evidence:
        required_fields = [
            "evidence_id",
            "evidence_type",
            "timestamp",
            "text",
        ]

        if any(field not in item for field in required_fields):
            raise ValueError(
                "Evidence is missing required fields."
            )

        evidence_id = item["evidence_id"]
        evidence_type = item["evidence_type"]
        timestamp = item["timestamp"]
        text = item["text"]

        if not isinstance(text, str) or not text.strip():
            continue

        context_parts.append(
            f"""
Evidence ID: {evidence_id}
Evidence Type: {evidence_type}
Timestamp: {timestamp}
Content:
{text}
"""
        )

        source = {
            "evidence_id": evidence_id,
            "evidence_type": evidence_type,
            "timestamp": timestamp,
        }
        sources.append(source)
        source_lookup[evidence_id] = source

    if not context_parts:
        return {
            "status": "insufficient_evidence",
            "answer": (
                "The retrieved evidence does not contain "
                "usable information to answer this question."
            ),
            "model": MODEL_NAME,
            "sources": [],
        }

    context = "\n".join(context_parts)

    prompt = f"""
You are VidiQ AI, an enterprise video intelligence assistant.

Answer the user's question using ONLY the supplied evidence.

USER QUESTION:
{query}

RETRIEVED VIDEO EVIDENCE:
{context}

INSTRUCTIONS:

1. Use only information explicitly supported by the evidence.
2. Do not invent facts, events, people, or activities.
3. Cite supporting evidence using its timestamp and evidence ID.
   Example: [00:01:11 | transcript_000006]
4. Distinguish spoken statements from visual observations.
5. Do not claim that something is visually visible based only
   on transcript evidence.
6. If the evidence is insufficient, clearly say so.
7. If sources disagree or are unclear, explain the uncertainty.
8. Give a direct, concise and useful answer.
9. When information is not present in the supplied evidence,
   say it cannot be determined from the retrieved evidence.
   Never claim that something is absent from the entire video
   unless the complete video has been examined.
Return the answer as readable text with inline citations.
"""

    client = get_gemini_client()

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=[
            {
                "type": "text",
                "text": prompt,
            }
        ],
        timeout=90,
    )

    answer = (interaction.output_text or "").strip()

    if not answer:
        raise RuntimeError(
            "Gemini returned an empty answer."
        )

    # Extract citations in the expected format:
    # [00:01:11 | transcript_000006]
    citation_pattern = re.compile(
        r"\[(\d{2}:\d{2}:\d{2})\s*\|\s*([A-Za-z0-9_-]+)\]"
    )

    citations = citation_pattern.findall(answer)

    cited_sources = []
    citation_errors = []

    for timestamp, evidence_id in citations:

        if evidence_id not in source_lookup:
            citation_errors.append(
                f"Unknown evidence ID: {evidence_id}"
            )
            continue

        source = source_lookup[evidence_id]

        if timestamp != source["timestamp"]:
            citation_errors.append(
                f"Timestamp mismatch for {evidence_id}: "
                f"expected {source['timestamp']}, got {timestamp}"
            )
            continue

        if source not in cited_sources:
            cited_sources.append(source)

    # Accept explicit abstention without citations.
    abstention_phrases = [
        "cannot be determined",
        "insufficient evidence",
        "couldn't find relevant evidence",
        "not enough information",
        "does not contain usable information",
    ]

    is_abstention = any(
        phrase in answer.lower()
        for phrase in abstention_phrases
    )

    if citation_errors or (not citations and not is_abstention):
        return {
            "status": "citation_validation_failed",
            "answer": (
                "The generated answer could not pass citation "
                "validation. Please retry or inspect the evidence."
            ),
            "model": MODEL_NAME,
            "retrieved_sources": sources,
            "cited_sources": cited_sources,
            "citation_errors": citation_errors,
        }

    return {
        "status": (
            "insufficient_evidence"
            if is_abstention
            else "completed"
        ),
        "answer": answer,
        "model": MODEL_NAME,
        "retrieved_sources": sources,
        "cited_sources": cited_sources,
        "sources": cited_sources,
    }
