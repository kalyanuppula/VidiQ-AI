import json
from pathlib import Path


def save_transcript(
    transcription: dict,
    output_path: str,
) -> dict:
    """
    Save a timestamped transcription as a JSON file.
    """

    if not isinstance(transcription, dict):
        raise ValueError("Transcription must be a dictionary.")

    if not isinstance(transcription.get("segments"), list):
        raise ValueError("Transcription must contain a segments list.")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    with output.open("w", encoding="utf-8") as file:
        json.dump(
            transcription,
            file,
            indent=4,
            ensure_ascii=False,
        )

    return {
        "output_file": str(output),
        "segments_saved": len(transcription["segments"]),
        "file_size_kb": round(output.stat().st_size / 1024, 2),
    }