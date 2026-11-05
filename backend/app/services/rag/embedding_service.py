from functools import lru_cache

from sentence_transformers import SentenceTransformer


MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384


@lru_cache(maxsize=1)
def get_embedding_model():
    """
    Load and cache the local sentence embedding model.
    """

    return SentenceTransformer(
        MODEL_NAME,
        device="cpu",
    )


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """
    Generate normalized embeddings for a list of texts.
    """

    if not isinstance(texts, list):
        raise TypeError("Texts must be provided as a list.")

    if not texts:
        return []

    if any(
        not isinstance(text, str) or not text.strip()
        for text in texts
    ):
        raise ValueError(
            "Every text must be a non-empty string."
        )

    model = get_embedding_model()

    embeddings = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )

    if embeddings.shape != (
        len(texts),
        EMBEDDING_DIMENSION,
    ):
        raise RuntimeError(
            "Unexpected embedding dimensions."
        )

    return embeddings.tolist()