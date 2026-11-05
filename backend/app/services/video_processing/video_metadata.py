import json
import subprocess
from pathlib import Path


def extract_video_metadata(video_path: str) -> dict:
    """
    Extract video and audio metadata using FFprobe.
    """

    path = Path(video_path)

    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    command = [
        "ffprobe",
        "-v", "error",
        "-show_entries",
        "format=filename,duration,size,format_name:"
        "stream=codec_type,codec_name,width,height,r_frame_rate",
        "-of", "json",
        str(path),
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=True,
        )

        metadata = json.loads(result.stdout)

    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"FFprobe failed: {error.stderr}"
        ) from error

    streams = metadata.get("streams", [])
    video_stream = next(
        (stream for stream in streams
         if stream.get("codec_type") == "video"),
        None,
    )
    audio_stream = next(
        (stream for stream in streams
         if stream.get("codec_type") == "audio"),
        None,
    )

    if video_stream is None:
        raise ValueError("The supplied file has no video stream.")

    fps = video_stream.get("r_frame_rate", "0/1")

    try:
        numerator, denominator = map(int, fps.split("/"))
        frame_rate = (
            round(numerator / denominator, 2)
            if denominator else 0
        )
    except (ValueError, ZeroDivisionError):
        frame_rate = 0

    format_info = metadata.get("format", {})

    return {
        "filename": path.name,
        "duration_seconds": round(
            float(format_info.get("duration", 0)), 2
        ),
        "file_size_mb": round(
            int(format_info.get("size", 0)) / (1024 * 1024), 2
        ),
        "format": format_info.get("format_name"),
        "width": video_stream.get("width"),
        "height": video_stream.get("height"),
        "resolution": (
            f"{video_stream.get('width')}x"
            f"{video_stream.get('height')}"
        ),
        "fps": frame_rate,
        "video_codec": video_stream.get("codec_name"),
        "audio_available": audio_stream is not None,
        "audio_codec": (
            audio_stream.get("codec_name")
            if audio_stream else None
        ),
    }