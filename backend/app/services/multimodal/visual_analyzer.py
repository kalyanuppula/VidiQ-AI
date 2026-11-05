import os
import base64
import math
from functools import lru_cache
from pathlib import Path

# Work around slow Pydantic plugin discovery on this machine.
os.environ.setdefault("PYDANTIC_DISABLE_PLUGINS", "__all__")

from dotenv import load_dotenv
from google import genai
from google.genai import types


MODEL_NAME = "gemini-3.5-flash-lite"

# Timeout and retry settings
REQUEST_TIMEOUT_MS = 60_000
OVERALL_REQUEST_TIMEOUT_SECONDS = 90

# Load the API key from backend/.env
BACKEND_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BACKEND_DIR / ".env")


@lru_cache(maxsize=1)
def get_gemini_client():
    """Create and reuse the Gemini API client."""

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. Check backend/.env"
        )

    retry_options = types.HttpRetryOptions(
        attempts=3,
        initial_delay=1.0,
        max_delay=8.0,
        http_status_codes=[408, 429, 500, 502, 503, 504],
    )

    http_options = types.HttpOptions(
        timeout=REQUEST_TIMEOUT_MS,
        retry_options=retry_options,
    )

    return genai.Client(
        api_key=api_key,
        http_options=http_options,
    )


def get_mime_type(image_path: Path) -> str:
    """Identify the supported image format."""

    extension = image_path.suffix.lower()

    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    if extension not in mime_types:
        raise ValueError(
            f"Unsupported image format: {extension}"
        )

    return mime_types[extension]


def format_timestamp(seconds: float) -> str:
    """Convert seconds into HH:MM:SS format."""

    total_seconds = int(seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{remaining_seconds:02d}"
    )


def analyze_frame(
    image_path: str | Path,
    timestamp_seconds: float,
    video_id: str | None = None,
) -> dict:
    """
    Analyze one extracted video frame using Gemini.

    Returns a visual description linked to its video timestamp.
    """

    image_path = Path(image_path)

    if not image_path.exists() or not image_path.is_file():
        raise FileNotFoundError(
            f"Frame not found: {image_path}"
        )

    if (
        isinstance(timestamp_seconds, bool)
        or not isinstance(timestamp_seconds, (int, float))
        or not math.isfinite(timestamp_seconds)
        or timestamp_seconds < 0
    ):
        raise ValueError(
            "Timestamp must be a finite, non-negative number."
        )

    mime_type = get_mime_type(image_path)

    image_bytes = image_path.read_bytes()

    if not image_bytes:
        raise ValueError(f"Frame is empty: {image_path}")

    image_base64 = base64.b64encode(
        image_bytes
    ).decode("utf-8")

    prompt = (
        "Analyze this frame from an enterprise training or "
        "operational video. Describe only what is visibly "
        "supported. Identify visible people, objects, equipment, "
        "activities, possible safety-related observations, and "
        "readable text. Do not guess identities, intentions, or "
        "hidden details. Distinguish direct observations from "
        "possible concerns. Do not claim a safety violation "
        "without sufficient evidence. If something is unclear, "
        "say so."
    )

    client = get_gemini_client()

    interaction = client.interactions.create(
        model=MODEL_NAME,
        input=[
            {
                "type": "text",
                "text": prompt,
            },
            {
                "type": "image",
                "data": image_base64,
                "mime_type": mime_type,
            },
        ],
        timeout=OVERALL_REQUEST_TIMEOUT_SECONDS,
    )

    description = (
        interaction.output_text or ""
    ).strip()

    if not description:
        raise RuntimeError(
            "Gemini returned an empty description."
        )

    return {
        "video_id": video_id,
        "timestamp_seconds": round(
            float(timestamp_seconds), 3
        ),
        "timestamp": format_timestamp(timestamp_seconds),
        "frame_path": str(image_path),
        "description": description,
        "model": MODEL_NAME,
    }