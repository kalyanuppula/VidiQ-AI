import json

from app.services.multimodal import visual_pipeline


def test_visual_pipeline_handles_missing_frame(tmp_path, monkeypatch):

    def fake_analyze_frame(
        image_path,
        timestamp_seconds,
        video_id=None,
    ):
        if timestamp_seconds == 5.0:
            raise FileNotFoundError("Simulated missing frame")

        return {
            "video_id": video_id,
            "timestamp_seconds": timestamp_seconds,
            "timestamp": "00:00:00",
            "frame_path": str(image_path),
            "description": "Mock visual description",
            "model": "test-model",
        }

    monkeypatch.setattr(
        visual_pipeline,
        "analyze_frame",
        fake_analyze_frame,
    )

    manifest = {
        "video_file": "visual_test.mp4",
        "frames": [
            {
                "path": "frame_000001.jpg",
                "timestamp_seconds": 0.0,
            },
            {
                "path": "nonexistent_frame.jpg",
                "timestamp_seconds": 5.0,
            },
        ],
    }

    manifest_path = tmp_path / "failure_manifest.json"

    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    result = visual_pipeline.analyze_video_frames(
        manifest_path=manifest_path,
        output_path=tmp_path / "failure_result.json",
        video_id="visual_failure_test_001",
    )

    assert result["status"] == "partial"
    assert result["total_frames_analyzed"] == 1
    assert result["total_frames_failed"] == 1

    saved_result = json.loads(
        (tmp_path / "failure_result.json").read_text(
            encoding="utf-8"
        )
    )

    assert saved_result["status"] == "partial"

    print("\nFailure handling test passed!")

def test_visual_pipeline_when_all_frames_fail(tmp_path, monkeypatch):
    """Verify pipeline behavior when every frame fails."""

    def fake_analyze_frame(*args, **kwargs):
        raise RuntimeError("Simulated Gemini API failure")

    monkeypatch.setattr(
        visual_pipeline,
        "analyze_frame",
        fake_analyze_frame,
    )

    manifest = {
        "video_file": "test_video.mp4",
        "frames": [
            {
                "path": "frame_000001.jpg",
                "timestamp_seconds": 0.0,
            },
            {
                "path": "frame_000002.jpg",
                "timestamp_seconds": 5.0,
            },
        ],
    }

    manifest_path = tmp_path / "all_failed_manifest.json"

    manifest_path.write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    output_path = tmp_path / "all_failed_result.json"

    result = visual_pipeline.analyze_video_frames(
        manifest_path=manifest_path,
        output_path=output_path,
        video_id="all_failed_test",
    )

    assert result["status"] == "failed"
    assert result["total_frames"] == 2
    assert result["total_frames_analyzed"] == 0
    assert result["total_frames_failed"] == 2
    assert len(result["failed_frames"]) == 2
    assert output_path.exists()

    saved_result = json.loads(
        output_path.read_text(encoding="utf-8")
    )

    assert saved_result["status"] == "failed"

    print("\nAll-frames-failed test passed!")