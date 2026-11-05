import json
import subprocess
from pathlib import Path


def extract_video_frames(
    video_path: str,
    output_dir: str,
    interval_seconds: int = 5,
) -> dict:
    """
    Extract one video frame at the specified time interval.
    Save frame metadata in a JSON manifest.
    """

    video = Path(video_path)
    output = Path(output_dir)

    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")

    if interval_seconds <= 0:
        raise ValueError("Interval must be greater than zero.")

    output.mkdir(parents=True, exist_ok=True)

    frame_pattern = output / "frame_%06d.jpg"

    command = [
        "ffmpeg",
        "-y",
        "-i", str(video),
        "-vf", f"fps=1/{interval_seconds}",
        "-q:v", "2",
        str(frame_pattern),
    ]

    try:
        subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Frame extraction failed: {error.stderr}"
        ) from error

    frames = sorted(output.glob("frame_*.jpg"))

    manifest = {
        "video_file": video.name,
        "interval_seconds": interval_seconds,
        "total_frames": len(frames),
        "frames": [
            {
                "filename": frame.name,
                "timestamp_seconds": index * interval_seconds,
                "path": str(frame),
            }
            for index, frame in enumerate(frames)
        ],
    }

    manifest_path = output / "frames_manifest.json"

    with manifest_path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4)

    return {
        "video_file": video.name,
        "total_frames": len(frames),
        "output_directory": str(output),
        "manifest": str(manifest_path),
    }