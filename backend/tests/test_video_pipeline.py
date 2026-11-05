import pytest
from pathlib import Path

from app.services.video_processing import video_pipeline


def test_process_video_with_audio(tmp_path, monkeypatch):
    video_file = tmp_path / "test_video.mp4"
    video_file.touch()

    calls = []

    def mock_metadata(video_path):
        calls.append("metadata")
        return {
            "audio_available": True,
            "duration": 10.0,
        }

    def mock_extract_audio(video_path, audio_path):
        calls.append("audio")
        return {"audio_path": audio_path}

    def mock_transcribe_audio(audio_path, model_size):
        calls.append("transcription")
        return {
            "language": "en",
            "full_text": "Test video transcript",
            "segments": [
                {"start": 0, "end": 2, "text": "Hello"}
            ],
        }

    def mock_save_transcript(transcription, transcript_path):
        calls.append("save_transcript")
        return {"transcript_path": transcript_path}

    def mock_extract_frames(
        video_path,
        frames_dir,
        interval_seconds,
    ):
        calls.append("frames")
        return {"frame_count": 2}

    monkeypatch.setattr(
        video_pipeline,
        "extract_video_metadata",
        mock_metadata,
    )
    monkeypatch.setattr(
        video_pipeline,
        "extract_audio",
        mock_extract_audio,
    )
    monkeypatch.setattr(
        video_pipeline,
        "transcribe_audio",
        mock_transcribe_audio,
    )
    monkeypatch.setattr(
        video_pipeline,
        "save_transcript",
        mock_save_transcript,
    )
    monkeypatch.setattr(
        video_pipeline,
        "extract_video_frames",
        mock_extract_frames,
    )

    result = video_pipeline.process_video(
        str(video_file),
        data_dir=str(tmp_path / "data"),
    )

    assert result["status"] == "completed"
    assert result["audio"] is not None
    assert result["transcription"]["language"] == "en"
    assert result["frames"]["frame_count"] == 2

    assert calls == [
        "metadata",
        "audio",
        "transcription",
        "save_transcript",
        "frames",
    ]


def test_process_video_without_audio(tmp_path, monkeypatch):
    video_file = tmp_path / "silent_video.mp4"
    video_file.touch()

    calls = []

    def mock_metadata(video_path):
        calls.append("metadata")
        return {
            "audio_available": False,
            "duration": 10.0,
        }

    def mock_extract_audio(*args, **kwargs):
        pytest.fail("Audio extraction should not run.")

    def mock_transcribe_audio(*args, **kwargs):
        pytest.fail("Transcription should not run.")

    def mock_extract_frames(
        video_path,
        frames_dir,
        interval_seconds,
    ):
        calls.append("frames")
        return {"frame_count": 2}

    monkeypatch.setattr(
        video_pipeline,
        "extract_video_metadata",
        mock_metadata,
    )
    monkeypatch.setattr(
        video_pipeline,
        "extract_audio",
        mock_extract_audio,
    )
    monkeypatch.setattr(
        video_pipeline,
        "transcribe_audio",
        mock_transcribe_audio,
    )
    monkeypatch.setattr(
        video_pipeline,
        "extract_video_frames",
        mock_extract_frames,
    )

    result = video_pipeline.process_video(
        str(video_file),
        data_dir=str(tmp_path / "data"),
    )

    assert result["status"] == "completed"
    assert result["audio"] is None
    assert result["transcription"] is None
    assert result["frames"]["frame_count"] == 2

    assert calls == ["metadata", "frames"]


@pytest.mark.parametrize(
    "interval",
    [0, -1, True, False, 2.5],
)
def test_process_video_rejects_invalid_interval(
    tmp_path,
    interval,
):
    video_file = tmp_path / "dummy.mp4"
    video_file.touch()

    with pytest.raises(
        ValueError,
        match="Interval must be a positive integer",
    ):
        video_pipeline.process_video(
            video_path=str(video_file),
            interval_seconds=interval,
        )


def test_process_video_rejects_missing_file():
    with pytest.raises(FileNotFoundError):
        video_pipeline.process_video(
            video_path="missing_video.mp4",
        )


def test_process_video_rejects_directory(tmp_path):
    with pytest.raises(ValueError, match="not a file"):
        video_pipeline.process_video(
            video_path=str(tmp_path),
        )