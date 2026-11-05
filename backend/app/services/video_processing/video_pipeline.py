from pathlib import Path

from app.services.video_processing.video_metadata import extract_video_metadata
from app.services.video_processing.audio_extractor import extract_audio
from app.services.video_processing.transcription import transcribe_audio
from app.services.video_processing.transcript_saver import save_transcript
from app.services.video_processing.frame_extractor import extract_video_frames


def process_video(
    video_path: str,
    data_dir: str = "data",
    model_size: str = "base",
    interval_seconds: int = 5,
) -> dict:
    """
    Run the complete video and audio processing pipeline.
    Supports videos with or without audio.
    """

    video = Path(video_path)

    if not video.exists():
        raise FileNotFoundError(f"Video not found: {video}")

    if not video.is_file():
        raise ValueError(f"Input path is not a file: {video}")

    if (
    isinstance(interval_seconds, bool)
    or not isinstance(interval_seconds, int)
    or interval_seconds <= 0):
        raise ValueError(
        "Interval must be a positive integer."
        )

    root = Path(data_dir)
    video_name = video.stem

    # 1. Extract video metadata
    metadata = extract_video_metadata(str(video))

    # 2. Process audio only when available
    audio_result = None
    transcription_result = None

    if metadata["audio_available"]:

        # Extract audio
        audio_path = root / "audio" / f"{video_name}.wav"

        audio_result = extract_audio(
            str(video),
            str(audio_path),
        )

        # Transcribe audio
        transcription = transcribe_audio(
            str(audio_path),
            model_size=model_size,
        )

        # Save timestamped transcript
        transcript_path = (
            root / "transcripts" / f"{video_name}_transcript.json"
        )

        transcript_result = save_transcript(
            transcription,
            str(transcript_path),
        )

        transcription_result = {
            "language": transcription["language"],
            "full_text": transcription["full_text"],
            "segments": len(transcription["segments"]),
            **transcript_result,
        }

    # 3. Extract video frames
    frames_dir = root / "frames" / video_name

    frames_result = extract_video_frames(
        str(video),
        str(frames_dir),
        interval_seconds=interval_seconds,
    )

    return {
        "status": "completed",
        "video": metadata,
        "audio": audio_result,
        "transcription": transcription_result,
        "frames": frames_result,
    }