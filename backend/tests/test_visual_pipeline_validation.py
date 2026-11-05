import json

import pytest

from app.services.multimodal.visual_pipeline import analyze_video_frames


def test_missing_manifest():
    """Reject a manifest that does not exist."""

    with pytest.raises(FileNotFoundError):
        analyze_video_frames(
            manifest_path="nonexistent_manifest.json"
        )


def test_empty_manifest(tmp_path):
    """Reject a manifest containing no frames."""

    manifest = {
        "video_file": "test_video.mp4",
        "frames": [],
    }

    manifest_path = tmp_path / "empty_manifest.json"

    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="No frames found"):
        analyze_video_frames(
            manifest_path=manifest_path
        )


def test_invalid_json_manifest(tmp_path):
    """Reject malformed JSON."""

    manifest_path = tmp_path / "invalid_manifest.json"

    manifest_path.write_text(
        "{invalid json",
        encoding="utf-8",
    )

    with pytest.raises(json.JSONDecodeError):
        analyze_video_frames(
            manifest_path=manifest_path
        )