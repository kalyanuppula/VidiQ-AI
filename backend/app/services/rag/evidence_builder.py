import json
from pathlib import Path


def format_timestamp(seconds: float) -> str:
    total_seconds = int(seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    remaining_seconds = total_seconds % 60

    return (
        f"{hours:02d}:"
        f"{minutes:02d}:"
        f"{remaining_seconds:02d}"
    )


def build_evidence(
    transcript_path: str | Path,
    visual_analysis_path: str | Path,
    output_path: str | Path | None = None,
    video_id: str | None = None,
) -> dict:
    """
    Combine transcript segments and visual descriptions
    into a unified, timestamped evidence dataset.
    """

    transcript_path = Path(transcript_path)
    visual_analysis_path = Path(visual_analysis_path)

    if not transcript_path.is_file():
        raise FileNotFoundError(
            f"Transcript file not found: {transcript_path}"
        )

    if not visual_analysis_path.is_file():
        raise FileNotFoundError(
            f"Visual analysis file not found: {visual_analysis_path}"
        )

    with transcript_path.open(encoding="utf-8") as file:
        transcript_data = json.load(file)

    with visual_analysis_path.open(encoding="utf-8") as file:
        visual_data = json.load(file)

    transcript_segments = transcript_data.get("segments", [])
    visual_descriptions = visual_data.get(
        "visual_descriptions", []
    )

    if not isinstance(transcript_segments, list):
        raise ValueError("Transcript segments must be a list.")

    if not isinstance(visual_descriptions, list):
        raise ValueError("Visual descriptions must be a list.")

    resolved_video_id = (
        video_id
        or visual_data.get("video_id")
        or "unknown_video"
    )

    evidence = []

    # Convert transcript segments into evidence records.
    for index, segment in enumerate(transcript_segments, start=1):
        start = float(segment["start"])
        end = float(segment["end"])
        text = str(segment.get("text", "")).strip()

        if not text:
            continue

        if start < 0 or end < start:
            raise ValueError(
                f"Invalid transcript timestamps at segment {index}."
            )

        evidence.append({
            "evidence_id": f"transcript_{index:06d}",
            "video_id": resolved_video_id,
            "evidence_type": "transcript",
            "start_seconds": start,
            "end_seconds": end,
            "timestamp": format_timestamp(start),
            "text": text,
            "source": transcript_path.name,
        })

    # Convert visual descriptions into evidence records.
    for index, frame in enumerate(visual_descriptions, start=1):
        timestamp = float(frame["timestamp_seconds"])
        description = str(
            frame.get("description", "")
        ).strip()

        if not description:
            continue

        if timestamp < 0:
            raise ValueError(
                f"Invalid visual timestamp at frame {index}."
            )

        evidence.append({
            "evidence_id": f"visual_{index:06d}",
            "video_id": resolved_video_id,
            "evidence_type": "visual",
            "start_seconds": timestamp,
            "end_seconds": timestamp,
            "timestamp": format_timestamp(timestamp),
            "text": description,
            "source": visual_analysis_path.name,
        })

    # Sort evidence chronologically.
    evidence.sort(
        key=lambda item: (
            item["start_seconds"],
            item["evidence_type"],
        )
    )

    result = {
        "status": "completed",
        "video_id": resolved_video_id,
        "total_evidence": len(evidence),
        "transcript_evidence_count": sum(
            item["evidence_type"] == "transcript"
            for item in evidence
        ),
        "visual_evidence_count": sum(
            item["evidence_type"] == "visual"
            for item in evidence
        ),
        "evidence": evidence,
    }

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    return result