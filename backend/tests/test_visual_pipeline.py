import os

import pytest

from app.services.multimodal.visual_pipeline import analyze_video_frames


@pytest.mark.skipif(
    not os.getenv("RUN_GEMINI_TESTS"),
    reason="Set RUN_GEMINI_TESTS=1 to run Gemini integration tests",
)
def test_analyze_video_frames():
    result = analyze_video_frames(
        manifest_path="data/frames/speech_test/frames_manifest.json",
        video_id="speech_test_001",
    )

    assert result["status"] == "completed"
    assert result["total_frames"] > 0
    assert result["total_frames_analyzed"] > 0
    assert result["total_frames_failed"] == 0

    print("\nBatch Visual Analysis Summary")
    print("-----------------------------")
    print("Video ID:", result["video_id"])
    print("Total frames analyzed:", result["total_frames_analyzed"])

    for item in result["visual_descriptions"]:
        print("\nTimestamp:", item["timestamp"])
        print("Description:", item["description"])