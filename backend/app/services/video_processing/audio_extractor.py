import subprocess
from pathlib import Path


def extract_audio(video_path: str, output_path: str) -> dict:
    """
    Extract mono, 16 kHz WAV audio from a video.
    """

    video = Path(video_path)
    output = Path(output_path)

    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")

    output.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-y",
        "-i", str(video),
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-c:a", "pcm_s16le",
        str(output),
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
            f"Audio extraction failed: {error.stderr}"
        ) from error

    return {
        "input_video": video.name,
        "output_audio": str(output),
        "audio_format": "wav",
        "sample_rate": 16000,
        "channels": 1,
        "file_size_mb": round(
            output.stat().st_size / (1024 * 1024), 2
        ),
    }