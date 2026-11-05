import json
from pathlib import Path

from app.services.multimodal.visual_analyzer import (
    analyze_frame,
    MODEL_NAME,
)


def analyze_video_frames(
    manifest_path: str | Path,
    output_path: str | Path | None = None,
    video_id: str | None = None,
) -> dict:
    """
    Analyze video frames independently.

    Successful results are preserved even if some frames fail.
    All failures are recorded in the output JSON.
    """

    manifest_path = Path(manifest_path)

    if not manifest_path.exists() or not manifest_path.is_file():
        raise FileNotFoundError(
            f"Frame manifest not found: {manifest_path}"
        )

    with manifest_path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    if not isinstance(manifest, dict):
        raise ValueError("Invalid frame manifest format.")

    frames = manifest.get("frames", [])

    if not isinstance(frames, list) or not frames:
        raise ValueError("No frames found in the manifest.")

    results = []
    failed_frames = []

    total_frames = len(frames)

    for index, frame in enumerate(frames, start=1):

        frame_path = None
        timestamp = None

        try:
            if not isinstance(frame, dict):
                raise ValueError("Invalid frame entry in manifest.")

            if "path" not in frame:
                raise ValueError("Frame path is missing.")

            if "timestamp_seconds" not in frame:
                raise ValueError("Frame timestamp is missing.")

            timestamp = float(frame["timestamp_seconds"])

            frame_path = Path(frame["path"])

            if not frame_path.is_absolute():
                cwd_path = Path.cwd() / frame_path
                manifest_relative_path = manifest_path.parent / frame_path

                if cwd_path.exists():
                    frame_path = cwd_path
                else:
                    frame_path = manifest_relative_path

            print(
                f"Analyzing frame {index}/{total_frames} "
                f"at {timestamp} seconds..."
            )

            result = analyze_frame(
                image_path=frame_path,
                timestamp_seconds=timestamp,
                video_id=video_id,
            )

            results.append(result)

            print(f"Frame {index} analyzed successfully.")

        except Exception as error:

            failure = {
                "frame_index": index,
                "frame_path": (
                    str(frame_path)
                    if frame_path is not None
                    else frame.get("path")
                    if isinstance(frame, dict)
                    else None
                ),
                "timestamp_seconds": timestamp,
                "error_type": type(error).__name__,
                "error": str(error),
            }

            failed_frames.append(failure)

            print(
                f"Frame {index} failed: "
                f"{type(error).__name__}: {error}"
            )

    # Determine overall processing status.
    if len(results) == total_frames:
        status = "completed"
    elif len(results) > 0:
        status = "partial"
    else:
        status = "failed"

    # Preserve the existing result structure and add failure details.
    analysis = {
        "status": status,
        "video_file": manifest.get("video_file"),
        "video_id": video_id,
        "model": MODEL_NAME,
        "total_frames": total_frames,
        "total_frames_analyzed": len(results),
        "total_frames_failed": len(failed_frames),
        "visual_descriptions": results,
        "failed_frames": failed_frames,
    }

    if output_path is None:
        output_dir = Path("data/visual_descriptions")
        output_dir.mkdir(parents=True, exist_ok=True)

        video_name = Path(
            manifest.get("video_file", "video")
        ).stem

        output_path = (
            output_dir / f"{video_name}_visual_analysis.json"
        )

    else:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with Path(output_path).open("w", encoding="utf-8") as file:
        json.dump(
            analysis,
            file,
            indent=4,
            ensure_ascii=False,
        )

    print(f"\nVisual analysis saved to: {output_path}")
    print(f"Processing status: {status}")
    print(f"Successful frames: {len(results)}")
    print(f"Failed frames: {len(failed_frames)}")

    return analysis