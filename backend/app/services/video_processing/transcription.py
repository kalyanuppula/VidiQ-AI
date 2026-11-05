
from functools import lru_cache
from pathlib import Path

from faster_whisper import WhisperModel


@lru_cache(maxsize=2)
def load_whisper_model(model_size: str = "tiny"):
    """
    Load and cache a Faster-Whisper model.
    """

    return WhisperModel(
        model_size,
        device="cpu",
        compute_type="int8",
    )


def transcribe_audio(
    audio_path: str,
    model_size: str = "tiny",
) -> dict:
    """
    Transcribe audio and return timestamped segments.
    """

    path = Path(audio_path)

    if not path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    if path.stat().st_size == 0:
        raise ValueError("Audio file is empty.")

    model = load_whisper_model(model_size)

    segments, info = model.transcribe(
        str(path),
        beam_size=5,
        vad_filter=True,
    )

    transcript_segments = []

    for segment in segments:
        transcript_segments.append({
            "start": round(segment.start, 2),
            "end": round(segment.end, 2),
            "text": segment.text.strip(),
        })

    full_text = " ".join(
        segment["text"] for segment in transcript_segments
    )

    return {
        "audio_file": path.name,
        "model": model_size,
        "language": info.language,
        "language_probability": round(
            info.language_probability, 3
        ),
        "duration_seconds": round(info.duration, 2),
        "full_text": full_text,
        "segments": transcript_segments,
    }
